import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WorkspaceCheckpoint:
    id: str
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_commit: Optional[str] = None
    backup_dir: Optional[str] = None


class SnapshotManager:
    """Manages workspace snapshots and rollbacks to guarantee safe recovery from failed edits."""

    def __init__(self, workspace_root: str, store_dir: Optional[str] = None):
        self.workspace_root = str(Path(workspace_root).resolve())
        base = Path(store_dir) if store_dir else Path(self.workspace_root) / ".tael"
        self.checkpoints_dir = base / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.meta_file = self.checkpoints_dir / "checkpoints.json"

    def _load_meta(self) -> List[Dict[str, Any]]:
        if self.meta_file.exists():
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_meta(self, items: List[Dict[str, Any]]) -> None:
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)

    def _is_git_repo(self) -> bool:
        return (Path(self.workspace_root) / ".git").exists()

    def create_checkpoint(self, description: str) -> WorkspaceCheckpoint:
        """Create a checkpoint using git commit if in repo, or directory backup."""
        checkpoint_id = f"chk_{int(time.time())}_{os.urandom(2).hex()}"
        git_sha = None
        backup_path_str = None

        if self._is_git_repo():
            try:
                # Check if there are changes to stage
                subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.workspace_root,
                    capture_output=True,
                    timeout=10.0,
                )
                commit_msg = f"tael-checkpoint: {description} [{checkpoint_id}]"
                proc = subprocess.run(
                    ["git", "commit", "-m", commit_msg, "--allow-empty"],
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True,
                    timeout=10.0,
                )
                if proc.returncode == 0:
                    sha_proc = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=self.workspace_root,
                        capture_output=True,
                        text=True,
                        timeout=5.0,
                    )
                    git_sha = sha_proc.stdout.strip()
            except Exception:
                pass

        # Fallback to local file backup if git commit was not made
        if not git_sha:
            dest = self.checkpoints_dir / checkpoint_id
            dest.mkdir(parents=True, exist_ok=True)
            backup_path_str = str(dest)

        chk = WorkspaceCheckpoint(
            id=checkpoint_id,
            description=description,
            git_commit=git_sha,
            backup_dir=backup_path_str,
        )

        all_meta = self._load_meta()
        all_meta.append({
            "id": chk.id,
            "description": chk.description,
            "timestamp": chk.timestamp,
            "git_commit": chk.git_commit,
            "backup_dir": chk.backup_dir,
        })
        self._save_meta(all_meta[-20:])  # Bound history to 20 checkpoints
        return chk

    def rollback(self, checkpoint_id: Optional[str] = None) -> bool:
        """Roll back workspace to a specific checkpoint or the latest one."""
        all_meta = self._load_meta()
        if not all_meta:
            return False

        target = None
        if checkpoint_id:
            for item in all_meta:
                if item["id"] == checkpoint_id:
                    target = item
                    break
        else:
            target = all_meta[-1]

        if not target:
            return False

        if target.get("git_commit") and self._is_git_repo():
            try:
                proc = subprocess.run(
                    ["git", "reset", "--hard", target["git_commit"]],
                    cwd=self.workspace_root,
                    capture_output=True,
                    timeout=15.0,
                )
                return proc.returncode == 0
            except Exception:
                return False

        return False

    def list_checkpoints(self) -> List[Dict[str, Any]]:
        return self._load_meta()
