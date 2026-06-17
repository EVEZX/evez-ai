"""openclaw.client — Responses API model client (server-side only).
SECURITY: OPENAI_API_KEY read from env. Never commit keys. Never expose in browser/mobile.
"""
import os, json, urllib.request, urllib.error


class ModelClient:
    def __init__(self, model="gpt-4o-mini"):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = model

    def propose(self, system: str, user: str, tools: list | None = None) -> dict:
        if not self.api_key:
            return {"error": "OPENAI_API_KEY not set", "content": ""}
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if tools:
            body["tools"] = tools
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                resp = json.loads(r.read())
            return resp["choices"][0]["message"]
        except urllib.error.HTTPError as e:
            return {"error": str(e), "content": ""}
