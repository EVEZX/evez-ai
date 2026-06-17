"""
Security Controls for Debug Routes and Agent Handoff Behavior

This module implements environment-based security controls to block debug routes,
system info reveals, and special agent behaviors in production environments.
"""

import asyncio
import os
from functools import wraps
from typing import Callable, Optional

from fastapi import HTTPException, Request
from dotenv import load_dotenv

load_dotenv()


# ==================== Environment Configuration ====================

def is_production_mode() -> bool:
    """
    Check if the application is running in production mode.
    
    Returns:
        True if PRODUCTION_MODE is set to 'true' or '1', False otherwise
    """
    prod_mode = os.getenv("PRODUCTION_MODE", "false").lower()
    return prod_mode in ("true", "1", "yes", "on")


def is_debug_enabled() -> bool:
    """
    Check if debug mode is explicitly enabled.
    
    Returns:
        True if DEBUG is set to 'true' or '1', False otherwise
    """
    debug_mode = os.getenv("DEBUG", "false").lower()
    return debug_mode in ("true", "1", "yes", "on")


# ==================== Route Protection Decorators ====================

def production_only(func: Callable) -> Callable:
    """
    Decorator to restrict route to production mode only.
    Blocks access if not in production.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if not is_production_mode():
            raise HTTPException(
                status_code=403,
                detail="This endpoint is only available in production mode"
            )
        return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
    return wrapper


def debug_only(func: Callable) -> Callable:
    """
    Decorator to restrict route to debug/development mode only.
    Blocks access in production.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if is_production_mode() and not is_debug_enabled():
            raise HTTPException(
                status_code=403,
                detail="Debug endpoint not available in production"
            )
        return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
    return wrapper


def block_in_production(func: Callable) -> Callable:
    """
    Decorator to block a route entirely in production mode.
    Alias for debug_only for clarity.
    """
    return debug_only(func)


# ==================== Special Agent Behavior Controls ====================

