"""EVEZ Code Module - Code Execution & Analysis"""
import subprocess
import tempfile
from pathlib import Path

class CodeExecutor:
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.results: dict[str, dict] = {}
    
    def python(self, code: str) -> dict:
        """Execute Python code in isolated context"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            try:
                result = subprocess.run(
                    ['python3', f.name],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return {
                    "ok": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode
                }
            finally:
                Path(f.name).unlink(missing_ok=True)
    
    def hash_code(self, code: str) -> str:
        """Generate transform_hash for code"""
        import hashlib
        return "sha256:" + hashlib.sha256(code.encode()).hexdigest()[:16]

executor = CodeExecutor()