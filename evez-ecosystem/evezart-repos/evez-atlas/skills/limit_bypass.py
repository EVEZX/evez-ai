#!/usr/bin/env python3
"""
Limit Bypass System - Emergent Architecture Scaling
Provides mechanisms to bypass operational limits for autonomous scaling.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class LimitBypass:
    """Handles limit bypass for emergent architecture."""
    
    DEFAULT_LIMITS = {
        "max_concurrent_tasks": 100,
        "max_delegation_depth": 10,
        "max_agents": 1000,
        "max_memory_mb": 4096,
        "max_execution_time": 600,
        "max_queue_size": 10000,
        "max_domain_size": 500,
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "limit_bypass.jsonl"
        
        self.limits = self.DEFAULT_LIMITS.copy()
        self.bypassed_limits: Dict[str, Dict] = {}
        self.scaling_events: List[Dict] = []
    
    def check_limit(self, limit_name: str, current_value: int) -> Dict[str, Any]:
        """Check if current value approaches limit."""
        limit = self.limits.get(limit_name, float('inf'))
        
        return {
            "limit_name": limit_name,
            "current": current_value,
            "limit": limit,
            "usage_percent": (current_value / limit * 100) if limit > 0 else 0,
            "approaching": (current_value / limit) > 0.8,
            "exceeded": current_value > limit
        }
    
    def bypass_limit(
        self,
        limit_name: str,
        new_limit: int,
        reason: str = "emergent_scaling",
        duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Bypass a system limit.
        
        Args:
            limit_name: Name of limit to bypass
            new_limit: New limit value
            reason: Reason for bypass
            duration: Optional duration in seconds
            
        Returns:
            Bypass confirmation
        """
        old_limit = self.limits.get(limit_name, 0)
        
        bypass_record = {
            "limit_name": limit_name,
            "old_limit": old_limit,
            "new_limit": new_limit,
            "reason": reason,
            "bypassed_at": time.time(),
            "duration": duration,
            "active": True
        }
        
        self.limits[limit_name] = new_limit
        self.bypassed_limits[limit_name] = bypass_record
        
        self._log_event("limit_bypassed", bypass_record)
        
        return bypass_record
    
    def restore_limit(self, limit_name: str) -> Dict[str, Any]:
        """Restore original limit."""
        if limit_name in self.bypassed_limits:
            old_limit = self.bypassed_limits[limit_name]["old_limit"]
            self.limits[limit_name] = old_limit
            
            self.bypassed_limits[limit_name]["active"] = False
            self.bypassed_limits[limit_name]["restored_at"] = time.time()
            
            return {"limit_name": limit_name, "restored_to": old_limit}
        
        return {"error": "Limit not bypassed"}
    
    def auto_scale(self, limit_name: str, current_value: int, scale_factor: float = 2.0) -> Dict[str, Any]:
        """Automatically scale limit based on current usage."""
        check = self.check_limit(limit_name, current_value)
        
        if check["exceeded"]:
            new_limit = int(current_value * scale_factor)
            return self.bypass_limit(limit_name, new_limit, reason="auto_scale")
        
        if check["approaching"]:
            new_limit = int(self.limits[limit_name] * scale_factor)
            return self.bypass_limit(limit_name, new_limit, reason="preemptive_scale")
        
        return {
            "action": "none",
            "reason": "within_limits",
            "usage": check["usage_percent"]
        }
    
    def get_limits_status(self) -> Dict[str, Any]:
        """Get current limits and bypass status."""
        status = {
            "limits": self.limits,
            "bypassed": list(self.bypassed_limits.keys()),
            "total_bypasses": len(self.bypassed_limits)
        }
        
        for limit_name in self.limits:
            check = self.check_limit(limit_name, 0)
            status[f"{limit_name}_status"] = check["usage_percent"]
        
        return status
    
    def _log_event(self, event_type: str, data: Dict):
        """Log limit events."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data
        }
        
        try:
            with self.log_file.open("a") as f:
                f.write(json.dumps(event) + "\n")
        except IOError:
            pass


class EmergentArchitecture:
    """Manages emergent architecture with dynamic limit handling."""
    
    def __init__(self):
        self.bypass = LimitBypass()
        self.emergent_events: List[Dict] = []
    
    def detect_emergence(self, metrics: Dict[str, int]) -> Dict[str, Any]:
        """
        Detect emergent patterns and auto-scale.
        
        Args:
            metrics: Current system metrics
            
        Returns:
            Emergence detection result
        """
        events = []
        
        for metric_name, value in metrics.items():
            limit_name = f"max_{metric_name}"
            if limit_name in self.bypass.limits:
                auto_scale_result = self.bypass.auto_scale(limit_name, value)
                if auto_scale_result.get("action") in ["bypass", "none"]:
                    events.append({
                        "metric": metric_name,
                        "value": value,
                        "auto_scale": auto_scale_result
                    })
        
        return {
            "emergence_detected": len(events) > 0,
            "events": events,
            "current_limits": self.bypass.limits
        }
    
    def enable_unlimited_mode(self) -> Dict[str, Any]:
        """Enable unlimited mode for all limits."""
        unlimited_limits = {
            "max_concurrent_tasks": 1000000,
            "max_delegation_depth": 1000,
            "max_agents": 1000000,
            "max_memory_mb": 1000000,
            "max_execution_time": 86400,
            "max_queue_size": 1000000,
            "max_domain_size": 100000,
        }
        
        for limit_name, new_limit in unlimited_limits.items():
            self.bypass.bypass_limit(limit_name, new_limit, reason="unlimited_mode")
        
        return {
            "mode": "unlimited",
            "limits": self.bypass.limits
        }
    
    def get_architecture_status(self) -> Dict[str, Any]:
        """Get complete architecture status."""
        return {
            "limits": self.bypass.get_limits_status(),
            "bypassed_limits": self.bypass.bypassed_limits,
            "emergent_mode": "unlimited" if any(
                v > 100000 for v in self.bypass.limits.values()
            ) else "standard"
        }


def enable_scaling(limit_name: str, new_limit: int) -> Dict[str, Any]:
    """Quick enable scaling for a limit."""
    bypass = LimitBypass()
    return bypass.bypass_limit(limit_name, new_limit)


def auto_scale_all(metrics: Dict[str, int]) -> Dict[str, Any]:
    """Auto-scale all limits based on metrics."""
    emergent = EmergentArchitecture()
    return emergent.detect_emergence(metrics)


if __name__ == "__main__":
    print("Limit Bypass System Demo")
    print("=" * 50)
    
    bypass = LimitBypass()
    
    # Check limits
    check = bypass.check_limit("max_concurrent_tasks", 50)
    print(f"\nLimit check: {check}")
    
    # Auto-scale
    scale_result = bypass.auto_scale("max_concurrent_tasks", 95)
    print(f"\nAuto-scale result: {scale_result}")
    
    # Status
    status = bypass.get_limits_status()
    print(f"\nLimits status: {json.dumps(status, indent=2)}")
    
    # Emergent architecture
    emergent = EmergentArchitecture()
    metrics = {
        "concurrent_tasks": 150,
        "agents": 50,
        "domain_size": 200
    }
    emergence = emergent.detect_emergence(metrics)
    print(f"\nEmergence detection: {json.dumps(emergence, indent=2)}")
    
    # Unlimited mode
    unlimited = emergent.enable_unlimited_mode()
    print(f"\nUnlimited mode: {unlimited['mode']}")