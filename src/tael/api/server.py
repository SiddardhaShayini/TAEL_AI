from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from tael import __version__
from tael.config.settings import TaelConfig
from tael.core.orchestrator import TaskOrchestrator
from tael.core.session import SessionState
from tael.memory.models import MemoryCategory
from tael.memory.store import MemoryStore
from tael.models.runtime import ModelRuntimeManager
from tael.resources.monitor import ResourceMonitor


def get_logo_svg_path(workspace_root: str) -> Optional[Path]:
    candidates = [
        Path(workspace_root) / "assets" / "tael-logo-v3.svg",
        Path(__file__).parents[3] / "assets" / "tael-logo-v3.svg",
        Path.cwd() / "assets" / "tael-logo-v3.svg",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


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

    @app.get("/logo.svg")
    def get_logo():
        logo_path = get_logo_svg_path(cfg.workspace_root)
        if logo_path:
            return Response(content=logo_path.read_text(encoding="utf-8"), media_type="image/svg+xml")
        raise HTTPException(status_code=404, detail="Logo SVG not found")

    @app.get("/", response_class=HTMLResponse)
    def index():
        snapshot = resource_monitor.sample()
        runtime = ModelRuntimeManager(cfg.model)
        ollama_ok = runtime.check_health()
        installed = runtime.list_installed_models() if ollama_ok else []
        status_badge = '<span style="color:#2BB3A3;font-weight:bold;">ONLINE</span>' if ollama_ok else '<span style="color:#FFB547;font-weight:bold;">OFFLINE (Mock Mode)</span>'
        pressure_badge = '<span style="color:#ff6b6b;font-weight:bold;">YES</span>' if snapshot.is_under_pressure else '<span style="color:#2BB3A3;font-weight:bold;">NO</span>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>TAEL AI — Local Studio & Dashboard</title>
  <link rel="icon" type="image/svg+xml" href="/logo.svg">
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0; padding: 0;
      background-color: #08161A;
      color: #E8F1EE;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      display: flex; flex-direction: column; align-items: center; min-height: 100vh;
    }}
    .container {{
      max-width: 900px; width: 95%; margin: 30px auto;
      background: #0F2A30; border-radius: 16px; border: 1px solid #2BB3A3;
      padding: 28px; box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }}
    .header {{
      display: flex; align-items: center; gap: 20px; border-bottom: 1px solid rgba(43,179,163,0.3);
      padding-bottom: 20px; margin-bottom: 20px;
    }}
    .header img {{ width: 80px; height: 80px; }}
    h1 {{ margin: 0 0 6px 0; color: #E8F1EE; font-size: 26px; }}
    .tagline {{ margin: 0; color: #2BB3A3; font-size: 14px; font-weight: 500; }}
    .tabs {{ display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 1px solid rgba(43,179,163,0.2); padding-bottom: 8px; }}
    .tab-btn {{
      background: transparent; border: none; color: #E8F1EE; padding: 8px 16px; border-radius: 6px;
      font-weight: 600; cursor: pointer; transition: 0.2s;
    }}
    .tab-btn.active {{ background: #2BB3A3; color: #08161A; }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin: 20px 0; }}
    .card {{
      background: #08161A; border: 1px solid rgba(43,179,163,0.3); border-radius: 10px; padding: 16px;
    }}
    .card-title {{ font-size: 12px; text-transform: uppercase; color: #2BB3A3; margin-bottom: 6px; letter-spacing: 0.5px; }}
    .card-val {{ font-size: 20px; font-weight: bold; color: #E8F1EE; }}
    .chat-box {{
      background: #08161A; border: 1px solid rgba(43,179,163,0.3); border-radius: 10px;
      padding: 16px; min-height: 250px; max-height: 450px; overflow-y: auto; margin-bottom: 16px;
    }}
    .msg {{ margin-bottom: 14px; line-height: 1.5; }}
    .msg.user {{ color: #FFB547; font-weight: 600; }}
    .msg.assistant {{ color: #E8F1EE; background: #0F2A30; padding: 12px; border-radius: 8px; border-left: 3px solid #2BB3A3; }}
    .tool-pill {{ display: inline-block; background: rgba(43,179,163,0.2); border: 1px solid #2BB3A3; color: #2BB3A3; font-size: 12px; padding: 3px 8px; border-radius: 4px; margin-top: 6px; }}
    .input-row {{ display: flex; gap: 10px; }}
    textarea {{
      flex: 1; background: #08161A; border: 1px solid rgba(43,179,163,0.4); border-radius: 8px;
      color: #E8F1EE; padding: 12px; font-family: inherit; font-size: 14px; resize: vertical; min-height: 50px;
    }}
    textarea:focus {{ outline: none; border-color: #2BB3A3; }}
    .btn {{
      display: inline-block; background: #2BB3A3; color: #08161A; padding: 10px 20px; border-radius: 8px;
      text-decoration: none; font-weight: bold; border: none; cursor: pointer; transition: background 0.2s;
    }}
    .btn:hover {{ background: #FFB547; }}
    .btn-outline {{
      background: transparent; border: 1px solid #2BB3A3; color: #2BB3A3;
    }}
    .btn-outline:hover {{ background: #2BB3A3; color: #08161A; }}
    .footer {{ margin-top: 24px; display: flex; gap: 12px; flex-wrap: wrap; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <img src="/logo.svg" alt="TAEL AI Logo" />
      <div>
        <h1>TAEL AI Studio (v{__version__})</h1>
        <p class="tagline">Task-Adaptive Efficient Language AI &mdash; Capable local AI, built for everyday hardware.</p>
      </div>
    </div>

    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('chat-tab', this)">Interactive Agent Chat</button>
      <button class="tab-btn" onclick="switchTab('system-tab', this)">System Hardware Telemetry</button>
      <button class="tab-btn" onclick="switchTab('tools-tab', this)">Registered Tools</button>
    </div>

    <div id="chat-tab" class="tab-content active">
      <div id="chat-history" class="chat-box">
        <div class="msg assistant">
          Welcome to TAEL AI Studio. Enter a natural language coding task, technical question, or command below to execute.
        </div>
      </div>
      <div class="input-row">
        <textarea id="user-input" placeholder="e.g. Inspect the project directory and explain its architecture..."></textarea>
        <button id="send-btn" class="btn" onclick="sendTask()">Run Task</button>
      </div>
    </div>

    <div id="system-tab" class="tab-content">
      <div class="grid">
        <div class="card">
          <div class="card-title">Resource Profile</div>
          <div class="card-val">{snapshot.active_profile.upper()}</div>
        </div>
        <div class="card">
          <div class="card-title">RAM Available / Total</div>
          <div class="card-val">{snapshot.available_ram_gb} GB / {snapshot.total_ram_gb} GB</div>
        </div>
        <div class="card">
          <div class="card-title">CPU Logical Cores</div>
          <div class="card-val">{snapshot.cpu_count_logical} Cores ({snapshot.cpu_percent}% load)</div>
        </div>
        <div class="card">
          <div class="card-title">System Under Pressure</div>
          <div class="card-val">{pressure_badge}</div>
        </div>
        <div class="card">
          <div class="card-title">Model Backend</div>
          <div class="card-val">{cfg.model.model_name}</div>
        </div>
        <div class="card">
          <div class="card-title">Inference Engine Status</div>
          <div class="card-val">{status_badge}</div>
        </div>
      </div>
    </div>

    <div id="tools-tab" class="tab-content">
      <div style="background:#08161A; padding:16px; border-radius:10px; border:1px solid rgba(43,179,163,0.3);">
        <p style="margin-top:0; color:#2BB3A3; font-weight:bold;">Active Typed Tools in Registry ({len(orchestrator.tools.list_tools())} Tools)</p>
        <ul style="margin:0; padding-left:20px; line-height:1.8;">
          {"".join(f"<li><strong>{t.name}</strong> <span style='color:#FFB547;'>({t.permission.value})</span>: {t.description}</li>" for t in orchestrator.tools.list_tools())}
        </ul>
      </div>
    </div>

    <div class="footer">
      <a class="btn" href="/docs">API Interactive Docs (Swagger)</a>
      <a class="btn btn-outline" href="/status">JSON Status Endpoint</a>
      <a class="btn btn-outline" href="/tools">Tools Schema</a>
      <a class="btn btn-outline" href="/health">Health Check</a>
    </div>
  </div>

  <script>
    let activeSessionId = null;

    function switchTab(tabId, btn) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      btn.classList.add('active');
    }}

    async function ensureSession() {{
      if (activeSessionId) return activeSessionId;
      try {{
        const res = await fetch('/session', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{}})
        }});
        const data = await res.json();
        activeSessionId = data.session_id;
        return activeSessionId;
      }} catch (e) {{
        console.error('Failed to create session:', e);
        return null;
      }}
    }}

    async function sendTask() {{
      const input = document.getElementById('user-input');
      const text = input.value.trim();
      if (!text) return;

      const history = document.getElementById('chat-history');
      const sendBtn = document.getElementById('send-btn');
      
      history.innerHTML += `<div class="msg user">User: ${{text}}</div>`;
      input.value = '';
      sendBtn.disabled = true;
      sendBtn.innerText = 'Running...';
      history.scrollTop = history.scrollHeight;

      const sessionId = await ensureSession();
      if (!sessionId) {{
        history.innerHTML += `<div class="msg assistant" style="color:red;">Error initializing session.</div>`;
        sendBtn.disabled = false;
        sendBtn.innerText = 'Run Task';
        return;
      }}

      try {{
        const res = await fetch(`/session/${{sessionId}}/chat`, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ prompt: text, max_turns: 6 }})
        }});
        const result = await res.json();
        let toolsHtml = '';
        if (result.tools_executed && result.tools_executed.length > 0) {{
          toolsHtml = '<br>' + result.tools_executed.map(t => `<span class="tool-pill">Tool: ${{t.tool}} (${{t.success ? 'Success' : 'Failed'}})</span>`).join(' ');
        }}
        history.innerHTML += `<div class="msg assistant">${{result.final_answer || 'Task completed.'}}${{toolsHtml}}</div>`;
      }} catch (err) {{
        history.innerHTML += `<div class="msg assistant" style="color:red;">Execution failed: ${{err.message}}</div>`;
      }} finally {{
        sendBtn.disabled = false;
        sendBtn.innerText = 'Run Task';
        history.scrollTop = history.scrollHeight;
      }}
    }}
  </script>
</body>
</html>"""

    @app.get("/tools", dependencies=[Depends(verify_auth)])
    def list_tools():
        schemas = orchestrator.tools.get_schemas()
        return schemas

    @app.get("/checkpoints", dependencies=[Depends(verify_auth)])
    def list_checkpoints():
        from tael.policy.rollback import SnapshotManager
        mgr = SnapshotManager(cfg.workspace_root)
        return mgr.list_checkpoints()

    class CreateCheckpointRequest(BaseModel):
        description: str

    @app.post("/checkpoints", dependencies=[Depends(verify_auth)])
    def create_checkpoint(req: CreateCheckpointRequest):
        from tael.policy.rollback import SnapshotManager
        mgr = SnapshotManager(cfg.workspace_root)
        chk = mgr.create_checkpoint(req.description)
        return {"id": chk.id, "description": chk.description, "timestamp": chk.timestamp}

    class RollbackRequest(BaseModel):
        checkpoint_id: Optional[str] = None

    @app.post("/rollback", dependencies=[Depends(verify_auth)])
    def rollback_workspace(req: RollbackRequest):
        from tael.policy.rollback import SnapshotManager
        mgr = SnapshotManager(cfg.workspace_root)
        ok = mgr.rollback(req.checkpoint_id)
        if not ok:
            raise HTTPException(status_code=400, detail="Rollback failed")
        return {"success": True, "target": req.checkpoint_id or "latest"}

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
