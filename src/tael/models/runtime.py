from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import httpx

from tael.config.settings import ModelConfig


class ModelRuntimeError(Exception):
    pass


class ModelRuntimeManager:
    """Manages local model runtime lifecycle, health checks, model eviction, and safety checks."""

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

    def list_loaded_models(self) -> List[Dict[str, Any]]:
        """List models currently loaded in RAM/VRAM by Ollama."""
        if self.config.backend == "mock":
            return []
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.config.endpoint}/api/ps")
                if res.status_code == 200:
                    return res.json().get("models", [])
                return []
        except Exception:
            return []

    def unload_model(self, model_name: Optional[str] = None) -> bool:
        """
        Explicitly unload model from RAM and terminate Ollama's background llama.cpp runner.
        Crucial for everyday 8GB RAM laptops to reclaim memory immediately.
        """
        if self.config.backend == "mock":
            return True
        target = model_name or self.config.model_name
        try:
            with httpx.Client(timeout=5.0) as client:
                # Setting keep_alive: 0 signals Ollama to immediately evict the model from memory
                res = client.post(
                    f"{self.config.endpoint}/api/generate",
                    json={"model": target, "keep_alive": 0},
                )
                return res.status_code == 200
        except Exception:
            return False
