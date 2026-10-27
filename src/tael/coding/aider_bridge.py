import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
from pathlib import Path


class AiderBridge:
    """Bridge for delegating focused code modifications and refactoring to Aider using local Granite models."""

    def __init__(self, workspace_root: str, model_name: str = "granite-code:3b", endpoint: str = "http://127.0.0.1:11434"):
        self.workspace_root = str(Path(workspace_root).resolve())
        self.model_name = model_name
        self.endpoint = endpoint

    def is_aider_available(self) -> bool:
        """Check if aider executable is accessible on system PATH."""
        return shutil.which("aider") is not None

    def run_coding_task(
        self,
        instruction: str,
        files: Optional[List[str]] = None,
        auto_commit: bool = False,
        timeout_seconds: float = 180.0,
    ) -> Dict[str, Any]:
        """Execute a coding task via Aider pointing to local model runtime."""
        if not self.is_aider_available():
            return {
                "success": False,
                "error": (
                    "Aider is not installed or not found on PATH. "
                    "Install with: uv pip install aider-chat (or pip install aider-chat). "
                    "TAEL can also use built-in write_file and workspace tools directly."
                ),
                "duration_seconds": 0.0,
            }

        # Formulate Ollama-compatible model flag for Aider
        # E.g. --model ollama/granite-code:3b
        model_flag = f"ollama/{self.model_name}"
        
        cmd = [
            "aider",
            "--model", model_flag,
            "--message", instruction,
            "--yes-always",
        ]

        if not auto_commit:
            cmd.append("--no-auto-commits")

        if files:
            cmd.extend(files)

        # Set environment variables for local OpenAI-compatible endpoint
        env = os.environ.copy()
        env["OLLAMA_API_BASE"] = self.endpoint

        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            duration = time.time() - start_time
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode,
                "duration_seconds": round(duration, 2),
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Aider run timed out after {timeout_seconds} seconds.",
                "duration_seconds": timeout_seconds,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute Aider: {str(e)}",
                "duration_seconds": round(time.time() - start_time, 2),
            }
