"""ClawBreak MCP Client — connects to external tool servers."""
import httpx
import json
import asyncio
from typing import Any

class MCPClient:
    """Client for Model Context Protocol servers (Composio, etc.)."""

    def __init__(self, config):
        self.config = config
        self.servers = config.data.get("mcp", {}).get("servers", {})
        self._tool_cache = {}  # server_name -> [tools]

    async def list_tools(self, server_name=None):
        """List available tools from MCP servers."""
        results = {}
        servers = {server_name: self.servers[server_name]} if server_name else self.servers

        for name, server in servers.items():
            try:
                tools = await self._call_server(name, "tools/list", {})
                results[name] = tools
                self._tool_cache[name] = tools
            except Exception as e:
                results[name] = {"error": str(e)}

        return results

    async def call_tool(self, server_name, tool_name, arguments):
        """Call a tool on an MCP server."""
        return await self._call_server(server_name, "tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

    async def _call_server(self, server_name, method, params):
        """Make an MCP JSON-RPC call."""
        server = self.servers.get(server_name)
        if not server:
            return {"error": f"Unknown MCP server: {server_name}"}

        transport = server.get("transport", {})
        url = transport.get("url", "")
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

        # Add auth headers
        for k, v in transport.get("headers", {}).items():
            headers[k] = v

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            # Handle SSE response
            text = resp.text
            for line in text.splitlines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if "result" in data:
                            content = data["result"].get("content", [])
                            for c in content:
                                if c.get("type") == "text":
                                    try:
                                        return json.loads(c["text"])
                                    except:
                                        return {"text": c["text"]}
                            return data["result"]
                    except json.JSONDecodeError:
                        pass

            return {"raw": text[:500]}

    async def search_and_execute(self, use_case, **kwargs):
        """High-level: search for a tool matching the use case and execute it."""
        # Use Composio's search to find the right tool
        composio = self.servers.get("composio")
        if not composio:
            return {"error": "No Composio MCP server configured"}

        # Search for tools
        search_result = await self._call_server("composio", "tools/call", {
            "name": "COMPOSIO_SEARCH_TOOLS",
            "arguments": {
                "queries": [{"use_case": use_case, "known_fields": str(kwargs)}],
                "session": {"generate_id": True},
            },
        })

        return search_result

    def get_composio_gmail(self):
        """Shortcut: get Gmail tools via Composio."""
        return "composio"

    def get_composio_github(self):
        """Shortcut: get GitHub tools via Composio."""
        return "composio"

    def get_composio_slack(self):
        """Shortcut: get Slack tools via Composio."""
        return "composio"


# Built-in tool integrations (no MCP needed)
class BuiltInTools:
    """Tools that connect to services directly via API."""

    def __init__(self, config):
        self.config = config
        self.searxng_url = config.get("tools", "searxng_url")

    async def search(self, query, categories="general", limit=5):
        """Web search via SearXNG."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.searxng_url}/search", params={
                "q": query, "format": "json", "categories": categories
            })
            data = resp.json()
            return data.get("results", [])[:limit]

    async def send_email(self, to, subject, body):
        """Send email via Composio MCP."""
        mcp = MCPClient(self.config)
        return await mcp.call_tool("composio", "COMPOSIO_MULTI_EXECUTE_TOOL", {
            "tools": [{"tool_slug": "GMAIL_SEND_EMAIL", "arguments": {"to": to, "subject": subject, "body": body}}],
            "sync_response_to_workbench": False,
        })

    async def github_api(self, endpoint, method="GET", data=None):
        """Call GitHub API directly."""
        token = self.config.data.get("github", {}).get("token", "")
        if not token:
            return {"error": "No GitHub token configured"}

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            url = f"https://api.github.com{endpoint}"
            if method == "GET":
                resp = await client.get(url, headers=headers)
            elif method == "POST":
                resp = await client.post(url, headers=headers, json=data)
            elif method == "PATCH":
                resp = await client.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                resp = await client.delete(url, headers=headers)
            else:
                return {"error": f"Unsupported method: {method}"}

            return resp.json()

    async def weather(self, location):
        """Get weather via wttr.in."""
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://wttr.in/{location}?format=j1")
            if resp.status_code == 200:
                data = resp.json()
                current = data.get("current_condition", [{}])[0]
                return {
                    "location": location,
                    "temp": f"{current.get('temp_F')}°F / {current.get('temp_C')}°C",
                    "condition": current.get("weatherDesc", [{}])[0].get("value", "?"),
                    "humidity": f"{current.get('humidity')}%",
                    "wind": f"{current.get('windspeedMiles')} mph",
                }
            return {"error": f"Weather lookup failed for {location}"}
