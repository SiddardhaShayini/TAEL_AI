from typing import Callable, Dict, Any, Optional
from tael.policy.permissions import PermissionLevel
from tael.config.settings import PolicyConfig


class ApprovalDecision:
    def __init__(self, granted: bool, reason: str = ""):
        self.granted = granted
        self.reason = reason


ApprovalCallback = Callable[[str, PermissionLevel, Dict[str, Any]], bool]


def default_cli_approver(tool_name: str, permission: PermissionLevel, args: Dict[str, Any]) -> bool:
    """Default interactive CLI prompt for action approval."""
    print(f"\n[!] PERMISSION REQUIRED: {permission.value}")
    print(f"    Tool: {tool_name}")
    print(f"    Arguments: {args}")
    try:
        choice = input("    Approve this action? (y/N): ").strip().lower()
        return choice in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


class ApprovalManager:
    def __init__(
        self,
        config: PolicyConfig,
        custom_approver: Optional[ApprovalCallback] = None,
    ):
        self.config = config
        self.approver: ApprovalCallback = custom_approver or default_cli_approver
        # Set of permissions granted globally for the current session
        self.session_grants = set()

    def requires_approval(self, permission: PermissionLevel) -> bool:
        """Check if this permission level requires explicit user confirmation under active policy."""
        if permission == PermissionLevel.READ_WORKSPACE:
            return False
        if permission == PermissionLevel.WRITE_WORKSPACE:
            return self.config.require_approval_write
        if permission == PermissionLevel.EXECUTE_COMMAND:
            return self.config.require_approval_execute
        if permission == PermissionLevel.INTERNET_ACCESS:
            return not self.config.allow_internet or self.config.require_approval_internet
        if permission == PermissionLevel.APP_LAUNCH:
            return self.config.require_approval_app_launch
        if permission == PermissionLevel.EXTERNAL_SIDE_EFFECT:
            return True
        return True

    def request_approval(
        self,
        tool_name: str,
        permission: PermissionLevel,
        arguments: Dict[str, Any],
    ) -> ApprovalDecision:
        """Evaluate approval for an action."""
        # Check if action does not need approval
        if not self.requires_approval(permission):
            return ApprovalDecision(True, "Auto-approved by policy")

        # Check if permission has been session-granted
        if permission in self.session_grants:
            return ApprovalDecision(True, f"Permission {permission.value} was previously approved for this session")

        # Call the user/client approver
        granted = self.approver(tool_name, permission, arguments)
        if granted:
            return ApprovalDecision(True, "Approved by user")
        else:
            return ApprovalDecision(False, f"Denied by user for action {tool_name} ({permission.value})")
