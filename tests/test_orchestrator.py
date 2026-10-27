from pathlib import Path
from tael.config.settings import TaelConfig
from tael.core.orchestrator import TaskOrchestrator
from tael.core.session import SessionState
from tael.models.client import MockLLMClient, LLMResponse, ToolCall
from tael.tools import create_default_registry


def test_orchestrator_multi_turn_tool_calling(tmp_path: Path):
    ws = str(tmp_path)
    cfg = TaelConfig.load()
    cfg.workspace_root = ws
    cfg.policy.require_approval_write = False

    # Create mock LLM that calls write_file tool, then finishes
    mock_llm = MockLLMClient()
    mock_llm.queue_response(
        LLMResponse(
            content="I will create the math.py file.",
            tool_calls=[
                ToolCall(
                    name="write_file",
                    arguments={"path": "math_lib.py", "content": "def add(a, b): return a + b\n"},
                )
            ],
        )
    )
    mock_llm.queue_response(
        LLMResponse(
            content="Created math_lib.py successfully. The task is complete.",
            tool_calls=[],
        )
    )

    registry = create_default_registry()
    orchestrator = TaskOrchestrator(
        config=cfg,
        llm_client=mock_llm,
        tool_registry=registry,
    )

    result = orchestrator.execute_task("Create a math helper library")
    assert result["status"] == "completed"
    assert result["turns"] == 2
    assert len(result["tools_executed"]) == 1
    assert result["tools_executed"][0]["tool"] == "write_file"
    assert (tmp_path / "math_lib.py").exists()
    assert "def add(a, b)" in (tmp_path / "math_lib.py").read_text()


def test_orchestrator_cancellation(tmp_path: Path):
    ws = str(tmp_path)
    cfg = TaelConfig.load()
    cfg.workspace_root = ws

    mock_llm = MockLLMClient()
    session = SessionState(workspace_root=ws)
    session.cancel()  # Pre-cancelled

    orchestrator = TaskOrchestrator(config=cfg, llm_client=mock_llm)
    result = orchestrator.execute_task("Do something", session=session)
    assert result["status"] == "cancelled"
