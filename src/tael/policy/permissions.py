from enum import Enum
from pathlib import Path
from typing import Optional


class PermissionLevel(str, Enum):
    READ_WORKSPACE = "read_workspace"
    WRITE_WORKSPACE = "write_workspace"
    EXECUTE_COMMAND = "execute_command"
    INTERNET_ACCESS = "internet_access"
    APP_LAUNCH = "app_launch"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"


class WorkspaceConfinementError(PermissionError):
    """Raised when an operation attempts to access paths outside the permitted workspace."""
    pass


def validate_workspace_path(path_str: str, workspace_root: str, allow_root: bool = True) -> Path:
    """
    Validate that target path resolves strictly within the workspace root.
    Protects against path traversal (../), symlinks escaping the workspace, and alternate path forms.
    """
    root = Path(workspace_root).resolve()
    target = Path(path_str)
    
    if not target.is_absolute():
        target = (root / target).resolve()
    else:
        target = target.resolve()

    if not allow_root and target == root:
        raise WorkspaceConfinementError(f"Direct operation on workspace root itself is restricted: {target}")

    try:
        # relative_to raises ValueError if target is not within root
        target.relative_to(root)
    except ValueError:
        raise WorkspaceConfinementError(
            f"Access denied: path '{path_str}' resolves to '{target}' which is outside workspace root '{root}'"
        )

    return target
