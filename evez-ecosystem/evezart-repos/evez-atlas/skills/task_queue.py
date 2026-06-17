#!/usr/bin/env python3
"""
Task Queue with Iterative Error Correction
Manages task pacing, gap filling, and error correction for swarm operations.
"""

import json
import os
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
import uuid


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    ERROR_CORRECTION = "error_correction"


@dataclass
class Task:
    """Represents a task in the queue."""
    id: str
    name: str
    data: Dict[str, Any]
    status: TaskStatus
    created_at: str
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    completed_at: Optional[str] = None
    temporal_gap: float = 0.0  # Seconds between attempts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary."""
        data['status'] = TaskStatus(data['status'])
        return cls(**data)


class TaskQueue:
    """
    Task queue with iterative error correction and gap filling.
    Implements temporal hibernation and task pacing.
    """
    
    def __init__(self, queue_file: str = 'data/task_queue.jsonl'):
        self.queue_file = queue_file
        self.tasks: Dict[str, Task] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self._load_queue()
    
    def _load_queue(self):
        """Load tasks from queue file."""
        if not os.path.exists(self.queue_file):
            return
        
        try:
            with open(self.queue_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        task = Task.from_dict(data)
                        self.tasks[task.id] = task
        except Exception as e:
            print(f"Error loading queue: {e}")
    
    def _save_task(self, task: Task):
        """Append task to queue file."""
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        
        with open(self.queue_file, 'a') as f:
            f.write(json.dumps(task.to_dict()) + '\n')
    
    def register_handler(self, task_name: str, handler: Callable):
        """Register a handler function for a task type."""
        self.task_handlers[task_name] = handler
    
    def enqueue(self, task_name: str, data: Dict[str, Any], max_attempts: int = 3) -> Task:
        """Add a task to the queue."""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=task_name,
            data=data,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow().isoformat(),
            max_attempts=max_attempts
        )
        self.tasks[task_id] = task
        self._save_task(task)
        return task
    
    def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a single task with error correction."""
        task = self.tasks.get(task_id)
        if not task:
            return {'status': 'error', 'message': 'Task not found'}
        
        handler = self.task_handlers.get(task.name)
        if not handler:
            task.status = TaskStatus.FAILED
            task.last_error = f"No handler for task: {task.name}"
            self._save_task(task)
            return {'status': 'error', 'message': task.last_error}
        
        # Update status to running
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        self._save_task(task)
        
        try:
            # Execute the task
            result = handler(task.data)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            self._save_task(task)
            
            return {
                'status': 'success',
                'task_id': task_id,
                'result': result,
                'attempts': task.attempts
            }
            
        except Exception as e:
            # Error correction mode
            task.last_error = str(e)
            
            if task.attempts >= task.max_attempts:
                # Max attempts reached
                task.status = TaskStatus.FAILED
                self._save_task(task)
                return {
                    'status': 'failed',
                    'task_id': task_id,
                    'error': str(e),
                    'attempts': task.attempts
                }
            else:
                # Enter error correction mode
                task.status = TaskStatus.ERROR_CORRECTION
                task.temporal_gap = min(task.attempts * 2.0, 10.0)  # Exponential backoff
                self._save_task(task)
                
                # Attempt iterative correction
                return self._iterative_correction(task)
    
    def _iterative_correction(self, task: Task) -> Dict[str, Any]:
        """
        Perform iterative error correction with temporal gap pacing.
        """
        # Wait for temporal gap (hibernation period)
        if task.temporal_gap > 0:
            time.sleep(min(task.temporal_gap, 1.0))  # Cap at 1 second for testing
        
        # Retry with correction
        task.status = TaskStatus.RETRYING
        self._save_task(task)
        
        # Recursive retry
        return self.execute_task(task.id)
    
    def process_queue(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Process pending tasks in the queue."""
        results = []
        pending_tasks = [
            t for t in self.tasks.values()
            if t.status in [TaskStatus.PENDING, TaskStatus.ERROR_CORRECTION]
        ]
        
        for task in pending_tasks[:batch_size]:
            result = self.execute_task(task.id)
            results.append(result)
        
        return results
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status."""
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_tasks': len(self.tasks),
            'by_status': status_counts,
            'avg_attempts': self._calculate_avg_attempts(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_avg_attempts(self) -> float:
        """Calculate average attempts per task."""
        if not self.tasks:
            return 0.0
        return sum(t.attempts for t in self.tasks.values()) / len(self.tasks)
    
    def get_failed_tasks(self) -> List[Task]:
        """Get all failed tasks for analysis."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
    
    def retry_failed_tasks(self) -> List[Dict[str, Any]]:
        """Retry all failed tasks."""
        results = []
        for task in self.get_failed_tasks():
            # Reset task for retry
            task.status = TaskStatus.PENDING
            task.attempts = 0
            task.last_error = None
            self._save_task(task)
            
            result = self.execute_task(task.id)
            results.append(result)
        
        return results


# Example task handlers
def example_forgiveness_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    """Example handler for forgiveness tasks."""
    from skills.jubilee import forgive
    return forgive(data)


def example_quantum_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    """Example handler for quantum simulation tasks."""
    from skills.jubilee import quantum_sim
    return quantum_sim(data)


if __name__ == '__main__':
    # Demo usage
    queue = TaskQueue()
    
    # Register handlers
    queue.register_handler('forgiveness', example_forgiveness_handler)
    queue.register_handler('quantum_sim', example_quantum_handler)
    
    # Enqueue some tasks
    task1 = queue.enqueue('forgiveness', {'account_id': 'TEST001'})
    task2 = queue.enqueue('quantum_sim', {'circuit': 'bell_state'})
    
    print("Queue status:")
    print(json.dumps(queue.get_queue_status(), indent=2))
