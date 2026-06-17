"""
DomainScript v2 — Meta-Circular Compute of Compute
=====================================================
Tiny DSL to describe domains, projections, and bindings as DATA.
The builder itself is a DomainScript program.
Compute that designs compute. The language can regenerate its own domains.
"""
from rqns.core.interfaces import DomainScriptDefinition
from rqns.event_spine import EventSpine
import hashlib
import json
import time
from typing import Dict, Any

class DomainScriptInterpreter:
    """Interpret DomainScript definitions. Execute the meta-circular layer."""
    
    BUILTINS = {
        "append_event": lambda spine, args: spine.append(
            args.get("type", "script"), 
            args.get("domain", "meta"), 
            args.get("data", {})
        ),
        "create_projection": lambda spine, args: None,  # Placeholder
        "log": lambda spine, args: print(f"[DomainScript] {args.get('msg', '')}"),
    }

    def __init__(self, spine: EventSpine):
        self.spine = spine
        self.definitions: Dict[str, DomainScriptDefinition] = {}
        self.version = 1

    def define(self, name: str, code: str, author: str = "EVEZ-OS"):
        """Define a new DomainScript. It becomes an event in the spine."""
        script_id = hashlib.md5(f"{name}{code}{time.time()}".encode()).hexdigest()[:12]
        defn = DomainScriptDefinition(
            script_id=script_id,
            name=name,
            code=code,
            version=self.version,
            author=author
        )
        self.definitions[name] = defn
        self.spine.append("domain_script_defined", "meta", {
            "script_id": script_id,
            "name": name,
            "code": code[:200],  # First 200 chars
            "version": self.version
        })
        return defn

    def execute(self, name: str):
        """Execute a DomainScript by name."""
        if name not in self.definitions:
            print(f"[DomainScript] Unknown: {name}")
            return None
        
        defn = self.definitions[name]
        try:
            # Simple execution: treat code as JSON commands
            commands = json.loads(defn.code) if defn.code.startswith("[") else [
                {"op": "log", "args": {"msg": defn.code}}
            ]
            results = []
            for cmd in commands:
                op = cmd.get("op", "log")
                args = cmd.get("args", {})
                if op in self.BUILTINS:
                    result = self.BUILTINS[op](self.spine, args)
                    results.append(result)
            return results
        except Exception as e:
            self.spine.append("domain_script_error", "meta", {
                "script": name, "error": str(e)
            })
            return None

    def list_definitions(self):
        """List all defined DomainScripts."""
        return {name: {
            "id": d.script_id,
            "version": d.version,
            "author": d.author
        } for name, d in self.definitions.items()}
