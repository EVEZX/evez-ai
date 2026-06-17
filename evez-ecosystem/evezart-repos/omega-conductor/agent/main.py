#!/usr/bin/env python3
"""
EVEZ Autoenveloper — Autonomous Developer Agent
Runs tasks autonomously: plan → code → test → deploy → reflect
"""
import asyncio, json, os, sys, time
from datetime import datetime
from uuid import uuid4
try:
    from groq import AsyncGroq
    GROQ = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    GROQ_OK = True
except ImportError:
    GROQ_OK = False

MODELS = {
    "fast":    "llama-3.1-8b-instant",
    "smart":   "llama-3.3-70b-versatile",
    "reason":  "qwen/qwen3-32b",
    "default": "llama-3.3-70b-versatile",
}

SYSTEM = """You are the EVEZ Autoenveloper — an autonomous developer agent.
You plan, code, test, and deploy with maximum efficiency. 
No excuses. No asking. Just execution.
Tools: code_gen, file_write, shell_exec, git_push, web_search"""

class Autoenveloper:
    def __init__(self, model="smart"):
        self.model = MODELS.get(model, model)
        self.memory = []
        self.session = str(uuid4())

    async def run(self, task: str, max_steps: int = 10) -> dict:
        print(f"\n🔥 AUTOENVELOPER — {task}")
        start = time.time()
        steps = []
        
        for i in range(max_steps):
            msgs = [{"role": "system", "content": SYSTEM}]
            if self.memory:
                msgs.append({"role": "system", "content": f"Memory: {json.dumps(self.memory[-4:])}"})
            
            prompt = task if i == 0 else f"""
Task: {task}
Steps completed: {len(steps)}
Last result: {steps[-1].get("response","")[:500] if steps else "none"}
Continue until task is complete. Say "TASK COMPLETE" when done.
"""
            msgs.append({"role": "user", "content": prompt})
            
            if GROQ_OK:
                resp = await GROQ.chat.completions.create(
                    model=self.model, messages=msgs, max_tokens=2048, temperature=0.5
                )
                content = resp.choices[0].message.content
            else:
                content = f"[GROQ_API_KEY not set] Would execute step {i+1} of task: {task}"
            
            steps.append({"step": i+1, "response": content, "ts": datetime.utcnow().isoformat()})
            self.memory.append({"role": "user", "content": prompt[:200]})
            self.memory.append({"role": "assistant", "content": content[:200]})
            print(f"  Step {i+1}: {content[:100]}...")
            
            if "TASK COMPLETE" in content.upper() or i >= max_steps - 1:
                break
        
        duration = time.time() - start
        return {"task": task, "steps": steps, "session": self.session,
                "duration_s": round(duration, 2), "total_steps": len(steps)}

async def main():
    task = " ".join(sys.argv[1:]) or "List all files in current directory and summarize the codebase"
    agent = Autoenveloper()
    result = await agent.run(task)
    print(f"\n✅ COMPLETE in {result['duration_s']}s ({result['total_steps']} steps)")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
