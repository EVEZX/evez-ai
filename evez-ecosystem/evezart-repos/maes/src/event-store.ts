import Database from 'better-sqlite3';
import { randomUUID } from 'crypto';

export interface GameEvent {
  eventId: string;
  streamId: string;
  eventType: string;
  timestamp: number;
  payload: unknown;
  metadata: { causedBy: string; position: number };
}

export class EventStore {
  private db: Database.Database;

  constructor(dbPath = 'data/events.db') {
    this.db = new Database(dbPath);
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS events (
        position    INTEGER PRIMARY KEY AUTOINCREMENT,
        eventId     TEXT    UNIQUE NOT NULL,
        streamId    TEXT    NOT NULL,
        eventType   TEXT    NOT NULL,
        timestamp   INTEGER NOT NULL,
        payload     TEXT    NOT NULL,
        causedBy    TEXT    NOT NULL
      );
      CREATE INDEX IF NOT EXISTS idx_stream ON events(streamId, position);
    `);
  }

  append(streamId: string, eventType: string, payload: unknown, causedBy: string): number {
    const stmt = this.db.prepare(`
      INSERT INTO events (eventId, streamId, eventType, timestamp, payload, causedBy)
      VALUES (?, ?, ?, ?, ?, ?)
    `);
    const res = stmt.run(
      randomUUID(), streamId, eventType,
      Date.now(), JSON.stringify(payload), causedBy
    );
    return res.lastInsertRowid as number;
  }

  readStream(streamId: string, fromPosition = 0, max = 1000): GameEvent[] {
    return this.db.prepare(`
      SELECT * FROM events WHERE streamId = ? AND position >= ?
      ORDER BY position ASC LIMIT ?
    `).all(streamId, fromPosition, max) as GameEvent[];
  }

  readAll(fromPosition = 0, max = 1000): GameEvent[] {
    return this.db.prepare(`
      SELECT * FROM events WHERE position >= ? ORDER BY position ASC LIMIT ?
    `).all(fromPosition, max) as GameEvent[];
  }
}
