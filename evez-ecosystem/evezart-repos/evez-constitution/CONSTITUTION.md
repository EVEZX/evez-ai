# EVEZ CONSTITUTION - Event Spine Architecture

## Constitutional Root
This repository serves as the constitutional root for the EVEZ federated system.

## Event Schema
- **Observation Event**: git commit, workflow run, build artifact
- **Transform Event**: code change, model execution, inference
- **Contradiction Event**: failed assertion, CI failure, divergent hash

## Hash Laws
- Every artifact has `transform_hash` (content hash)
- Every event has `event_hash` (state hash)
- Every contradiction has `contradiction_hash`

## Repositories in Federation
| Role | Repository | Status |
|------|------------|--------|
| Constitutional Root | evez | This repo |
| Proving Ground | agentvault/ephv | CI replay target |
| Observation | crawhub/CrawFather | Evidence packets |
| Analysis | codeql/codex | Transform scrutiny |

## Deploy Sequence
1. Store rules bundle, event schemas, golden vectors
2. Validate agentvault CI runs against schema
3. Emit run bundles with transform_hash
4. Force contradiction core → repair → replay
