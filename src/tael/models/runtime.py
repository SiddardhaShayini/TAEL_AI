from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx

from tael.config.settings import ModelConfig


class ModelRuntimeError(Exception):
    pass


class ModelRuntimeManager:
    """Manages local model runtime lifecycle, health checks, and safety checks."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self._validate_loopback(config.endpoint)

    def _validate_loopback(self, endpoint: str) -> None:
        """Enforce loopback-only binding by default for security (§8.2)."""
        parsed = urlparse(endpoint)
        hostname = parsed.hostname or ""
        if hostname not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError(
                f"Security violation: Model endpoint '{endpoint}' is not bound to loopback (127.0.0.1 / localhost)."
            )

    def check_health(self) -> bool:
        """Verify the local inference server (e.g. Ollama) is reachable and healthy."""
        if self.config.backend == "mock":
            return True
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.config.endpoint}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    def list_installed_models(self) -> List[str]:
        """List models installed in the local Ollama instance."""
        if self.config.backend == "mock":
            return [self.config.model_name]
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(f"{self.config.endpoint}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    return models
                return []
        except Exception:
            return []

    def is_model_available(self, model_name: Optional[str] = None) -> bool:
        """Check if target model is present locally."""
        target = model_name or self.config.model_name
        installed = self.list_installed_models()
        return any(target in m for m in installed)
