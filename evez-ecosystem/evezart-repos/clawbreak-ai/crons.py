"""ClawBreak Crons — built-in scheduled tasks."""
import time
import json
import asyncio
from pathlib import Path

class CronManager:
    """Manage scheduled tasks without external cron."""

    def __init__(self, config, memory, llm_client, mcp_client):
        self.config = config
        self.memory = memory
        self.llm = llm_client
        self.mcp = mcp_client
        self.jobs = config.data.get("crons", [])
        self._tasks = []
        self._last_run = {}  # job_name -> timestamp

    async def start_all(self):
        """Start all cron jobs."""
        for job in self.jobs:
            if job.get("enabled", True):
                self._tasks.append(asyncio.create_task(self._run_loop(job)))

    async def stop_all(self):
        """Stop all cron jobs."""
        for t in self._tasks:
            t.cancel()

    async def _run_loop(self, job):
        """Run a cron job on schedule."""
        name = job.get("name", "unnamed")
        interval = job.get("interval_seconds", 3600)
        prompt = job.get("prompt", "")

        while True:
            try:
                # Check if it's time to run
                last = self._last_run.get(name, 0)
                if time.time() - last >= interval:
                    self._last_run[name] = time.time()

                    # Execute the job
                    messages = [
                        {"role": "system", "content": self.config.get("system_prompt")},
                        {"role": "user", "content": f"[CRON: {name}] {prompt}"}
                    ]
                    result = await self.llm.chat(messages)

                    if "error" not in result:
                        try:
                            reply = result["choices"][0]["message"]["content"]
                            self.memory.store_fact(
                                f"cron_{name}_{int(time.time())}",
                                reply[:500],
                                category="cron"
                            )
                        except:
                            pass

            except asyncio.CancelledError:
                return
            except Exception as e:
                self.memory.store_fact(
                    f"cron_error_{name}_{int(time.time())}",
                    str(e)[:200],
                    category="cron_error"
                )

            # Sleep in small increments so we can cancel
            for _ in range(min(interval, 60)):
                await asyncio.sleep(1)

    def add_job(self, name, prompt, interval_seconds=3600, enabled=True):
        """Add a new cron job."""
        job = {"name": name, "prompt": prompt, "interval_seconds": interval_seconds, "enabled": enabled}
        self.jobs.append(job)
        self.config.data["crons"] = self.jobs
        self.config.save()
        self._tasks.append(asyncio.create_task(self._run_loop(job)))
        return {"status": "added", "name": name}

    def list_jobs(self):
        """List all cron jobs."""
        return [
            {
                "name": j.get("name"),
                "interval": f"{j.get('interval_seconds', 3600)}s",
                "enabled": j.get("enabled", True),
                "last_run": self._last_run.get(j.get("name", ""), 0),
            }
            for j in self.jobs
        ]
PYEOF