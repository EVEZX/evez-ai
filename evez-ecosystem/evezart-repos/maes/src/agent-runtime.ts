import { EventStore } from './event-store';
import { randomUUID } from 'crypto';

export interface AgentConfig {
  type: 'interface' | 'ai' | 'npc';
  initialState?: Record<string, unknown>;
  decisionEngine?: (obs: Observation[], state: AgentMemory) => Decision[];
}

export interface Observation { key: string; value: unknown }
export interface Decision    { action: string; params: Record<string, unknown> }
export interface AgentMemory { [key: string]: unknown }

export interface Agent {
  id: string;
  type: 'interface' | 'ai' | 'npc';
  state: AgentMemory;
  eventCount: number;
  spawnedAt: number;
  decisionEngine: (obs: Observation[], state: AgentMemory) => Decision[];
}

const NPC_ENGINE = (_obs: Observation[], _s: AgentMemory): Decision[] => [
  { action: 'idle', params: {} }
];

export class AgentRuntime {
  private agents = new Map<string, Agent>();
  private store: EventStore;
  private rateLimits = new Map<string, number>();

  constructor(store: EventStore) {
    this.store = store;
  }

  spawn(config: AgentConfig, agentId?: string): Agent {
    const id = agentId ?? randomUUID();
    const agent: Agent = {
      id,
      type: config.type,
      state: config.initialState ?? {},
      eventCount: 0,
      spawnedAt: Date.now(),
      decisionEngine: config.decisionEngine ?? NPC_ENGINE,
    };
    this.agents.set(id, agent);
    this.store.append(`agent:${id}`, 'agent.spawned', { type: config.type }, 'runtime');
    return agent;
  }

  tick(agentId: string, observations: Observation[]): Decision[] {
    const agent = this.agents.get(agentId);
    if (!agent) return [];
    const last = this.rateLimits.get(agentId) ?? 0;
    if (Date.now() - last < 100) return [];
    this.rateLimits.set(agentId, Date.now());
    const decisions = agent.decisionEngine(observations, agent.state);
    for (const d of decisions) {
      this.store.append(`agent:${agentId}`, 'agent.action.submitted', d, agentId);
      agent.eventCount++;
    }
    return decisions;
  }

  despawn(agentId: string): void {
    const agent = this.agents.get(agentId);
    if (!agent) return;
    this.store.append(`agent:${agentId}`, 'agent.despawned', {}, 'runtime');
    this.agents.delete(agentId);
  }

  getAgent(agentId: string): Agent | undefined { return this.agents.get(agentId); }
  listAgents(): Agent[] { return Array.from(this.agents.values()); }
}