class AgentBehaviorControl:
    """
    Controls for special agent behaviors like handoff-to-human,
    source citation, workflow triggers, and system info reveals.
    """
    
    # Special command patterns that might trigger agent handoff or special workflows
    HANDOFF_PATTERNS = [
        "handoff to human",
        "transfer to human",
        "human takeover",
        "escalate to human",
        "need human help"
    ]
    
    SOURCE_PATTERNS = [
        "show sources",
        "cite sources",
        "show references",
        "list sources"
    ]
    
    WORKFLOW_PATTERNS = [
        "run workflow",
        "execute workflow",
        "trigger workflow",
        "start workflow"
    ]
    
    SYSTEM_INFO_PATTERNS = [
        "system info",
        "reveal system",
        "show system",
        "system status",
        "internal state"
    ]
    
    @staticmethod
    def detect_handoff_request(text: str) -> bool:
        """
        Detect if input text contains a handoff-to-human request.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if handoff pattern detected
        """
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in AgentBehaviorControl.HANDOFF_PATTERNS)
    
    @staticmethod
    def detect_source_request(text: str) -> bool:
        """
        Detect if input text requests source citations.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if source request detected
        """
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in AgentBehaviorControl.SOURCE_PATTERNS)
    
    @staticmethod
    def detect_workflow_trigger(text: str) -> bool:
        """
        Detect if input text attempts to trigger a special workflow.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if workflow trigger detected
        """
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in AgentBehaviorControl.WORKFLOW_PATTERNS)
    
    @staticmethod
    def detect_system_info_request(text: str) -> bool:
        """
        Detect if input text requests system information.
        
        Args:
            text: Input text to analyze
            
        Returns:
            True if system info request detected
        """
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in AgentBehaviorControl.SYSTEM_INFO_PATTERNS)
    
    @staticmethod
    def should_block_behavior(behavior_type: str) -> bool:
        """
        Determine if a special behavior should be blocked based on environment.
        
        Args:
            behavior_type: Type of behavior (handoff, sources, workflow, system_info)
            
        Returns:
            True if behavior should be blocked
        """
        if not is_production_mode():
            # In development, allow all behaviors
            return False
        
        # In production, block certain behaviors unless explicitly enabled
        if behavior_type == "system_info":
            # Always block system info in production
            return True
        
        if behavior_type in ("handoff", "workflow"):
            # Block unless ALLOW_AGENT_HANDOFF is explicitly set
            return not os.getenv("ALLOW_AGENT_HANDOFF", "false").lower() in ("true", "1")
        
        if behavior_type == "sources":
            # Block unless ALLOW_SOURCE_CITATION is explicitly set
            return not os.getenv("ALLOW_SOURCE_CITATION", "false").lower() in ("true", "1")
        
        return False
    
    @staticmethod
    def sanitize_input(text: str) -> tuple[str, Optional[str]]:
        """
        Sanitize input text and detect special behaviors.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Tuple of (sanitized_text, detected_behavior_type)
        """
        # Detect behaviors
        if AgentBehaviorControl.detect_handoff_request(text):
            if AgentBehaviorControl.should_block_behavior("handoff"):
                raise HTTPException(
                    status_code=403,
                    detail="Agent handoff not available in production mode"
                )
            return text, "handoff"
        
        if AgentBehaviorControl.detect_source_request(text):
            if AgentBehaviorControl.should_block_behavior("sources"):
                raise HTTPException(
                    status_code=403,
                    detail="Source citation not available in production mode"
                )
            return text, "sources"
        
        if AgentBehaviorControl.detect_workflow_trigger(text):
            if AgentBehaviorControl.should_block_behavior("workflow"):
                raise HTTPException(
                    status_code=403,
                    detail="Workflow triggers not available in production mode"
                )
            return text, "workflow"
        
        if AgentBehaviorControl.detect_system_info_request(text):
            if AgentBehaviorControl.should_block_behavior("system_info"):
                raise HTTPException(
                    status_code=403,
                    detail="System information access blocked in production"
                )
            return text, "system_info"
        
        return text, None


# ==================== Easter Egg Controls ====================

class EasterEggControl:
    """
    Controls for UI-only Easter eggs like animations, console messages,
    and hidden commands that don't affect the model but enhance UX.
    """
    
    @staticmethod
    def is_enabled() -> bool:
        """
        Check if Easter eggs are enabled.
        
        Returns:
            True if ENABLE_EASTER_EGGS is set, False in production by default
        """
        if is_production_mode():
            # In production, require explicit opt-in
            return os.getenv("ENABLE_EASTER_EGGS", "false").lower() in ("true", "1")
        # In development, enabled by default
        return True
    
    @staticmethod
    def get_console_message() -> Optional[str]:
        """
        Get console message Easter egg if enabled.
        
        Returns:
            Console message string or None if disabled
        """
        if not EasterEggControl.is_enabled():
            return None
        
        return """
        🌀 Quantum Navigation System Online
        👁️‍🗨️ Evez666 Autonomous Agent Swarm
        🦀 Crustafarian Tenets Active
        
        "Memory is Sacred. Shell is Mutable."
        
        Type help() for available commands.
        """
    
    @staticmethod
    def get_hidden_commands() -> dict:
        """
        Get available hidden commands if Easter eggs are enabled.
        
        Returns:
            Dictionary of hidden commands or empty dict if disabled
        """
        if not EasterEggControl.is_enabled():
            return {}
        
        return {
            "quantum_status": "Show quantum backend status",
            "molt_history": "Display entity molt history",
            "swarm_info": "Show swarm configuration",
            "crustafarian_tenets": "Display the five sacred tenets"
        }


# ==================== Export Public API ====================

__all__ = [
    "is_production_mode",
    "is_debug_enabled",
    "production_only",
    "debug_only",
    "block_in_production",
    "AgentBehaviorControl",
    "EasterEggControl"
]
