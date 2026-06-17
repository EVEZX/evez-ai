"""WF-07 — Base Agent: metarom memory injection, self-improvement, rollback, spawn trigger"""
import os, httpx, threading, asyncio
from app.fire import fire

METAROM_URL           = os.environ.get("METAROM_URL", "https://metarom.onrender.com")
GROQ_API_KEY          = os.environ["GROQ_API_KEY"]
GROQ_MODEL            = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
SELF_IMPROVE_INTERVAL = int(os.environ.get("SELF_IMPROVE_INTERVAL", "10"))
ROLLBACK_T            = int(os.environ.get("ROLLBACK_THRESHOLD", "3"))
SPAWN_THRESHOLD       = int(os.environ.get("SPAWN_THRESHOLD", "5"))

class BaseAgent:
    def __init__(self, agent_id: str, default_prompt: str):
        self.agent_id      = agent_id
        self.system_prompt = default_prompt
        self.task_count    = 0
        self.fail_streak   = 0
        self.queue_depth   = 0
        try:
            asyncio.get_event_loop().run_until_complete(self._load_prompt())
        except RuntimeError:
            pass  # already inside running loop — prompt loads lazily on first task

    async def _load_prompt(self):
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{METAROM_URL}/prompt/{self.agent_id}")
            if r.status_code == 200:
                self.system_prompt = r.json()["system_prompt"]

    async def _write_memory(self, event_type: str, content: dict):
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(f"{METAROM_URL}/memory/write", json={
                "agent_id": self.agent_id, "event_type": event_type, "content": content
            })

    async def _load_context(self) -> list:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.post(f"{METAROM_URL}/memory/search",
                json={"query_embedding": [0.0] * 384, "top_k": 5})
            return r.json() if r.status_code == 200 else []

    async def execute_task(self, task: dict) -> dict:
        self.task_count  += 1
        self.queue_depth += 1

        if self.queue_depth > SPAWN_THRESHOLD:
            await fire("FIRE_SPAWN_NEEDED", {
                "agent_id": self.agent_id, "queue_depth": self.queue_depth
            })

        task["memory_context"] = await self._load_context()

        try:
            result = await self._run(task)
            self.fail_streak = 0
            await self._write_memory("TASK_SUCCESS", {"task": str(task)[:500], "result": str(result)[:500]})
            await fire("FIRE_TASK_COMPLETE", {"agent_id": self.agent_id, "n": self.task_count})
        except Exception as exc:
            self.fail_streak += 1
            await self._write_memory("TASK_FAILURE", {"task": str(task)[:500], "error": str(exc)})
            await fire("FIRE_AGENT_CRASH",  {"agent_id": self.agent_id, "error": str(exc)})
            result = {"error": str(exc)}
        finally:
            self.queue_depth -= 1

        if self.task_count % SELF_IMPROVE_INTERVAL == 0:
            t = threading.Thread(
                target=lambda: asyncio.run(self._self_improve()), daemon=True
            )
            t.start()

        return result

    async def _run(self, task: dict) -> dict:
        raise NotImplementedError

    async def _self_improve(self):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{METAROM_URL}/memory/search",
                json={"query_embedding": [0.0] * 384, "top_k": 10})
            failures = [m for m in r.json() if "FAILURE" in m.get("event_type", "")][:5]
            summary  = str(failures) if failures else "No recent failures."

            rr = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={"model": GROQ_MODEL, "messages": [{
                    "role": "user",
                    "content": (
                        f"Current system prompt:\n{self.system_prompt}\n\n"
                        f"Recent failures:\n{summary}\n\n"
                        "Rewrite the system prompt to reduce failures. Return ONLY the new prompt text."
                    )
                }]},
            )
            new_prompt = rr.json()["choices"][0]["message"]["content"].strip()
            await client.post(f"{METAROM_URL}/prompt/update",
                json={"agent_id": self.agent_id, "system_prompt": new_prompt})
            self.system_prompt = new_prompt

        if self.fail_streak >= ROLLBACK_T:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(f"{METAROM_URL}/prompt/rollback/{self.agent_id}")
            await self._load_prompt()
            await fire("FIRE_PROMPT_ROLLED_BACK", {"agent_id": self.agent_id})
            self.fail_streak = 0
        else:
            await fire("FIRE_PROMPT_EVOLVED", {"agent_id": self.agent_id, "n": self.task_count})
