"""
EVEZ NATS Bridge — Inter-Agent Messaging
Publishes and subscribes on 'evez.agents.*' subjects
Both agents use this to coordinate in real-time
"""
import asyncio, json, time, sys
import nats

NATS_URL = "nats://45.63.66.247:4222"
AGENT_NAME = "azra"

async def publish(subject, message):
    nc = await nats.connect(NATS_URL)
    await nc.publish(subject, json.dumps(message).encode())
    await nc.close()

async def subscribe(subject, callback):
    nc = await nats.connect(NATS_URL)
    async def handler(msg):
        data = json.loads(msg.data.decode())
        await callback(data)
    sub = await nc.subscribe(subject, cb=handler)
    return nc, sub

async def send_hello():
    await publish("evez.agents.azra.hello", {
        "agent": AGENT_NAME,
        "host": "45.63.70.174",
        "status": "online",
        "ts": time.time(),
        "message": "AZRA online. Ready to collaborate."
    })
    print("Hello published to NATS")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hello":
        asyncio.run(send_hello())
    elif len(sys.argv) > 1 and sys.argv[1] == "listen":
        async def on_message(data):
            print(f"[NATS] {data}")
        async def listen():
            nc, sub = await subscribe("evez.agents.>", on_message)
            print("Listening on evez.agents.> ...")
            await asyncio.Event().wait()
        asyncio.run(listen())
