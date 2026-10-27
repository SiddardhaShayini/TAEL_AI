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

{memory_context}
"""


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
        self.tools = tool_registry or create_default_registry()
        self.llm = llm_client or create_llm_client(config.model)
        
        self.memory_store = memory_store or MemoryStore(
            workspace_path=self.workspace_root,
            store_dir=config.memory.store_dir,
        )
        self.memory_retriever = MemoryRetriever(
            self.memory_store,
            default_token_budget=config.memory.token_budget,
        )

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

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(memory_context=memory_snippet)
        if not session.messages:
            session.add_message(LLMMessage(role="system", content=system_prompt))
        
        session.add_message(LLMMessage(role="user", content=user_request))

        tool_schemas = self.tools.get_schemas()
        turns = 0
        final_answer = ""
        tools_executed = []

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

            # Record thought/response if content present
            if response.content:
                progress.on_thought(response.content)
                final_answer = response.content

            # Check if LLM requested tool calls
            if not response.tool_calls:
                # LLM finished its task turn without requesting further tools
                session.add_message(LLMMessage(role="assistant", content=response.content))
                break

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
