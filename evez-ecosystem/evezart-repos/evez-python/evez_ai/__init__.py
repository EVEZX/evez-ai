"""EVEZ AI Python SDK — OpenAI-compatible, 99% cheaper than GPT-4"""
import json, urllib.request, urllib.error

BASE_URL = "https://evez-api2.fly.dev/v1"

class EvezAI:
    MODELS = type('M', (), {'SMART': 'evez-smart', 'CODE': 'evez-code', 'FAST': 'evez-fast', 'VISION': 'evez-vision'})()
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = self._Chat(self)
    
    class _Chat:
        def __init__(self, client):
            self.completions = client._Completions(client)
    
    class _Completions:
        def __init__(self, client):
            self._client = client
        
        def create(self, **kwargs):
            data = json.dumps(kwargs).encode()
            req = urllib.request.Request(
                f"{BASE_URL}/chat/completions",
                data=data,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._client.api_key}"}
            )
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
