from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "agentvault.sqlite"


def search(conn: sqlite3.Connection, query: str, limit: int = 8):
    rows = conn.execute(
        """
        SELECT d.source, d.path, COALESCE(d.title,'') as title,
               snippet(docs_fts, 1, '[', ']', '…', 12) as snip
        FROM docs_fts
        JOIN docs d ON d.id = docs_fts.rowid
        WHERE docs_fts MATCH ?
        ORDER BY bm25(docs_fts)
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()

    return [
        {"source": r[0], "path": r[1], "title": r[2], "snippet": r[3]}
        for r in rows
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    results = search(conn, args.query, args.limit)
    print(json.dumps({"query": args.query, "results": results}, indent=2))


if __name__ == "__main__":
    main()
