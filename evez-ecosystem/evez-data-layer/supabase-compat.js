/**
 * Supabase-compatible local layer using SQLite
 * Drop-in replacement for @supabase/supabase-js
 */
import Database from 'better-sqlite3';
import { randomUUID } from 'crypto';
import { readFileSync, existsSync } from 'fs';

const DB_PATH = process.env.EVEZ_DB_PATH || '/home/openclaw/evez-ecosystem/evez-data-layer/evez.db';

class LocalTable {
  constructor(db, table) {
    this.db = db;
    this.table = table;
    this._filters = [];
    this._orderField = null;
    this._limitN = null;
  }
  
  select(cols = '*') { this._cols = cols; return this; }
  eq(col, val) { this._filters.push({col, op: '=', val}); return this; }
  neq(col, val) { this._filters.push({col, op: '!=', val}); return this; }
  gt(col, val) { this._filters.push({col, op: '>', val}); return this; }
  lt(col, val) { this._filters.push({col, op: '<', val}); return this; }
  order(col) { this._orderField = col; return this; }
  limit(n) { this._limitN = n; return this; }
  single() { this._limitN = 1; return this; }
  
  async then(resolve) {
    try {
      let sql = `SELECT ${this._cols || '*'} FROM ${this.table}`;
      const params = [];
      if (this._filters.length) {
        sql += ' WHERE ' + this._filters.map(f => `${f.col} ${f.op} ?`).join(' AND ');
        this._filters.forEach(f => params.push(f.val));
      }
      if (this._orderField) sql += ` ORDER BY ${this._orderField}`;
      if (this._limitN) sql += ` LIMIT ${this._limitN}`;
      const rows = this.db.prepare(sql).all(...params);
      resolve({ data: rows, error: null });
    } catch (e) {
      resolve({ data: null, error: e.message });
    }
  }
  
  insert(rows) {
    const self = this;
    return {
      async then(resolve) {
        try {
          const stmts = [];
          for (const row of Array.isArray(rows) ? rows : [rows]) {
            if (!row.id) row.id = randomUUID();
            const cols = Object.keys(row);
            const vals = Object.values(row);
            const sql = `INSERT INTO ${self.table} (${cols.join(',')}) VALUES (${cols.map(() => '?').join(',')})`;
            self.db.prepare(sql).run(...vals);
          }
          resolve({ data: rows, error: null });
        } catch (e) {
          resolve({ data: null, error: e.message });
        }
      }
    };
  }
  
  update(data) {
    const self = this;
    return {
      async then(resolve) {
        try {
          const cols = Object.keys(data);
          const vals = Object.values(data);
          let sql = `UPDATE ${self.table} SET ${cols.map(c => `${c} = ?`).join(',')}`;
          const params = [...vals];
          if (self._filters.length) {
            sql += ' WHERE ' + self._filters.map(f => `${f.col} ${f.op} ?`).join(' AND ');
            self._filters.forEach(f => params.push(f.val));
          }
          self.db.prepare(sql).run(...params);
          resolve({ data, error: null });
        } catch (e) {
          resolve({ data: null, error: e.message });
        }
      }
    };
  }
  
  delete() {
    const self = this;
    return {
      async then(resolve) {
        try {
          let sql = `DELETE FROM ${self.table}`;
          const params = [];
          if (self._filters.length) {
            sql += ' WHERE ' + self._filters.map(f => `${f.col} ${f.op} ?`).join(' AND ');
            self._filters.forEach(f => params.push(f.val));
          }
          self.db.prepare(sql).run(...params);
          resolve({ data: null, error: null });
        } catch (e) {
          resolve({ data: null, error: e.message });
        }
      }
    };
  }
}

export function createClient() {
  const db = existsSync(DB_PATH) 
    ? new Database(DB_PATH) 
    : new Database(DB_PATH);
  
  db.pragma('journal_mode = WAL');
  
  // Auto-create tables on first use
  return {
    from(table) {
      // Ensure table exists
      try { db.prepare(`SELECT 1 FROM ${table} LIMIT 0`).get(); } 
      catch { db.prepare(`CREATE TABLE IF NOT EXISTS ${table} (id TEXT PRIMARY KEY, data TEXT)`).run(); }
      return new LocalTable(db, table);
    },
    rpc(fn, params) {
      return new LocalTable(db, fn);
    }
  };
}
