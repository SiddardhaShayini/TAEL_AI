from pathlib import Path
from typing import Literal, Optional
import os
import yaml
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    backend: Literal["ollama", "llamacpp", "mock"] = "ollama"
    endpoint: str = "http://127.0.0.1:11434"
    model_name: str = "granite-code:3b"
    context_window: int = 4096
    max_output_tokens: int = 1024
    temperature: float = 0.2
    timeout_seconds: float = 90.0


class ResourceConfig(BaseModel):
    profile: Literal["auto", "conservative", "balanced"] = "auto"
    max_ram_percent: float = 85.0
    min_free_ram_gb: float = 1.5
    max_cpu_threads: int = 4
    sampling_interval_seconds: float = 2.0


class PolicyConfig(BaseModel):
    require_approval_write: bool = True
    require_approval_execute: bool = True
    require_approval_internet: bool = True
    require_approval_app_launch: bool = True
    allow_internet: bool = False
    audit_logging: bool = True
    audit_log_path: Optional[str] = None


class MemoryConfig(BaseModel):
    enabled: bool = True
    store_dir: Optional[str] = None
    token_budget: int = 1000
    fts_enabled: bool = True
    max_results: int = 10


class ServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 7860
    request_timeout_seconds: float = 120.0
    auth_token: Optional[str] = None


class TaelConfig(BaseModel):
    workspace_root: str = Field(default_factory=lambda: os.getcwd())
    model: ModelConfig = Field(default_factory=ModelConfig)
    resource: ResourceConfig = Field(default_factory=ResourceConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)

    @classmethod
    def get_default_config_path(cls) -> Path:
        return Path(__file__).parent / "defaults.yaml"

    @classmethod
    def get_user_tael_dir(cls, workspace_root: Optional[str] = None) -> Path:
        env_home = os.environ.get("TAEL_HOME")
        if env_home:
            path = Path(env_home)
            try:
                path.mkdir(parents=True, exist_ok=True)
                return path
            except OSError:
                pass

        try:
            path = Path.home() / ".tael"
            path.mkdir(parents=True, exist_ok=True)
            # Verify actual write permission
            test_probe = path / ".write_probe"
            test_probe.touch()
            test_probe.unlink(missing_ok=True)
            return path
        except OSError:
            # Fall back to workspace or temp dir if home directory is restricted
            base = Path(workspace_root) if workspace_root else Path.cwd()
            path = base / ".tael"
            try:
                path.mkdir(parents=True, exist_ok=True)
                return path
            except OSError:
                import tempfile
                path = Path(tempfile.gettempdir()) / "tael"
                path.mkdir(parents=True, exist_ok=True)
                return path

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "TaelConfig":
        """Load configuration from default YAML, user config, and environment variables."""
        data = {}
        default_file = cls.get_default_config_path()
        if default_file.exists():
            with open(default_file, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if loaded:
                    data.update(loaded)

        # Check user config at ~/.tael/config.yaml or explicit path
        search_paths = [
            config_path,
            Path.cwd() / ".tael" / "config.yaml",
            Path.home() / ".tael" / "config.yaml",
        ]

        for p in search_paths:
            try:
                if p and p.exists() and p.is_file():
                    with open(p, "r", encoding="utf-8") as f:
                        user_data = yaml.safe_load(f)
                        if user_data:
                            # Deep merge top-level keys
                            for k, v in user_data.items():
                                if isinstance(v, dict) and k in data and isinstance(data[k], dict):
                                    data[k].update(v)
                                else:
                                    data[k] = v
                    break
            except OSError:
                continue

        cfg = cls(**data)

        # Set default memory store_dir and audit_log_path if not provided
        tael_dir = cls.get_user_tael_dir(cfg.workspace_root)
        if not cfg.memory.store_dir:
            cfg.memory.store_dir = str(tael_dir / "memory")
        if not cfg.policy.audit_log_path:
            cfg.policy.audit_log_path = str(tael_dir / "audit.log")

        # Canonicalize workspace root
        cfg.workspace_root = str(Path(cfg.workspace_root).resolve())
        return cfg
