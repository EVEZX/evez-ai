"""ClawBreak - Tool execution engine."""
import subprocess
import json
import os
import time
import httpx
from pathlib import Path

class ToolEngine:
    def __init__(self, config, memory):
        self.config = config
        self.memory = memory
        self.tools = {
            "shell": self._tool_shell,
            "search": self._tool_search,
            "memory": self._tool_memory,
            "file": self._tool_file,
            "sysinfo": self._tool_sysinfo,
        }

    def get_tool_descriptions(self):
        """Returns tool descriptions for the system prompt."""
        descs = []
        for name, fn in self.tools.items():
            descs.append(f"- {name}: {fn.__doc__.strip()}")
        return "\n".join(descs)

    def execute(self, tool_name, args):
        """Execute a tool and return the result."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}. Available: {list(self.tools.keys())}"}

        try:
            result = self.tools[tool_name](**args if isinstance(args, dict) else {"input": str(args)})
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

    def _tool_shell(self, command="", timeout=None):
        """Run a bash command. Args: command (str), timeout (int, default 30)"""
        timeout = timeout or self.config.get("tools", "shell_timeout")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=timeout, cwd=os.path.expanduser("~")
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output[:10000]  # Limit output
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"

    def _tool_search(self, query="", categories="general", engines="", limit=5):
        """Search the web via SearXNG. Args: query (str), categories (str), limit (int)"""
        searx_url = self.config.get("tools", "searxng_url")
        params = {"q": query, "format": "json", "categories": categories}
        if engines:
            params["engines"] = engines

        try:
            resp = httpx.get(f"{searx_url}/search", params=params, timeout=10)
            data = resp.json()
            results = data.get("results", [])[:limit]
            if not results:
                return f"No results for: {query}"
            output = []
            for r in results:
                output.append(f"## {r.get('title','')}\n{r.get('url','')}\n{r.get('content','')[:200]}\n")
            return "\n".join(output)
        except Exception as e:
            return f"Search error: {e}"

    def _tool_memory(self, action="recall", key="", value="", query="", category="general"):
        """Store or recall facts. Args: action (store|recall|list|delete), key, value, query, category"""
        if action == "store":
            if not key or not value:
                return "Error: key and value required for store"
            self.memory.store_fact(key, value, category)
            return f"Stored: {key} = {value[:100]}"
        elif action == "recall":
            if not query:
                return "Error: query required for recall"
            facts = self.memory.recall_facts(query)
            if not facts:
                return f"No facts matching: {query}"
            return "\n".join(f"- {f['key']}: {f['value'][:100]} [{f['category']}]" for f in facts)
        elif action == "list":
            facts = self.memory.list_facts(category if category != "general" else None)
            if not facts:
                return "No facts stored"
            return "\n".join(f"- {f['key']}: {f['value'][:80]} [{f['category']}] accessed {f['access_count']}x" for f in facts)
        elif action == "delete":
            if not key:
                return "Error: key required for delete"
            self.memory.delete_fact(key)
            return f"Deleted: {key}"
        else:
            return f"Unknown action: {action}. Use: store, recall, list, delete"

    def _tool_file(self, action="read", path="", content=""):
        """Read or write files. Args: action (read|write|list), path, content"""
        if action == "read":
            if not path:
                return "Error: path required"
            try:
                p = Path(os.path.expanduser(path))
                return p.read_text()[:10000]
            except Exception as e:
                return f"Read error: {e}"
        elif action == "write":
            if not path or not content:
                return "Error: path and content required"
            try:
                p = Path(os.path.expanduser(path))
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
                return f"Written {len(content)} chars to {path}"
            except Exception as e:
                return f"Write error: {e}"
        elif action == "list":
            target = Path(os.path.expanduser(path or "~"))
            if target.is_dir():
                items = list(target.iterdir())[:50]
                return "\n".join(f"{'📁' if i.is_dir() else '📄'} {i.name}" for i in items)
            return f"Not a directory: {path}"
        return f"Unknown action: {action}"

    def _tool_sysinfo(self):
        """Get system information. No args needed."""
        import platform
        try:
            mem_info = subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=5).stdout
        except:
            mem_info = "unavailable"
        try:
            disk_info = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5).stdout
        except:
            disk_info = "unavailable"

        return f"""System: {platform.system()} {platform.release()}
Machine: {platform.machine()}
Python: {platform.python_version()}
CPU count: {os.cpu_count()}
PID: {os.getpid()}
Uptime: {subprocess.run(['uptime', '-p'], capture_output=True, text=True, timeout=5).stdout.strip()}

Memory:
{mem_info}

Disk:
{disk_info}"""

    def parse_tool_calls(self, text):
        """Parse tool calls from LLM response text. Supports [tool:name(args)] syntax."""
        import re
        calls = []
        pattern = r'\[tool:(\w+)\((.*?)\)\]'
        for match in re.finditer(pattern, text):
            tool_name = match.group(1)
            args_str = match.group(2)
            try:
                # Try parsing as JSON
                args = json.loads(args_str)
            except:
                # Fall back to simple key=value parsing
                args = {"input": args_str}
            calls.append({"name": tool_name, "args": args})
        return calls
