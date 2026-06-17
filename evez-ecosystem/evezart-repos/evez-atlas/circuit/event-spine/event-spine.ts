import crypto from "crypto";

export type AtlasDomain =
  | "atlas"
  | "game"
  | "agents"
  | "fsc"
  | "governance"
  | "observability";

export interface EventSpineRecord<T = any> {
  id: string;
  index: number;
  timestamp: string;
  domain: AtlasDomain;
  kind: string;
  payload: T;
  prevHash: string | null;
  hash: string;
}

export class EventSpine {
  private _chain: EventSpineRecord[] = [];

  get chain(): ReadonlyArray<EventSpineRecord> {
    return this._chain;
  }

  append<T = any>(event: {
    domain: AtlasDomain;
    kind: string;
    payload: T;
  }): EventSpineRecord<T> {
    const index = this._chain.length;
    const timestamp = new Date().toISOString();
    const prevHash = index === 0 ? null : this._chain[index - 1].hash;

    const id = crypto.randomUUID();
    const base = {
      id,
      index,
      timestamp,
      domain: event.domain,
      kind: event.kind,
      payload: event.payload,
      prevHash,
    };

    const hash = this.computeHash(base);
    const record: EventSpineRecord<T> = { ...base, hash };

    this._chain.push(record);
    return record;
  }

  replay(): EventSpineRecord[] {
    return [...this._chain];
  }

  verify(): { ok: boolean; error?: string; index?: number } {
    for (let i = 0; i < this._chain.length; i++) {
      const rec = this._chain[i];
      const expectedHash = this.computeHash({
        id: rec.id,
        index: rec.index,
        timestamp: rec.timestamp,
        domain: rec.domain,
        kind: rec.kind,
        payload: rec.payload,
        prevHash: rec.prevHash,
      });

      if (rec.hash !== expectedHash) {
        return { ok: false, error: "hash_mismatch", index: i };
      }

      if (i === 0 && rec.prevHash !== null) {
        return { ok: false, error: "bad_prev_hash_genesis", index: i };
      }

      if (i > 0 && rec.prevHash !== this._chain[i - 1].hash) {
        return { ok: false, error: "bad_prev_hash_link", index: i };
      }
    }
    return { ok: true };
  }

  private computeHash(obj: any): string {
    const json = JSON.stringify(obj);
    return crypto.createHash("sha256").update(json).digest("hex");
  }

  toJSON() {
    return this._chain;
  }

  static fromJSON(data: EventSpineRecord[]): EventSpine {
    const spine = new EventSpine();
    spine._chain = data;
    return spine;
  }
}
