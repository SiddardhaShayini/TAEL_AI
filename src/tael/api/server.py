from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel

from tael import __version__
from tael.config.settings import TaelConfig
from tael.core.orchestrator import TaskOrchestrator
from tael.core.session import SessionState
from tael.memory.models import MemoryCategory
from tael.memory.store import MemoryStore
from tael.models.runtime import ModelRuntimeManager
from tael.resources.monitor import ResourceMonitor


def create_app(config: Optional[TaelConfig] = None) -> FastAPI:
    cfg = config or TaelConfig.load()
    app = FastAPI(
        title="TAEL AI Local Service",
        description="Local-first agent orchestrator and memory API",
        version=__version__,
    )

    # Active in-memory sessions
    sessions: Dict[str, SessionState] = {}
    orchestrator = TaskOrchestrator(cfg)
    memory_store = MemoryStore(cfg.workspace_root, cfg.memory.store_dir)
    resource_monitor = ResourceMonitor(cfg.resource.profile)

    # Simple bearer token authentication if configured
    def verify_auth(authorization: Optional[str] = Header(None)) -> bool:
        if not cfg.server.auth_token:
            return True
        if not authorization or authorization != f"Bearer {cfg.server.auth_token}":
            raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing bearer token")
        return True

    @app.get("/health")
    def health_check():
        return {"status": "ok", "version": __version__}

    @app.get("/status", dependencies=[Depends(verify_auth)])
    def get_status():
        snapshot = resource_monitor.sample()
        runtime = ModelRuntimeManager(cfg.model)
        installed = runtime.list_installed_models() if runtime.check_health() else []
        return {
            "version": __version__,
            "workspace_root": cfg.workspace_root,
            "resource": {
                "profile": snapshot.active_profile,
                "total_ram_gb": snapshot.total_ram_gb,
                "available_ram_gb": snapshot.available_ram_gb,
                "ram_percent": snapshot.ram_percent,
                "cpu_percent": snapshot.cpu_percent,
                "is_under_pressure": snapshot.is_under_pressure,
                "pressure_reason": snapshot.pressure_reason,
            },
            "model": {
                "backend": cfg.model.backend,
                "endpoint": cfg.model.endpoint,
                "model_name": cfg.model.model_name,
                "online": runtime.check_health(),
                "installed_models": installed,
            },
        }

    class CreateSessionRequest(BaseModel):
        workspace_root: Optional[str] = None

    @app.post("/session", dependencies=[Depends(verify_auth)])
    def create_session(req: CreateSessionRequest):
        ws = req.workspace_root or cfg.workspace_root
        session = SessionState(workspace_root=ws)
        sessions[session.session_id] = session
        return {"session_id": session.session_id, "workspace_root": ws}

    class ChatRequest(BaseModel):
        prompt: str
        max_turns: int = 10

    @app.post("/session/{session_id}/chat", dependencies=[Depends(verify_auth)])
    def session_chat(session_id: str, req: ChatRequest):
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        result = orchestrator.execute_task(req.prompt, session=session, max_turns=req.max_turns)
        return result

    @app.post("/session/{session_id}/cancel", dependencies=[Depends(verify_auth)])
    def cancel_session(session_id: str):
        session = sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session.cancel()
        return {"session_id": session_id, "cancelled": True}

    @app.get("/memory", dependencies=[Depends(verify_auth)])
    def list_memory(category: Optional[str] = None):
        cat_enum = MemoryCategory(category) if category else None
        entries = memory_store.list_entries(category=cat_enum, active_only=True)
        return [
            {
                "id": e.id,
                "category": e.category.value,
                "title": e.title,
                "content": e.content,
                "tags": e.tags,
                "verified": e.verified,
                "source_paths": e.source_paths,
            }
            for e in entries
        ]

    class MemorySearchRequest(BaseModel):
        query: str
        limit: int = 10

    @app.post("/memory/search", dependencies=[Depends(verify_auth)])
    def search_memory(req: MemorySearchRequest):
        results = memory_store.search_fts(req.query, limit=req.limit)
        return [
            {
                "id": r.id,
                "category": r.category.value,
                "title": r.title,
                "content": r.content,
                "verified": r.verified,
            }
            for r in results
        ]

    return app
