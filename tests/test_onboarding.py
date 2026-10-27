from pathlib import Path
from tael.cli.onboarding import run_onboarding_wizard
from tael.config.settings import TaelConfig


def test_onboarding_wizard_generates_config(tmp_path: Path):
    cfg = TaelConfig.load()
    cfg.workspace_root = str(tmp_path)
    cfg.memory.store_dir = str(tmp_path / "memory")

    # Run onboarding
    updated_cfg = run_onboarding_wizard(cfg, interactive=False)
    assert updated_cfg.resource.profile in ("conservative", "balanced")

    # Verify config file written
    target_config = tmp_path / ".tael" / "config.yaml"
    assert target_config.exists()
    content = target_config.read_text(encoding="utf-8")
    assert "model:" in content
    assert "resource:" in content
