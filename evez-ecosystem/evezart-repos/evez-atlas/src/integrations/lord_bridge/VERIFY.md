# LORD bridge verification

## Runtime listener

Start the listener from the project root:

```bash
python -m src.integrations.lord_bridge.lord_bridge
```

## Python smoke test

Send a known-good payload:

```bash
python src/integrations/lord_bridge/smoke_test.py
```

## Browser test

After the monitor site is republished, open:

- `/lord-monitor/bridge-test.html`
- `/lord-monitor/ops-checklist.html`
- `/lord-monitor/status.json`

## Expected outcome

- the websocket listener accepts the payload on `ws://127.0.0.1:8765`
- the bridge computes urgency
- the bridge normalizes state for downstream runtime use
- the Airtable implementation records can then be marked complete
