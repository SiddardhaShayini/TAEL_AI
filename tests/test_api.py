import pytest
import httpx
from pathlib import Path

from tael.api.server import create_app
from tael.config.settings import TaelConfig


@pytest.mark.asyncio
async def test_api_endpoints(tmp_path: Path):
    cfg = TaelConfig.load()
    cfg.workspace_root = str(tmp_path)
    cfg.memory.store_dir = str(tmp_path / "memory")
    cfg.model.backend = "mock"

    app = create_app(cfg)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "ok"

        # 1b. Root Dashboard & Logo
        res_index = await client.get("/")
        assert res_index.status_code == 200
        assert "TAEL AI" in res_index.text
        assert "/logo.svg" in res_index.text

        res_logo = await client.get("/logo.svg")
        assert res_logo.status_code == 200
        assert "image/svg+xml" in res_logo.headers.get("content-type", "")
        assert "<svg" in res_logo.text

        # 2. Status
        res_status = await client.get("/status")
        assert res_status.status_code == 200
        data_status = res_status.json()
        assert "resource" in data_status
        assert "model" in data_status
        assert data_status["resource"]["profile"] in ("conservative", "balanced")

        # 3. Create session
        res_session = await client.post("/session", json={"workspace_root": str(tmp_path)})
        assert res_session.status_code == 200
        session_id = res_session.json()["session_id"]
        assert session_id is not None

        # 4. Cancel session
        res_cancel = await client.post(f"/session/{session_id}/cancel")
        assert res_cancel.status_code == 200
        assert res_cancel.json()["cancelled"] is True

        # 5. Memory list
        res_mem = await client.get("/memory")
        assert res_mem.status_code == 200
        assert isinstance(res_mem.json(), list)

        # 6. Memory search
        res_search = await client.post("/memory/search", json={"query": "test", "limit": 5})
        assert res_search.status_code == 200
        assert isinstance(res_search.json(), list)

        # 7. Tools list
        res_tools = await client.get("/tools")
        assert res_tools.status_code == 200
        tools_data = res_tools.json()
        assert len(tools_data) >= 15
        assert any(t["name"] == "read_file" for t in tools_data)

        # 8. Checkpoints
        res_chk_create = await client.post("/checkpoints", json={"description": "Test checkpoint from API"})
        assert res_chk_create.status_code == 200
        assert "id" in res_chk_create.json()

        res_chk_list = await client.get("/checkpoints")
        assert res_chk_list.status_code == 200
        assert len(res_chk_list.json()) >= 1

        # 9. Session chat execution
        res_session_2 = await client.post("/session", json={"workspace_root": str(tmp_path)})
        s_id = res_session_2.json()["session_id"]
        res_chat = await client.post(f"/session/{s_id}/chat", json={"prompt": "Hello assistant", "max_turns": 2})
        assert res_chat.status_code == 200
        assert "final_answer" in res_chat.json()

        # 10. Session chat stream (SSE)
        res_session_3 = await client.post("/session", json={"workspace_root": str(tmp_path)})
        s_id3 = res_session_3.json()["session_id"]
        res_stream = await client.post(f"/session/{s_id3}/chat/stream", json={"prompt": "Stream test", "max_turns": 2})
        assert res_stream.status_code == 200
        assert "text/event-stream" in res_stream.headers.get("content-type", "")
        body_text = res_stream.text
        assert "event: start" in body_text
        assert "event: done" in body_text

        # 11. Model unload & loaded inspection
        res_loaded = await client.get("/model/loaded")
        assert res_loaded.status_code == 200
        assert isinstance(res_loaded.json(), list)

        res_unload = await client.post("/model/unload")
        assert res_unload.status_code == 200
        assert res_unload.json()["success"] is True
