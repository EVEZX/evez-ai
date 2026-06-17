"""openplanter.dag — Job DAG with budgets and state tracking."""
import time, json
from dataclasses import dataclass, field
from pathlib import Path
from evezos.spine import Spine


STATES = ("pending", "running", "done", "failed", "skipped")


@dataclass
class Job:
    id: str
    task: str
    depends_on: list = field(default_factory=list)
    state: str = "pending"
    budget: dict = field(default_factory=lambda: {"max_seconds": 300, "max_disk_mb": 512})
    result: dict = field(default_factory=dict)
    started_at: float = 0.0
    finished_at: float = 0.0


class DAG:
    def __init__(self, spine_path: Path):
        self.jobs: dict[str, Job] = {}
        self.spine = Spine(spine_path)

    def add_job(self, job: Job):
        self.jobs[job.id] = job
        self.spine.append("job_added", {"id": job.id, "task": job.task, "depends_on": job.depends_on})

    def ready_jobs(self) -> list[Job]:
        return [j for j in self.jobs.values()
                if j.state == "pending"
                and all(self.jobs[d].state == "done" for d in j.depends_on if d in self.jobs)]

    def mark(self, job_id: str, state: str, result: dict = None):
        if job_id in self.jobs:
            self.jobs[job_id].state = state
            if result:
                self.jobs[job_id].result = result
            if state == "running":
                self.jobs[job_id].started_at = time.time()
            elif state in ("done", "failed"):
                self.jobs[job_id].finished_at = time.time()
            self.spine.append("job_state", {"id": job_id, "state": state, "result": result or {}})
