from pathlib import Path
from tael.config.settings import TaelConfig
from tael.eval.doctor import SystemDoctor


def test_system_doctor_checks(tmp_path: Path):
    cfg = TaelConfig.load()
    cfg.workspace_root = str(tmp_path)
    cfg.memory.store_dir = str(tmp_path / "memory")

    doctor = SystemDoctor(cfg)
    checks = doctor.run_all_checks()

    check_names = [c.name for c in checks]
    assert "Workspace Confinement" in check_names
    assert "SQLite FTS5 Full-Text Search" in check_names
    assert "Hardware Resource Supervisor" in check_names
    assert "Audit & Redaction Service" in check_names
    assert "Typed Tool Registry" in check_names
    assert "Model Inference Backend" in check_names

    # Confinement and FTS5 must pass
    confinement_check = next(c for c in checks if c.name == "Workspace Confinement")
    assert confinement_check.status == "PASS"

    fts_check = next(c for c in checks if c.name == "SQLite FTS5 Full-Text Search")
    assert fts_check.status == "PASS"
