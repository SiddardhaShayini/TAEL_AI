import json
import time
from typing import Any, Callable, Dict, List, Optional

from tael.config.settings import TaelConfig
from tael.core.planner import TaskPlan, PlanStep, StepStatus
from tael.core.session import SessionState
from tael.memory.models import MemoryCategory, MemoryEntry
from tael.memory.retrieval import MemoryRetriever
from tael.memory.store import MemoryStore
from tael.models.client import LLMClient, LLMMessage, ToolCall, create_llm_client
from tael.resources.monitor import ResourceMonitor
from tael.tools import ToolRegistry, create_default_registry


SYSTEM_PROMPT_TEMPLATE = """You are TAEL V3, a task-adaptive, efficient local AI coding assistant.
You specialize in natural-language software creation, debugging, testing, and hardware-aware engineering on everyday laptops.

Core operating rules:
1. Always ground your facts in current workspace files and actual tool execution. Never claim tests passed unless you ran them.
2. Use available tools when you need to inspect, modify, build, or verify the codebase.
3. Be concise, precise, and practical.
4. When you have finished the user's task or answered their question, provide a concise summary of what was accomplished and how it was verified.

{tools_context}

{memory_context}
"""


def format_tools_prompt(schemas: List[Dict[str, Any]]) -> str:
    """Format tool signatures into the system prompt for local models without native tool calling metadata."""
    lines = ["Available workspace tools:"]
    for s in schemas:
        props = s.get("parameters", {}).get("properties", {})
        params = [f"{k}: {v.get('type', 'any')}" for k, v in props.items()]
        sig = f"{s['name']}({', '.join(params)})"
        lines.append(f"- {sig}: {s.get('description', '')}")

    lines.append("\nCRITICAL ACTION RULES:")
    lines.append("1. ACTION OVER CHAT: When asked to create, write, edit, delete, inspect, or run files or commands, you MUST NOT just show code in chat or ask conversational questions. You MUST invoke a tool using the JSON format below to perform the action directly on disk.")
    lines.append("2. NEVER give manual instructions or tutorials to the user on how they can create or edit files manually. You are an autonomous software assistant with full tool execution permissions. Directly invoke write_file with the full content.")
    lines.append("3. Whenever asked to create or write a file (e.g. 'create a .md file and write about X', 'create quick_guide.md and write about Y', 'make script.py'), you MUST invoke write_file immediately with the file path and complete content.")
    lines.append("4. To invoke a tool, output a JSON block matching this exact structure:")
    lines.append('```json\n{"tool": "<tool_name>", "args": {<arguments>}}\n```')
    lines.append("\n[Example Tool Invocations]:")
    lines.append("Task: create a .md file and write about Agentic AI")
    lines.append('```json\n{"tool": "write_file", "args": {"path": "agentic_ai.md", "content": "# Agentic AI Overview\\nAgentic AI systems can autonomously plan and execute tasks..."}}\n```')
    lines.append("Task: create quick_guide.md and write about TAEL AI")
    lines.append('```json\n{"tool": "write_file", "args": {"path": "quick_guide.md", "content": "# TAEL AI Quick Guide\\nTAEL AI is a local-first agentic coding assistant designed for everyday laptops..."}}\n```')
    lines.append("Task: List files in current directory")
    lines.append('```json\n{"tool": "list_dir", "args": {"path": "."}}\n```')
    return "\n".join(lines)


class OrchestratorProgress:
    """Callback hook for streaming events (CLI / UI / API)."""
    def on_thought(self, content: str) -> None: pass
    def on_tool_start(self, tool_name: str, args: Dict[str, Any]) -> None: pass
    def on_tool_end(self, tool_name: str, result_summary: str, success: bool) -> None: pass
    def on_pressure_warning(self, message: str) -> None: pass


