#!/usr/bin/env python3
"""
Parallel Build Deployment System
Executes multiple build tasks concurrently using parallel path exploration.
"""

import asyncio
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class BuildStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class BuildTask:
    """Represents a single build task."""
    id: str
    command: str
    cwd: str = "."
    timeout: int = 300
    env: Dict[str, str] = field(default_factory=dict)
    priority: int = 0
    status: BuildStatus = BuildStatus.PENDING
    output: str = ""
    exit_code: Optional[int] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "cwd": self.cwd,
            "timeout": self.timeout,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration": self.end_time - self.start_time if self.start_time and self.end_time else None
        }


class ParallelBuildExecutor:
    """Executes build tasks in parallel with path optimization."""
    
    def __init__(self, max_workers: int = 4, data_dir: str = "data"):
        self.max_workers = max_workers
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.log_file = self.data_dir / "build_deployment.jsonl"
        
        self.tasks: Dict[str, BuildTask] = {}
        self.results: List[Dict[str, Any]] = []
        self.executor = None
    
    def add_task(self, task_id: str, command: str, cwd: str = ".", 
                 timeout: int = 300, priority: int = 0, env: Dict = None) -> BuildTask:
        """Add a build task to the queue."""
        task = BuildTask(
            id=task_id,
            command=command,
            cwd=cwd,
            timeout=timeout,
            priority=priority,
            env=env or {}
        )
        self.tasks[task_id] = task
        return task
    
    def _execute_task(self, task: BuildTask) -> Dict[str, Any]:
        """Execute a single build task."""
        task.status = BuildStatus.RUNNING
        task.start_time = time.time()
        
        # Merge environment
        full_env = os.environ.copy()
        full_env.update(task.env)
        
        try:
            result = subprocess.run(
                task.command,
                shell=True,
                cwd=task.cwd,
                capture_output=True,
                text=True,
                timeout=task.timeout,
                env=full_env
            )
            
            task.exit_code = result.returncode
            task.output = result.stdout + result.stderr
            
            if result.returncode == 0:
                task.status = BuildStatus.SUCCESS
            else:
                task.status = BuildStatus.FAILED
                
        except subprocess.TimeoutExpired:
            task.status = BuildStatus.TIMEOUT
            task.output = f"Task timed out after {task.timeout}s"
        except Exception as e:
            task.status = BuildStatus.FAILED
            task.output = str(e)
        
        task.end_time = time.time()
        
        return task.to_dict()
    
    def execute_parallel(self, task_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Execute tasks in parallel (up to max_workers)."""
        if task_ids is None:
            task_ids = list(self.tasks.keys())
        
        # Sort by priority
        sorted_tasks = sorted(
            [self.tasks[tid] for tid in task_ids if tid in self.tasks],
            key=lambda t: t.priority,
            reverse=True
        )
        
        self.results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._execute_task, task): task.id 
                for task in sorted_tasks
            }
            
            for future in as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                    self.results.append(result)
                    self._log_event("task_completed", result)
                except Exception as e:
                    error_result = {
                        "id": task_id,
                        "status": "error",
                        "error": str(e)
                    }
                    self.results.append(error_result)
        
        return self.results
    
    def execute_sequential(self, task_ids: List[str] = None) -> List[Dict[str, Any]]:
        """Execute tasks sequentially (for dependencies)."""
        if task_ids is None:
            task_ids = list(self.tasks.keys())
        
        sorted_tasks = sorted(
            [self.tasks[tid] for tid in task_ids if tid in self.tasks],
            key=lambda t: t.priority,
            reverse=True
        )
        
        self.results = []
        
        for task in sorted_tasks:
            result = self._execute_task(task)
            self.results.append(result)
            self._log_event("task_completed", result)
        
        return self.results
    
    def get_build_summary(self) -> Dict[str, Any]:
        """Get summary of build results."""
        if not self.results:
            return {"total": 0}
        
        status_counts = {}
        for r in self.results:
            status = r.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_duration = sum(
            r.get("duration", 0) for r in self.results 
            if r.get("duration") is not None
        )
        
        return {
            "total_tasks": len(self.results),
            "by_status": status_counts,
            "success_rate": status_counts.get("success", 0) / len(self.results) if self.results else 0,
            "total_duration": total_duration,
            "parallel_efficiency": total_duration / (len(self.results) * max(t.get("duration", 1) for t in self.results if t.get("duration"))) if self.results else 0
        }
    
    def _log_event(self, event_type: str, data: Dict):
        """Log build events."""
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


async def async_build_deploy(commands: List[Dict[str, Any]], max_parallel: int = 4) -> Dict[str, Any]:
    """Async version for use in async contexts."""
    executor = ParallelBuildExecutor(max_workers=max_parallel)
    
    for cmd in commands:
        executor.add_task(
            task_id=cmd.get("id", f"task-{len(executor.tasks)}"),
            command=cmd["command"],
            cwd=cmd.get("cwd", "."),
            timeout=cmd.get("timeout", 300),
            priority=cmd.get("priority", 0),
            env=cmd.get("env", {})
        )
    
    results = executor.execute_parallel()
    summary = executor.get_build_summary()
    
    return {
        "results": results,
        "summary": summary
    }


def run_parallel_builds(build_configs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Main entry point for parallel build deployment."""
    executor = ParallelBuildExecutor(max_workers=4)
    
    for config in build_configs:
        executor.add_task(
            task_id=config.get("id", f"build-{len(executor.tasks)}"),
            command=config["command"],
            cwd=config.get("cwd", "."),
            timeout=config.get("timeout", 300),
            priority=config.get("priority", 0),
            env=config.get("env", {})
        )
    
    results = executor.execute_parallel()
    summary = executor.get_build_summary()
    
    return {
        "results": results,
        "summary": summary,
        "parallel": True,
        "max_workers": executor.max_workers
    }


if __name__ == "__main__":
    # Demo: Run multiple build commands in parallel
    builds = [
        {"id": "lint", "command": "python -m pyflakes . || true", "priority": 1},
        {"id": "test", "command": "python -m pytest --collect-only 2>/dev/null || echo 'No tests'", "priority": 2},
        {"id": "deps-check", "command": "python -c 'import fastapi, pydantic, uvicorn; print(\"Deps OK\")'", "priority": 0},
    ]
    
    print("Running parallel build demo...")
    result = run_parallel_builds(builds)
    
    print("\nBuild Results:")
    for r in result["results"]:
        print(f"  {r['id']}: {r['status']}")
    
    print(f"\nSummary: {result['summary']}")