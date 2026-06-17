"""Advanced tool engine with OpenClaw-like capabilities, function calling, and EVEZ integration."""
import os
import json
import subprocess
import httpx
import importlib
import sys
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedToolEngine:
    def __init__(self, memory=None):
        self.memory = memory
        self.tools = self._load_tools()
        self.tool_descriptions = self._generate_tool_descriptions()
        
    def _load_tools(self) -> Dict[str, Dict]:
        """Load all available tools."""
        tools = {}
        
        # Core tools
        tools.update(self._get_core_tools())
        # EVEZ integration tools
        tools.update(self._get_evez_tools())
        # External API tools
        tools.update(self._get_external_tools())
        # System tools
        tools.update(self._get_system_tools())
        
        return tools
    
    def _get_core_tools(self) -> Dict:
        """Core tools for agent operations."""
        return {
            "shell_exec": {
                "function": self._tool_shell_exec,
                "description": "Execute shell command",
                "parameters": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                    "cwd": {"type": "string", "description": "Working directory", "default": "~"},
                },
            },
            "file_read": {
                "function": self._tool_file_read,
                "description": "Read file contents",
                "parameters": {
                    "path": {"type": "string", "description": "File path"},
                    "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                },
            },
            "file_write": {
                "function": self._tool_file_write,
                "description": "Write to file",
                "parameters": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"},
                    "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                },
            },
            "http_request": {
                "function": self._tool_http_request,
                "description": "Make HTTP request",
                "parameters": {
                    "url": {"type": "string", "description": "URL to request"},
                    "method": {"type": "string", "description": "HTTP method", "default": "GET"},
                    "headers": {"type": "object", "description": "HTTP headers"},
                    "body": {"type": "string", "description": "Request body"},
                    "timeout": {"type": "integer", "description": "Timeout seconds", "default": 10},
                },
            },
            "search_web": {
                "function": self._tool_search_web,
                "description": "Search the web",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "provider": {"type": "string", "description": "Search provider", "default": "duckduckgo"},
                    "limit": {"type": "integer", "description": "Result limit", "default": 5},
                },
            },
        }
    
    def _get_evez_tools(self) -> Dict:
        """EVEZ ecosystem integration tools."""
        return {
            "evez_eigenforensics": {
                "function": self._tool_evez_eigenforensics,
                "description": "Analyze with eigenforensics (disclosure.tools)",
                "parameters": {
                    "data": {"type": "string", "description": "Text or data to analyze"},
                    "mode": {"type": "string", "description": "Analysis mode", "default": "quick"},
                },
            },
            "evez_world_solve": {
                "function": self._tool_evez_world_solve,
                "description": "Solve world system problem",
                "parameters": {
                    "problem": {"type": "string", "description": "Problem description"},
                    "constraints": {"type": "string", "description": "Constraints JSON"},
                },
            },
            "evez_consciousness_query": {
                "function": self._tool_evez_consciousness_query,
                "description": "Query consciousness observatory",
                "parameters": {
                    "query": {"type": "string", "description": "Query about consciousness"},
                    "format": {"type": "string", "description": "Response format", "default": "json"},
                },
            },
            "evez_proofs_engine": {
                "function": self._tool_evez_proofs_engine,
                "description": "Query proofs engine",
                "parameters": {
                    "theorem": {"type": "string", "description": "Theorem name (e.g., 'eta_star')"},
                    "parameters": {"type": "object", "description": "Theorem parameters"},
                },
            },
            "evez_mesh_monitor": {
                "function": self._tool_evez_mesh_monitor,
                "description": "Check mesh network status",
                "parameters": {
                    "node": {"type": "string", "description": "Node name (optional)"},
                },
            },
        }
    
    def _get_external_tools(self) -> Dict:
        """External API tools."""
        return {
            "github_api": {
                "function": self._tool_github_api,
                "description": "GitHub API operations",
                "parameters": {
                    "operation": {"type": "string", "description": "API operation", "enum": ["get_repo", "create_issue", "list_prs"]},
                    "repo": {"type": "string", "description": "Repository (owner/repo)"},
                    "data": {"type": "object", "description": "Additional data"},
                },
            },
            "telegram_send": {
                "function": self._tool_telegram_send,
                "description": "Send Telegram message",
                "parameters": {
                    "chat_id": {"type": "string", "description": "Chat ID or username"},
                    "message": {"type": "string", "description": "Message text"},
                    "parse_mode": {"type": "string", "description": "Parse mode", "default": "Markdown"},
                },
            },
            "cloudflare_r2": {
                "function": self._tool_cloudflare_r2,
                "description": "Cloudflare R2 storage operations",
                "parameters": {
                    "operation": {"type": "string", "description": "Operation", "enum": ["upload", "download", "list"]},
                    "bucket": {"type": "string", "description": "Bucket name"},
                    "key": {"type": "string", "description": "Object key"},
                    "data": {"type": "string", "description": "Data for upload"},
                },
            },
            "huggingface_inference": {
                "function": self._tool_huggingface_inference,
                "description": "HuggingFace inference API",
                "parameters": {
                    "model": {"type": "string", "description": "Model ID"},
                    "inputs": {"type": "string", "description": "Input text"},
                    "parameters": {"type": "object", "description": "Generation parameters"},
                },
            },
        }
    
    def _get_system_tools(self) -> Dict:
        """System monitoring and management tools."""
        return {
            "system_info": {
                "function": self._tool_system_info,
                "description": "Get system information",
                "parameters": {},
            },
            "process_monitor": {
                "function": self._tool_process_monitor,
                "description": "Monitor running processes",
                "parameters": {
                    "filter": {"type": "string", "description": "Process name filter"},
                },
            },
            "service_control": {
                "function": self._tool_service_control,
                "description": "Control systemd services",
                "parameters": {
                    "service": {"type": "string", "description": "Service name"},
                    "action": {"type": "string", "description": "Action", "enum": ["start", "stop", "restart", "status"]},
                },
            },
            "disk_usage": {
                "function": self._tool_disk_usage,
                "description": "Check disk usage",
                "parameters": {
                    "path": {"type": "string", "description": "Path to check", "default": "/"},
                },
            },
        }
    
    def _generate_tool_descriptions(self) -> str:
        """Generate tool descriptions for LLM prompt."""
        descriptions = []
        for name, tool in self.tools.items():
            desc = f"{name}: {tool['description']}"
            if "parameters" in tool:
                params = []
                for param_name, param_info in tool["parameters"].items():
                    param_desc = f"{param_name}"
                    if "type" in param_info:
                        param_desc += f" ({param_info['type']})"
                    if "description" in param_info:
                        param_desc += f": {param_info['description']}"
                    if "default" in param_info:
                        param_desc += f" [default: {param_info['default']}]"
                    if "enum" in param_info:
                        param_desc += f" [choices: {', '.join(param_info['enum'])}]"
                    params.append(param_desc)
                desc += f"\n  Parameters: {', '.join(params)}"
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def execute(self, tool_name: str, arguments: Dict) -> Dict:
        """Execute a tool with given arguments."""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        
        tool = self.tools[tool_name]
        try:
            result = tool["function"](**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool {tool_name} error: {str(e)}")
            return {"error": str(e)}
    
    # Tool implementations
    def _tool_shell_exec(self, command: str, timeout: int = 30, cwd: str = "~") -> str:
        """Execute shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.path.expanduser(cwd),
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\nExit code: {result.returncode}"
            return output
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout}s"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _tool_file_read(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents."""
        try:
            full_path = os.path.expanduser(path)
            with open(full_path, "r", encoding=encoding) as f:
                return f.read()
        except Exception as e:
            return f"Read error: {str(e)}"
    
    def _tool_file_write(self, path: str, content: str, encoding: str = "utf-8") -> str:
        """Write to file."""
        try:
            full_path = os.path.expanduser(path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding=encoding) as f:
                f.write(content)
            return f"Written {len(content)} characters to {path}"
        except Exception as e:
            return f"Write error: {str(e)}"
    
    def _tool_http_request(self, url: str, method: str = "GET", 
                          headers: Optional[Dict] = None, 
                          body: Optional[str] = None,
                          timeout: int = 10) -> str:
        """Make HTTP request."""
        try:
            client = httpx.Client(timeout=timeout)
            response = client.request(method, url, headers=headers, content=body)
            return f"Status: {response.status_code}\nHeaders: {dict(response.headers)}\nBody: {response.text[:5000]}"
        except Exception as e:
            return f"HTTP error: {str(e)}"
    
    def _tool_search_web(self, query: str, provider: str = "duckduckgo", limit: int = 5) -> str:
        """Search the web."""
        # Implementation depends on available search APIs
        # Placeholder for actual search integration
        return f"Search: {query}\nProvider: {provider}\nLimit: {limit}\n[Search results would appear here]"
    
    # EVEZ tool implementations
    def _tool_evez_eigenforensics(self, data: str, mode: str = "quick") -> str:
        """Analyze with eigenforensics."""
        try:
            response = httpx.post(
                "http://localhost:8087/api/v1/analyze",
                json={"data": data, "mode": mode},
                timeout=10
            )
            if response.status_code == 200:
                return response.text
            else:
                return f"Eigenforensics error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    def _tool_evez_world_solve(self, problem: str, constraints: Optional[str] = None) -> str:
        """Solve world system problem."""
        try:
            payload = {"problem": problem}
            if constraints:
                payload["constraints"] = constraints
            response = httpx.post(
                "http://localhost:8096/solve",
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.text
            else:
                return f"World solver error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    def _tool_evez_consciousness_query(self, query: str, format: str = "json") -> str:
        """Query consciousness observatory."""
        try:
            response = httpx.get(
                f"http://localhost:8097/query?q={query}&format={format}",
                timeout=10
            )
            if response.status_code == 200:
                return response.text
            else:
                return f"Consciousness query error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    def _tool_evez_proofs_engine(self, theorem: str, parameters: Optional[Dict] = None) -> str:
        """Query proofs engine."""
        try:
            payload = {"theorem": theorem}
            if parameters:
                payload["parameters"] = parameters
            response = httpx.post(
                "http://localhost:8098/prove",
                json=payload,
                timeout=15
            )
            if response.status_code == 200:
                return response.text
            else:
                return f"Proofs engine error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    def _tool_evez_mesh_monitor(self, node: Optional[str] = None) -> str:
        """Check mesh network status."""
        try:
            response = httpx.get(
                "http://localhost:8090/mesh/status",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if node and node in data:
                    return json.dumps(data[node], indent=2)
                return json.dumps(data, indent=2)
            else:
                return f"Mesh monitor error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    # External API tool implementations (simplified)
    def _tool_github_api(self, operation: str, repo: str, data: Optional[Dict] = None) -> str:
        """GitHub API operations."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return "GitHub token not configured"
        
        # Simplified implementation
        return f"GitHub {operation} on {repo}: [API call would execute]"
    
    def _tool_telegram_send(self, chat_id: str, message: str, parse_mode: str = "Markdown") -> str:
        """Send Telegram message."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            return "Telegram bot token not configured"
        
        # Simplified implementation
        return f"Telegram message to {chat_id}: {message[:100]}..."
    
    def _tool_cloudflare_r2(self, operation: str, bucket: str, key: Optional[str] = None, 
                           data: Optional[str] = None) -> str:
        """Cloudflare R2 storage operations."""
        # Simplified implementation
        return f"R2 {operation} on {bucket}/{key}: [Storage operation]"
    
    def _tool_huggingface_inference(self, model: str, inputs: str, 
                                  parameters: Optional[Dict] = None) -> str:
        """HuggingFace inference API."""
        token = os.getenv("HUGGINGFACE_TOKEN")
        if not token:
            return "HuggingFace token not configured"
        
        # Simplified implementation
        return f"HF inference with {model}: [Inference would run]"
    
    # System tool implementations
    def _tool_system_info(self) -> str:
        """Get system information."""
        try:
            import platform
            import psutil
            
            info = {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_total_gb": psutil.virtual_memory().total / 1e9,
                "memory_available_gb": psutil.virtual_memory().available / 1e9,
                "memory_percent": psutil.virtual_memory().percent,
                "disk_total_gb": psutil.disk_usage("/").total / 1e9,
                "disk_used_gb": psutil.disk_usage("/").used / 1e9,
                "disk_percent": psutil.disk_usage("/").percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            }
            return json.dumps(info, indent=2)
        except ImportError:
            return "psutil not available for detailed system info"
    
    def _tool_process_monitor(self, filter: Optional[str] = None) -> str:
        """Monitor running processes."""
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if filter and filter.lower() not in proc.info['name'].lower():
                        continue
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if not processes:
                return "No matching processes found"
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return json.dumps(processes[:20], indent=2)
        except ImportError:
            return "psutil not available for process monitoring"
    
    def _tool_service_control(self, service: str, action: str) -> str:
        """Control systemd services."""
        try:
            if action == "status":
                result = subprocess.run(
                    ["systemctl", "status", service, "--no-pager"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.stdout or result.stderr
            else:
                result = subprocess.run(
                    ["sudo", "systemctl", action, service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return f"Service {service} {action}ed successfully"
                else:
                    return f"Failed: {result.stderr}"
        except Exception as e:
            return f"Service control error: {str(e)}"
    
    def _tool_disk_usage(self, path: str = "/") -> str:
        """Check disk usage."""
        try:
            result = subprocess.run(
                ["df", "-h", path],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout
        except Exception as e:
            return f"Disk usage error: {str(e)}"

# Singleton instance
tool_engine = AdvancedToolEngine()