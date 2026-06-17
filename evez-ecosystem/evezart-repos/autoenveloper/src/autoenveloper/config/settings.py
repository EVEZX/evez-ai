"""
Autoenveloper — Configuration
"""
import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    openai_api_key:  str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    supabase_url:    str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key:    str = field(default_factory=lambda: os.getenv("SUPABASE_KEY", ""))
    github_token:    str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    slack_token:     str = field(default_factory=lambda: os.getenv("SLACK_BOT_TOKEN", ""))
    model:           str = field(default_factory=lambda: os.getenv("MODEL", "gpt-4o"))
    temperature:     float = 0.1
    max_tokens:      int = 4096
    max_iterations:  int = 25

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()
