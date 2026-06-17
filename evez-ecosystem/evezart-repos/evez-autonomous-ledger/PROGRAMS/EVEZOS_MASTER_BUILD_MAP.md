# EVEZOS Master Build Map

Status: active
Date: 2026-03-19

## Live surfaces
- Lovable core product surface
- Base44 immersive mobile operator surface
- Manus website cinematic surface
- Manus mobile app surface
- Vercel deployment surface
- n8n orchestration surface
- Local longscale and mobile code packages

## Core system
### Agent runtime
- Scanner
- Predictor
- Generator
- Shipper
- WorldSim

### Control planes
- Ledger: audit trail of actions, outcomes, and provenance
- Mission Bus: task dispatch and status tracking
- Chat terminal: future OpenAI / ChatGPT route
- Settings layer: GitHub, Vercel, OpenAI, Lovable, Manus, n8n credentials and endpoints

## App packages
### Longscale package
Contains:
- agent modules
- /api/agent-run
- /api/chat
- /api/opportunities
- /api/ledger
- /api/bus
- ledger UI
- bus UI
- n8n import workflow JSON

### Mobile package
Contains:
- Home
- Cycle
- Workflows
- Deliverables
- Ledger
- Chat
- Settings
- phone-first navigation and styling

## n8n target wiring
1. Webhook trigger receives operator input
2. Optional Set/Edit Fields normalizes payload
3. OpenAI node or HTTP Request node calls OpenAI Responses API
4. HTTP Request nodes call app endpoints:
   - /api/agent-run
   - /api/opportunities
   - /api/ledger
   - /api/bus
5. Respond to Webhook returns world state / deliverables / status

## Immediate sequence
1. Deploy longscale or mobile app
2. Import workflow JSON into n8n
3. Add OpenAI credential in n8n
4. Point workflow nodes at deployed app endpoints
5. Replace mock data with live webhook and queue telemetry
6. Bind ledger and bus to persistent storage

## Blockers
- protected sign-in flows for production systems
- OpenAI API key and final external credentials
- final deploy/import confirmation steps inside vendor dashboards

## Next expansion
- persistent database
- real n8n workflow telemetry
- publishing connectors
- faction/world overlays
- investor analytics dashboard
- memory and provenance synchronization
