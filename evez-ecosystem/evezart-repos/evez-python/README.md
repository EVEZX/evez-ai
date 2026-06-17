# evez-ai

```python
from evez_ai import EvezAI

evez = EvezAI("evez-your-api-key")

response = evez.chat.completions.create(
    model=EvezAI.MODELS.SMART,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response["choices"][0]["message"]["content"])
```

Get your free API key at [evez-api2.fly.dev/signup](https://evez-api2.fly.dev/signup)