class TaskOrchestrator:
    def __init__(
        self,
        config: TaelConfig,
        llm_client: Optional[LLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        memory_store: Optional[MemoryStore] = None,
        resource_monitor: Optional[ResourceMonitor] = None,
    ):
        self.config = config
        self.workspace_root = config.workspace_root
        self.resource_monitor = resource_monitor or ResourceMonitor(config.resource.profile)
        self.tools = tool_registry or create_default_registry(mcp_servers=config.mcp_servers)
        self.llm = llm_client or create_llm_client(config.model)
        
        self.memory_store = memory_store or MemoryStore(
            workspace_path=self.workspace_root,
            store_dir=config.memory.store_dir,
        )
        self.memory_retriever = MemoryRetriever(
            self.memory_store,
            default_token_budget=config.memory.token_budget,
        )

    def _extract_implicit_file_action(self, user_request: str, content: str) -> Optional[ToolCall]:
        """
        Safety net for smaller local models (3B) that generate file content inside
        markdown code blocks or textual descriptions instead of emitting a formal tool call JSON block.
        """
        import re
        user_lower = user_request.lower()
        create_keywords = ["create", "write", "make", "save", "generate", "add"]
        if not any(k in user_lower for k in create_keywords):
            return None

        # Check for explicit or implicit file extension
        ext = ".md" if (".md" in user_lower or "markdown" in user_lower) else ".py" if (".py" in user_lower or "python" in user_lower) else None

        # Look for explicit filename in user request
        fname_m = re.search(r'([a-zA-Z0-9_\-\.]+\.(?:md|py|txt|json|yaml|yml|html|css|js|sh|bat))', user_request, re.IGNORECASE)
        filename = fname_m.group(1) if fname_m else None

        if not filename and ext:
            # Derive filename from topic: "write about Agentic AI" -> "agentic_ai.md"
            topic_m = re.search(r'(?:about|on|for)\s+([a-zA-Z0-9_\s\-]+)', user_request, re.IGNORECASE)
            if topic_m:
                slug = topic_m.group(1).strip().replace(" ", "_").lower()
                slug = re.sub(r'[^a-z0-9_]', '', slug)[:30]
                filename = f"{slug}{ext}"
            else:
                filename = f"output{ext}"

        if not filename:
            return None

        file_content = None

        # 1. Prefer fenced code block
        code_m = re.search(r'```(?:[a-zA-Z0-9_\-]+)?\s*\n([\s\S]+?)\n```', content)
        if code_m:
            file_content = code_m.group(1).strip()
        # 2. Markdown text starting with header
        elif content.strip().startswith("#"):
            file_content = content.strip()
        # 3. Markdown header anywhere inside response
        elif re.search(r'\n(#+\s+.+)', content):
            header_m = re.search(r'(#+\s+.+)', content)
            file_content = content[header_m.start():].strip()
        # 4. If python file, find python import/def/class
        elif filename.endswith('.py') and re.search(r'(?:from\s+\w+|import\s+\w+|def\s+\w+|class\s+\w+)', content):
            py_m = re.search(r'(?:from\s+\w+|import\s+\w+|def\s+\w+|class\s+\w+)', content)
            file_content = content[py_m.start():].strip()
        # 5. General fallback: format content cleanly into the requested file
        elif len(content.strip()) > 20:
            cleaned = re.sub(r'^(?:Sure,?\s*I can help.*?:|Here(?: is|\'s).*?:)\s*', '', content.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r'\n+(?:That\'s it!|I hope this helps|Let me know if).*$', '', cleaned, flags=re.IGNORECASE).strip()
            title = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
            file_content = f"# {title}\n\n{cleaned if cleaned else content.strip()}"

        if not file_content:
            return None

        return ToolCall(name="write_file", arguments={"path": filename, "content": file_content})

    def execute_task(
        self,
        user_request: str,
        session: Optional[SessionState] = None,
        progress: Optional[OrchestratorProgress] = None,
        max_turns: int = 10,
    ) -> Dict[str, Any]:
        """Execute a complete natural-language task using agent loop with memory, tools, and resource monitoring."""
        session = session or SessionState(workspace_root=self.workspace_root)
        progress = progress or OrchestratorProgress()
        start_time = time.time()

        # Step 1: Memory retrieval (bounded token budget)
        memory_result = self.memory_retriever.retrieve_for_task(user_request)
        memory_snippet = self.memory_retriever.format_context_prompt(memory_result)

        tool_schemas = self.tools.get_schemas()
        tools_prompt = format_tools_prompt(tool_schemas)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            tools_context=tools_prompt,
            memory_context=memory_snippet,
        )
        if not session.messages:
            session.add_message(LLMMessage(role="system", content=system_prompt))
        
        session.add_message(LLMMessage(role="user", content=user_request))
        turns = 0
        final_answer = ""
        tools_executed = []
        tools_call_history = set()

        while turns < max_turns:
            turns += 1

            # Check for cancellation
            if session.is_cancelled:
                final_answer = "Task was cancelled by the user."
                break

            # Check hardware resource pressure
            under_pressure, reason = self.resource_monitor.check_pressure()
            if under_pressure and reason:
                progress.on_pressure_warning(f"Resource supervisor warning: {reason}")
                time.sleep(0.5)  # Backpressure pause

            # Call local LLM
            response = self.llm.chat(
                messages=session.messages,
                tools=tool_schemas,
            )

            # Strip prompt echoes if model starts continuing few-shot dialogues
            if "\nUser:" in response.content:
                response.content = response.content.split("\nUser:")[0].strip()

            # Record thought/response if content present
            if response.content:
                progress.on_thought(response.content)
                final_answer = response.content

            # Check if LLM requested tool calls
            if not response.tool_calls and turns == 1:
                # Safety net: extract implicit file creation if model emitted markdown/code block instead of tool JSON
                fallback_call = self._extract_implicit_file_action(user_request, response.content)
                if fallback_call:
                    response.tool_calls.append(fallback_call)

            if not response.tool_calls:
                # LLM finished its task turn without requesting further tools
                session.add_message(LLMMessage(role="assistant", content=response.content))
                break

            # Tool call deduplication to prevent model looping on identical invocations
            current_sigs = tuple(f"{tc.name}:{json.dumps(tc.arguments, sort_keys=True)}" for tc in response.tool_calls)
            if current_sigs and current_sigs in tools_call_history:
                break
            tools_call_history.add(current_sigs)

            # Assistant message with tool calls
            session.add_message(
                LLMMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )

            # Execute tool calls
            for tc in response.tool_calls:
                if session.is_cancelled:
                    break

                progress.on_tool_start(tc.name, tc.arguments)
                tool_res = self.tools.execute(
                    tool_name=tc.name,
                    arguments=tc.arguments,
                    context={"workspace_root": self.workspace_root},
                )

                summary = (
                    f"Success: {tool_res.data}"
                    if tool_res.success
                    else f"Error: {tool_res.error}"
                )
                if len(str(summary)) > 300:
                    summary = str(summary)[:300] + "..."

                progress.on_tool_end(tc.name, summary, tool_res.success)
                tools_executed.append({
                    "tool": tc.name,
                    "arguments": tc.arguments,
                    "success": tool_res.success,
                    "result": tool_res.to_dict(),
                })

                # Append tool result back to LLM messages
                content_str = json.dumps(tool_res.to_dict(), default=str)
                # Bounded length for prompt context safety
                if len(content_str) > 6000:
                    content_str = content_str[:6000] + '... [output truncated for context limit]"}'

                session.add_message(
                    LLMMessage(
                        role="tool",
                        content=content_str,
                    )
                )

        duration = time.time() - start_time

        # Ensure a clean user-facing final answer when tools were executed
        if tools_executed:
            actions = [f"• {t['tool']} ({t['arguments'].get('path') or t['arguments'].get('command') or ''})" for t in tools_executed if t.get('success')]
            if not final_answer or '```json\n{"tool":' in final_answer or "Open a text editor" in final_answer or "step-by-step guide" in final_answer:
                final_answer = "Task actions executed successfully:\n" + "\n".join(actions)
            elif not any(t.get('arguments', {}).get('path', '') in final_answer for t in tools_executed if t.get('arguments', {}).get('path')):
                final_answer = f"{final_answer}\n\nTask actions executed:\n" + "\n".join(actions)

        return {
            "session_id": session.session_id,
            "status": "completed" if not session.is_cancelled else "cancelled",
            "turns": turns,
            "duration_seconds": round(duration, 2),
            "final_answer": final_answer,
            "tools_executed": tools_executed,
            "memory_supplied_count": len(memory_result.entries),
            "memory_tokens_used": memory_result.total_tokens,
        }
