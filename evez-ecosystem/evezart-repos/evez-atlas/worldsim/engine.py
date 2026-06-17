#!/usr/bin/env python3
# evez-os/worldsim/engine.py -- WorldSim (A4)
# physics/economy/social/info/infra
# Kill switch: worldsim/STOP file
# Creator: Steven Crawford-Maggard (EVEZ666)

import json, random, hashlib, logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger('evez-os.worldsim')
GRID = 8
N_AGENTS = 10
FRICTION = 0.02
NOISE = 0.05
FAIL_P = 0.03

class WorldSimAgent:
    def __init__(self, agent_id):
        self.id = agent_id
        self.tokens = 100.0
        self.reputation = 0.5
        self.strategy = random.choice(['explore','exploit','cooperate','defect'])

    def act(self, world):
        if self.strategy == 'cooperate':
            self.reputation = min(1.0, self.reputation + 0.02)
        elif self.strategy == 'exploit':
            self.tokens += world.get('resource_density', 0.1) * 10
        elif self.strategy == 'defect':
            self.tokens += 5
            self.reputation = max(0.0, self.reputation - 0.05)
        self.tokens = max(0.0, self.tokens - FRICTION * self.tokens)
        return {'id': self.id, 'tokens': round(self.tokens, 3), 'rep': round(self.reputation, 3)}

def run_tick(seed=None):
    if Path('worldsim/STOP').exists():
        return None
    if seed:
        random.seed(seed)
    agents = [WorldSimAgent(i) for i in range(N_AGENTS)]
    world = {'resource_density': random.random(), 'infra_failure': random.random() < FAIL_P}
    results = [a.act(world) for a in agents]
    event = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'type': 'worldsim_tick',
        'world': world,
        'top3': sorted(results, key=lambda x: x['tokens'], reverse=True)[:3],
        'total_tokens': round(sum(r['tokens'] for r in results), 3),
    }
    event['sha256'] = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()[:16]
    Path('worldsim').mkdir(exist_ok=True)
    with open('worldsim/spine_delta.jsonl', 'a') as fp:
        fp.write(json.dumps(event) + '\n')
    return event

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    r = run_tick()
    if r:
        print(json.dumps(r, indent=2))
