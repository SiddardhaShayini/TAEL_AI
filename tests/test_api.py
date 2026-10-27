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
