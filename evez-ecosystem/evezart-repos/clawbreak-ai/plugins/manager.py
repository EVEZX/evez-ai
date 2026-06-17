"""ClawBreak Plugin System — load and run community plugins."""
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

PLUGINS_DIR = Path(__file__).parent.parent / "plugins"

class PluginManager:
    """Load, manage, and execute plugins."""

    def __init__(self, config, memory):
        self.config = config
        self.memory = memory
        self.plugins = {}  # name -> {meta, module}
        self._load_all()

    def _load_all(self):
        """Discover and load all plugins."""
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

        for plugin_dir in PLUGINS_DIR.iterdir():
            if not plugin_dir.is_dir():
                continue
            manifest = plugin_dir / "plugin.json"
            main_file = plugin_dir / "main.py"
            if manifest.exists() and main_file.exists():
                try:
                    meta = json.loads(manifest.read_text())
                    # Dynamic import
                    spec = importlib.util.spec_from_file_location(
                        f"plugin_{meta['name']}", str(main_file)
                    )
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self.plugins[meta["name"]] = {"meta": meta, "module": mod}
                    print(f"Plugin loaded: {meta['name']} v{meta.get('version','?')}")
                except Exception as e:
                    print(f"Plugin load error ({plugin_dir.name}): {e}")

    async def execute(self, plugin_name, method, args=None):
        """Execute a plugin method."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return {"error": f"Plugin not found: {plugin_name}"}

        fn = getattr(plugin["module"], method, None)
        if not fn:
            return {"error": f"Method {method} not found in {plugin_name}"}

        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(args or {}, self.config, self.memory)
            else:
                result = fn(args or {}, self.config, self.memory)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    def list_plugins(self):
        """List all loaded plugins."""
        return [
            {
                "name": p["meta"]["name"],
                "version": p["meta"].get("version", "?"),
                "description": p["meta"].get("description", ""),
                "methods": [m for m in dir(p["module"]) if not m.startswith("_")],
            }
            for p in self.plugins.values()
        ]

    def install_from_url(self, url):
        """Install a plugin from a Git URL."""
        name = url.rstrip("/").split("/")[-1].replace(".git", "")
        target = PLUGINS_DIR / name
        result = subprocess.run(
            ["git", "clone", url, str(target)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            # Reload
            self._load_all()
            return {"status": "installed", "name": name}
        return {"error": result.stderr[:200]}


# Need asyncio import
import asyncio
PYEOF