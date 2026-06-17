LORD bridge integration

Files in this package:
- bridge_schema.py validates incoming fusion-update payloads
- lord_bridge.py runs the websocket receiver and adapter
- registry.py provides an additive registry for mutation and invariant hooks
- bootstrap.py provides an explicit bootstrap sequence helper
- __init__.py exports the package surface

Default listener: ws://127.0.0.1:8765

Run command: python -m src.integrations.lord_bridge.lord_bridge

Expected top-level message type: fusion-update
Required nested fields:
meta.recursionLevel
meta.entityType
crystallization.progress
corrections.current

Integration model:
Create an adapter object with apply_lord_state(state) and pass it into LordBridgeServer.
