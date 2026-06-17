import { createHash, randomUUID } from 'crypto';
import { writeFileSync, readFileSync, existsSync, mkdirSync } from 'fs';
import { EventStore } from './event-store';

export interface Checkpoint {
  checkpointId: string;
  streamId: string;
  position: number;
  stateSnapshot: unknown;
  timestamp: number;
  checksum: string;
}

export interface CheckpointToken {
  version: string;
  agentId: string;
  checkpointId: string;
  position: number;
  checksum: string;
  issuedAt: number;
  expiresAt: number;
}

export class CheckpointManager {
  private dir: string;
  private store: EventStore;

  constructor(store: EventStore, dir = 'data/checkpoints') {
    this.store = store;
    this.dir = dir;
    mkdirSync(dir, { recursive: true });
  }

  create(streamId: string, state: unknown): Checkpoint {
    const events = this.store.readStream(streamId);
    const position = events.length > 0 ? (events[events.length - 1] as any).position : 0;
    const stateStr = JSON.stringify(state);
    const checksum = createHash('sha256').update(stateStr).digest('hex');
    const cp: Checkpoint = {
      checkpointId: randomUUID(), streamId, position,
      stateSnapshot: state, timestamp: Date.now(), checksum,
    };
    writeFileSync(`${this.dir}/${streamId.replace(':', '_')}.json`, JSON.stringify(cp));
    return cp;
  }

  getLatest(streamId: string): Checkpoint | null {
    const path = `${this.dir}/${streamId.replace(':', '_')}.json`;
    if (!existsSync(path)) return null;
    return JSON.parse(readFileSync(path, 'utf8')) as Checkpoint;
  }

  issueToken(agentId: string): CheckpointToken | null {
    const cp = this.getLatest(`agent:${agentId}`);
    if (!cp) return null;
    return {
      version: '1.0', agentId,
      checkpointId: cp.checkpointId,
      position: cp.position,
      checksum: cp.checksum,
      issuedAt: Date.now(),
      expiresAt: Date.now() + 7 * 24 * 3_600_000,
    };
  }
}
