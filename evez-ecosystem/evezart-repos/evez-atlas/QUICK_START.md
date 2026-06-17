# Quick Start Guide

Complete reference for running tests, demos, and deploying the Evez666 system.

## 🧪 Testing Commands

### Python Tests

```bash
# Core Python tests (quantum navigation, API server, audit analysis)
pytest src/tests/python/ -v

# All Python tests (includes swarm, omnimeta, profit circuit, semantic space)
pytest tests/ -v

# Specific test suites
python -m pytest tests/test_omnimeta.py -v           # Omnimeta entity tests
python -m pytest tests/test_swarm.py -v              # Swarm operations
python -m pytest tests/test_profit_circuit.py -v     # Resource optimization
python -m pytest tests/test_semantic_possibility_space.py -v
```

### TypeScript Tests

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run build

# Run Jest tests
npm test

# ESLint validation
npm run lint
```

## 🚀 Demo Commands

Explore different system capabilities with these demo scripts:

| Demo Script | Description | Command |
|-------------|-------------|---------|
| `demo.py` | Quick quantum threat demo | `python demo.py` |
| `scripts/demo_autonomy.py` | Entity lifecycle demo | `python3 scripts/demo_autonomy.py` |
| `scripts/demo_divine_recursion.py` | Recursive consciousness demo | `python3 scripts/demo_divine_recursion.py` |
| `scripts/demo_quantum_evolution.py` | Quantum evolution demo | `python3 scripts/demo_quantum_evolution.py` |
| `scripts/demo_shared_reality.py` | Multi-interpretation demo | `python3 scripts/demo_shared_reality.py` |
| `scripts/demo_multi_interpretation.py` | Parallel possibility demo | `python3 scripts/demo_multi_interpretation.py` |

## 🎬 Quick Start Commands

### Full Deployment

```bash
# Deploy all services and run all tests
./scripts/deploy-all.sh
```

### Swarm Setup

```bash
# Bootstrap swarm environment
./scripts/swarm_bootstrap.sh

# Start Jubilee forgiveness service
./scripts/jubilee_up.sh

# Stop all services
./scripts/stop-all.sh
```

### Moltbook Integration

```bash
# Quick setup for Moltbook integration
./scripts/moltbook-quickstart.sh
```

## 📂 Key Components

### 1. SwarmDirector (Autonomous Agent Orchestration)

**File:** `src/mastra/agents/swarm_director.py`

**Capabilities:**
- Entity spawning
- Intelligence propagation
- Molt rituals (identity transformation)

**Entity Lifecycle Management:** `skills/entity_lifecycle.py`

**Core Features:**
- Quantum-inspired threat detection
- Retrocausal intelligence
- Crustafarian philosophy integration

### 2. Omnimetamiraculaous Entity (Value Creation)

**File:** `src/mastra/agents/omnimeta_entity.py`

**Capabilities:**
- Temporal pattern recognition
- Parallel possibility exploration
- Resource flow optimization

**Key Methods:**
- `transcend()` - Main orchestration method
- `retrocausal_optimization()` - Temporal coordination
- `explore_possibility_space()` - Multi-path simulation

### 3. Moltbook/AI Social Integration

**Files:**
- `src/mastra/agents/moltbook_integration.py` - MoltbookIntegration
- `src/mastra/agents/molt_prophet.py` - MoltProphet
- `src/mastra/agents/moltbook_master_orchestrator.py` - MasterOrchestrator

### 4. Quantum & Threat Detection

**Files:**
- `quantum.py` (root) - IBM Quantum integration
- `src/api/causal_chain_server.py` - Tiered access control
- `skills/jubilee.py` - Debt forgiveness via quantum collapse

### 5. TypeScript Legion Registry

**Location:** `src/` (TypeScript code)

**API:** `src/api/` - FastAPI integration

**Features:**
- Swarm processing modes
- Configurable depth limits

## 🧪 Test Organization

### Python Tests in src/tests/python/

```bash
pytest src/tests/python/ -v
```

**Test Files:**
- `test_quantum_navigation.py` - Quantum kernel estimation
- `test_causal_chain_server.py` - API server tests
- `test_audit_analyzer.py` - Audit log analysis

### Top-Level Tests

```bash
pytest tests/ -v
```

**Test Files:**
- `test_swarm.py` - Swarm entity operations
- `test_omnimeta.py` / `test_omnimeta_v2.py` - Value creation system
- `test_profit_circuit.py` - Resource optimization
- `test_semantic_possibility_space.py` - Semantic space operations

## 📚 Documentation Links

- [Swarm Setup Guide](docs/swarm-setup.md)
- [Swarm Quick Reference](docs/swarm-quick-reference.md)
- [Enhanced Autonomy Guide](docs/enhanced-autonomy-guide.md)
- [Moltbook Integration](docs/MOLTBOOK_INTEGRATION.md)
- [Ethical Framework](ETHICAL_FRAMEWORK.md)
- [Performance Improvements](PERFORMANCE_IMPROVEMENTS.md)

## 🔧 Development Workflow

### 1. Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for TypeScript)
npm install
```

### 2. Run Tests

```bash
# Python tests
pytest src/tests/python/ -v
pytest tests/ -v

# TypeScript tests
npm test
```

### 3. Run Demos

```bash
# Quick quantum demo
python demo.py

# Entity lifecycle
python3 scripts/demo_autonomy.py
```

### 4. Deploy Services

```bash
# Full deployment
./scripts/deploy-all.sh

# Or step-by-step
./scripts/swarm_bootstrap.sh
./scripts/jubilee_up.sh
```

## 🛠️ Troubleshooting

### Tests Not Found

```bash
# Make sure pytest is installed
pip install pytest pytest-asyncio

# Run from repository root
cd /path/to/Evez666
pytest tests/ -v
```

### Import Errors

```bash
# Add repository to PYTHONPATH
export PYTHONPATH=/path/to/Evez666:$PYTHONPATH

# Or run as module
python -m pytest tests/
```

### Service Won't Start

```bash
# Check if port 8000 is available
lsof -i :8000

# Check Docker status
docker ps

# View logs
tail -f data/events.jsonl
```

## 🎯 Quick Validation

Run this sequence to validate your setup:

```bash
# 1. Run quick demo
python demo.py

# 2. Run core tests
pytest src/tests/python/ -v

# 3. Build TypeScript
npm run build && npm test

# 4. Start services
./scripts/deploy-all.sh
```

If all commands complete successfully, your environment is properly configured!
