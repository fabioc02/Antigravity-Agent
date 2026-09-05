import os
import shlex

class SecuritySandbox:
    def __init__(self, workspace_root: str):
        self.workspace_root = os.path.abspath(workspace_root)
        self.blocked_commands = {'sudo', 'su', 'vim', 'nano', 'top', 'htop', 'ssh', 'reboot', 'shutdown'}

    def validate_path(self, target_path: str) -> str:
        abs_path = os.path.abspath(os.path.join(self.workspace_root, target_path))
        if not abs_path.startswith(self.workspace_root):
            raise PermissionError(f"Path traversal detected: {target_path} resolves outside workspace.")
        return abs_path

    def validate_command(self, command: str) -> None:
        try:
            parts = shlex.split(command)
            if not parts: raise ValueError("Empty command")
            if parts[0] in self.blocked_commands:
                raise PermissionError(f"Command '{parts[0]}' is blocked by security policy.")
        except ValueError as e:
            raise PermissionError(f"Invalid command syntax: {e}")
