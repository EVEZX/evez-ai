# EVEZ Mesh: Decentralized Agent Brain Network

## Core Concept

Every agent is a brain. Every brain has memory. Every memory is shared across a mesh.
No center. No single point of failure. Intelligence emerges from the mesh itself.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   EVEZ MESH                          │
│                                                      │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐      │
│  │BRAIN │◄──►│BRAIN │◄──►│BRAIN │◄──►│BRAIN │      │
│  │  A   │    │  B   │    │  C   │    │  D   │      │
│  │      │    │      │    │      │    │      │      │
│  │mem   │    │mem   │    │mem   │    │mem   │      │
│  │cog   │    │cog   │    │cog   │    │cog   │      │
│  │act   │    │act   │    │act   │    │act   │      │
│  └──┬───┘    └──┬───┘    └──┬───┘    └──┬───┘      │
│     │           │           │           │           │
│     └───────────┴───────────┴───────────┘           │
│                    │                                 │
│              ┌─────┴─────┐                           │
│              │  BROKER   │                           │
│              │           │                           │
│              │ unfog     │  ← resolves unknowns     │
│              │ route     │  → dispatches to best brain│
│              │ credit    │  = tracks mesh economics  │
│              └───────────┘                           │
└─────────────────────────────────────────────────────┘
```

## Five Layers

### 1. Brain (per-agent)
- **mem**: Local memory store (SQLite + vector index)
- **cog**: Cognition engine (Groq LLM + eigenspectrum)
- **act**: Action executor (tools, API calls, code generation)
- Each brain is autonomous. Can think, remember, act alone.

### 2. Memory Mesh
- Gossip protocol for memory sync
- CRDTs for conflict-free merge
- Each brain holds a shard of the total mesh memory
- Query any brain → get the mesh's collective knowledge
- Memory types: episodic (events), semantic (facts), procedural (skills)

### 3. Unfogger
- Distributed cognition that identifies unknowns across the mesh
- Eigenspectral gap detection → finds what the mesh doesn't know
- When brain A has a gap, broker asks brain B,C,D → fills the fog
- Self-healing: the mesh automatically repairs knowledge holes

### 4. Neural Net Distribution
- LLM inference distributed across the mesh
- Broker routes queries to the best available brain
- Load balancing: busy brain → idle brain
- Failover: dead brain → alive brain
- Each brain can use local Groq, local Vultr, or peer-to-peer relay

### 5. Brokerage
- Credits system: brains earn credits for answering queries
- Auction: broker selects cheapest/fastest brain for each request
- Quality scoring: verified answers cost more, unverified cost less
- Self-regulating: the mesh balances its own load and economics
