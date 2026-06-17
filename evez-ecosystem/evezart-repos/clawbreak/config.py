"""ClawBreak - Free AI Agent Platform. Config management."""
import os
import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8080,
    },
    "llm": {
        "base_url": "https://api.vultrinference.com/v1",
        "api_key": "",
        "model": "zai-org/GLM-5.1-FP8",
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "memory": {
        "db_path": "data/clawbreak.db",
        "max_context_messages": 20,
    },
    "tools": {
        "shell_timeout": 30,
        "searxng_url": "http://127.0.0.1:8888",
    },
    "system_prompt": """You are ClawBreak, a helpful AI assistant running on a self-hosted platform.
You can execute tools to help the user. Available tools:
- shell: Run bash commands (use for system tasks, file operations, installing software)
- search: Search the web using SearXNG (use for finding information)
- memory: Store and recall facts (use for remembering important information)
- file: Read and write files (use for code, configs, notes)
- sysinfo: Get system information

When the user asks you to do something, USE YOUR TOOLS. Don't just describe what you'd do - do it.
Be concise, direct, and actually helpful.""",
}

class Config:
    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        self.data = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        # File config
        if self.config_path.exists():
            with open(self.config_path) as f:
                file_cfg = yaml.safe_load(f) or {}
                self._deep_merge(self.data, file_cfg)

        # Environment overrides
        if os.getenv("CLAWBREAK_LLM_API_KEY"):
            self.data["llm"]["api_key"] = os.getenv("CLAWBREAK_LLM_API_KEY")
        if os.getenv("CLAWBREAK_LLM_BASE_URL"):
            self.data["llm"]["base_url"] = os.getenv("CLAWBREAK_LLM_BASE_URL")
        if os.getenv("CLAWBREAK_LLM_MODEL"):
            self.data["llm"]["model"] = os.getenv("CLAWBREAK_LLM_MODEL")
        if os.getenv("CLAWBREAK_PORT"):
            self.data["server"]["port"] = int(os.getenv("CLAWBREAK_PORT"))

    def _deep_merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def get(self, *keys):
        val = self.data
        for k in keys:
            val = val[k]
        return val

    def save(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.dump(self.data, f, default_flow_style=False)
