from pathlib import Path
from tael.config.settings import TaelConfig


def test_default_config_loading():
    cfg = TaelConfig.load()
    assert cfg.model.backend in ("ollama", "llamacpp", "mock")
    assert cfg.model.context_window >= 2048
    assert cfg.resource.max_ram_percent > 50.0
    assert cfg.policy.require_approval_write is True
    assert cfg.memory.enabled is True
    assert Path(cfg.workspace_root).is_absolute()
