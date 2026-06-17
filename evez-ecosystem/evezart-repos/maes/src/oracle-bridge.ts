/**
 * MAES ↔ EVEZ-OS Oracle Bridge
 * Subscribes to EVEZ-OS FIRE events and injects them as
 * agent observations into the MAES runtime.
 */

import { EventEmitter } from 'events';
import { AgentRuntime, Observation } from './agent-runtime';
import { EventStore } from './event-store';

export interface FireEvent {
  id: string;
  type: string;       // 'FIRE' | 'VOLTAGE_SPIKE' | 'TOPOLOGY_SHIFT' | ...
  source: string;     // circuit node id
  value: number;      // normalized 0–1
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export class OracleBridge extends EventEmitter {
  private runtime: AgentRuntime;
  private store: EventStore;
  private subscriptions = new Map<string, string[]>(); // agentId → event types

  constructor(runtime: AgentRuntime, store: EventStore) {
    super();
    this.runtime = runtime;
    this.store = store;
  }

  /**
   * Subscribe an agent to FIRE event types from EVEZ-OS.
   * When a matching FIRE event arrives, it becomes an observation
   * on the agent's next tick.
   */
  subscribe(agentId: string, eventTypes: string[]): void {
    this.subscriptions.set(agentId, eventTypes);
    this.store.append(
      `oracle:${agentId}`,
      'oracle.subscribed',
      { eventTypes },
      'oracle-bridge'
    );
  }

  /**
   * Ingest a FIRE event from EVEZ-OS (called by webhook or SSE listener).
   * Fans out to all subscribed agents as observations.
   */
  ingest(fire: FireEvent): void {
    this.store.append('oracle:global', 'fire.received', fire, 'evez-os');
    this.emit('fire', fire);

    for (const [agentId, types] of this.subscriptions) {
      if (!types.includes(fire.type) && !types.includes('*')) continue;

      const obs: Observation[] = [
        { key: 'fire.type',      value: fire.type },
        { key: 'fire.source',    value: fire.source },
        { key: 'fire.value',     value: fire.value },
        { key: 'fire.timestamp', value: fire.timestamp },
        ...(fire.metadata
          ? Object.entries(fire.metadata).map(([k, v]) => ({ key: `fire.meta.${k}`, value: v }))
          : []
        ),
      ];

      this.runtime.tick(agentId, obs);
    }
  }

  /**
   * RSI-governed cycle: poll EVEZ-OS event spine every `intervalMs`
   * and re-ingest any new FIRE events since last position.
   */
  startPolling(intervalMs = 5000): NodeJS.Timeout {
    let lastPos = 0;
    return setInterval(() => {
      const events = this.store.readAll(lastPos + 1, 100);
      if (!events.length) return;
      lastPos = (events[events.length - 1] as any).position;

      for (const ev of events) {
        if (ev.eventType.startsWith('fire.')) {
          const payload = JSON.parse(ev.payload as string);
          this.emit('cycle', { position: lastPos, event: ev, payload });
        }
      }
    }, intervalMs);
  }
}
