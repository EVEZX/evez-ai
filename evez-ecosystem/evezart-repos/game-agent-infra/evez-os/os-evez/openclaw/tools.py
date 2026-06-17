"""openclaw.tools — bounded tool executor (FS_READ, FS_WRITE, SHELL)."""
import subprocess, os
from pathlib import Path
from .policy import load_policy, check_kill_switch, assert_fs_read, assert_fs_write, assert_shell


class ToolRunner:
    def __init__(self, policy_path=None, data_dir=None):
        self.policy = load_policy(policy_path)
        self.data_dir = Path(data_dir or os.environ.get("OG_DATA_DIR", "./og_data"))
        self.call_count = 0
        self.max_calls = self.policy.get("budgets", {}).get("max_tool_calls", 1000)

    def _check(self):
        if check_kill_switch(self.policy, self.data_dir):
            raise RuntimeError("KILL SWITCH ACTIVE — STOP file found")
        if self.call_count >= self.max_calls:
            raise RuntimeError(f"Tool call budget exceeded: {self.max_calls}")
        self.call_count += 1

    def read_file(self, path: str) -> str:
        self._check()
        if not assert_fs_read(self.policy, path):
            raise PermissionError(f"FS_READ denied: {path}")
        return Path(path).read_text()

    def write_file(self, path: str, content: str):
        self._check()
        if not assert_fs_write(self.policy, path):
            raise PermissionError(f"FS_WRITE denied: {path}")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content)

    def run_shell(self, cmd: str, timeout=30) -> str:
        self._check()
        if not assert_shell(self.policy, cmd):
            raise PermissionError(f"SHELL denied: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
