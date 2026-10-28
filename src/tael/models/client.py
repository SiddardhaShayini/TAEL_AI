import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import httpx

from tael.config.settings import ModelConfig


@dataclass
class ToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[ToolCall]] = None


@dataclass
class LLMResponse:
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"


class LLMClient(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        pass


class OllamaClient(LLMClient):
    def __init__(self, config: ModelConfig):
        self.config = config

    def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        payload_messages = []
        for m in messages:
            msg_dict: Dict[str, Any] = {"role": m.role, "content": m.content}
            if m.tool_calls:
                msg_dict["tool_calls"] = [
                    {"function": {"name": tc.name, "arguments": tc.arguments}}
                    for tc in m.tool_calls
                ]
            payload_messages.append(msg_dict)

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": payload_messages,
            "stream": False,
            "options": {
                "temperature": temperature if temperature is not None else self.config.temperature,
                "num_ctx": self.config.context_window,
                "num_predict": self.config.max_output_tokens,
            },
        }

        if tools:
            # Format tools for Ollama tool calling
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t["description"],
                        "parameters": t["parameters"],
                    },
                }
                for t in tools
            ]

        try:
            with httpx.Client(timeout=self.config.timeout_seconds) as client:
                res = client.post(f"{self.config.endpoint}/api/chat", json=payload)
                if res.status_code == 400 and "does not support tools" in res.text:
                    # Model does not declare native tool calling in its Modelfile (e.g. granite-code:3b)
                    # Retry without the 'tools' parameter as a resilient fallback
                    payload_no_tools = dict(payload)
                    payload_no_tools.pop("tools", None)
                    res = client.post(f"{self.config.endpoint}/api/chat", json=payload_no_tools)

                if res.status_code != 200:
                    raise RuntimeError(f"Ollama returned HTTP {res.status_code}: {res.text}")

                data = res.json()
                msg = data.get("message", {})
                content = msg.get("content", "")

                tool_calls: List[ToolCall] = []
                for tc in msg.get("tool_calls", []):
                    fn = tc.get("function", {})
                    fn_name = fn.get("name")
                    fn_args = fn.get("arguments", {})
                    if isinstance(fn_args, str):
                        try:
                            fn_args = json.loads(fn_args)
                        except Exception:
                            fn_args = {}
                    if fn_name:
                        tool_calls.append(ToolCall(name=fn_name, arguments=fn_args))

                # Text-based tool extraction fallback for models without native tool calling
                if not tool_calls and content:
                    import re
                    patterns = [
                        r"```(?:json)?\s*(\{\s*\"tool\"\s*:\s*\"[^\"]+\".*?\})\s*```",
                        r"<tool_call>\s*(\{\s*\"tool\"\s*:\s*\"[^\"]+\".*?\})\s*</tool_call>",
                        r"(\{\s*\"tool\"\s*:\s*\"[^\"]+\"\s*,\s*\"args\"\s*:\s*\{.*?\}\s*\})",
                        r"(\{\s*\"name\"\s*:\s*\"[^\"]+\"\s*,\s*\"arguments\"\s*:\s*\{.*?\}\s*\})",
                    ]
                    for pat in patterns:
                        call_match = re.search(pat, content, re.DOTALL)
                        if call_match:
                            raw_json = call_match.group(1)
                            parsed = None
                            try:
                                parsed = json.loads(raw_json, strict=False)
                            except Exception:
                                try:
                                    # Fallback: remove control characters that break JSON strings
                                    clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda m: '\\n' if m.group(0) == '\n' else '\\t' if m.group(0) == '\t' else '', raw_json)
                                    parsed = json.loads(clean, strict=False)
                                except Exception:
                                    pass

                            if parsed:
                                tname = parsed.get("tool") or parsed.get("name")
                                targs = parsed.get("args") or parsed.get("arguments") or {}
                                if tname:
                                    tool_calls.append(ToolCall(name=tname, arguments=targs))
                                    break

                return LLMResponse(
                    content=content,
                    tool_calls=tool_calls,
                    finish_reason=data.get("done_reason", "stop"),
                )
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with local model runtime: {str(e)}")


class MockLLMClient(LLMClient):
    """Deterministic mock client for testing and verification without running Ollama."""

    def __init__(self, custom_responses: Optional[List[LLMResponse]] = None):
        self.responses: List[LLMResponse] = custom_responses or []
        self.call_history: List[List[LLMMessage]] = []

    def queue_response(self, response: LLMResponse) -> None:
        self.responses.append(response)

    def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        self.call_history.append(messages)
        if self.responses:
            return self.responses.pop(0)
        return LLMResponse(
            content="Mock response: Plan created and executed successfully.",
            tool_calls=[],
        )


def create_llm_client(config: ModelConfig) -> LLMClient:
    if config.backend == "mock":
        return MockLLMClient()
    return OllamaClient(config)
