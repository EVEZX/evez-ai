from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from bs4 import BeautifulSoup
from dateutil import parser as dtparser


VAULT_DIR = Path("vault")
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "agentvault.sqlite"


def _ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _db() -> sqlite3.Connection:
    _ensure_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS docs (
          id INTEGER PRIMARY KEY,
          source TEXT NOT NULL,
          path TEXT NOT NULL,
          title TEXT,
          created_at TEXT,
          content TEXT NOT NULL,
          sha256 TEXT,
          ingested_at TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
          title,
          content,
          source UNINDEXED,
          path UNINDEXED,
          content='docs',
          content_rowid='id'
        );

        CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON docs BEGIN
          INSERT INTO docs_fts(rowid, title, content, source, path)
          VALUES (new.id, new.title, new.content, new.source, new.path);
        END;

        CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON docs BEGIN
          INSERT INTO docs_fts(docs_fts, rowid, title, content, source, path)
          VALUES('delete', old.id, old.title, old.content, old.source, old.path);
        END;

        CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON docs BEGIN
          INSERT INTO docs_fts(docs_fts, rowid, title, content, source, path)
          VALUES('delete', old.id, old.title, old.content, old.source, old.path);
          INSERT INTO docs_fts(rowid, title, content, source, path)
          VALUES (new.id, new.title, new.content, new.source, new.path);
        END;
        """
    )
    conn.commit()


def _sha256(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def upsert_doc(
    conn: sqlite3.Connection,
    *,
    source: str,
    path: str,
    title: Optional[str],
    created_at: Optional[str],
    content: str,
) -> None:
    sha = _sha256(content)
    ingested_at = dt.datetime.now(dt.timezone.utc).isoformat()

    row = conn.execute(
        "SELECT id, sha256 FROM docs WHERE source=? AND path=?",
        (source, path),
    ).fetchone()

    if row and row[1] == sha:
        return

    if row:
        conn.execute(
            """
            UPDATE docs
            SET title=?, created_at=?, content=?, sha256=?, ingested_at=?
            WHERE id=?
            """,
            (title, created_at, content, sha, ingested_at, row[0]),
        )
    else:
        conn.execute(
            """
            INSERT INTO docs(source, path, title, created_at, content, sha256, ingested_at)
            VALUES(?,?,?,?,?,?,?)
            """,
            (source, path, title, created_at, content, sha, ingested_at),
        )


# ---------------------- ChatGPT ingest ----------------------

def ingest_chatgpt_html(path: Path) -> Iterable[dict]:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")

    # Best-effort parsing: ChatGPT exports can change structure.
    # We aim to extract readable text with a title derived from the file path.
    text = soup.get_text("\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    yield {
        "title": f"ChatGPT export: {path.name}",
        "created_at": None,
        "content": text,
    }


def ingest_chatgpt_conversations_json(path: Path) -> Iterable[dict]:
    data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))

    # Supports both list and dict-ish exports.
    if isinstance(data, dict) and "conversations" in data:
        convs = data["conversations"]
    else:
        convs = data

    for c in convs if isinstance(convs, list) else []:
        title = c.get("title") or "ChatGPT conversation"
        created = c.get("create_time") or c.get("created_at")
        created_at = None
        if created is not None:
            try:
                created_at = dt.datetime.fromtimestamp(created, tz=dt.timezone.utc).isoformat()
            except Exception:
                try:
                    created_at = dtparser.parse(str(created)).astimezone(dt.timezone.utc).isoformat()
                except Exception:
                    created_at = None

        # Pull messages in a readable linear form.
        parts = []
        mapping = c.get("mapping") or {}
        for _, node in mapping.items():
            msg = (node or {}).get("message") or {}
            if not msg:
                continue
            role = ((msg.get("author") or {}).get("role") or "").strip() or "unknown"
            content = (msg.get("content") or {}).get("parts")
            if isinstance(content, list):
                body = "\n".join(str(p) for p in content)
            else:
                body = str(content) if content is not None else ""
            body = body.strip()
            if body:
                parts.append(f"[{role}] {body}")

        yield {
            "title": title,
            "created_at": created_at,
            "content": "\n\n".join(parts).strip(),
        }


def ingest_chatgpt(conn: sqlite3.Connection) -> int:
    base = VAULT_DIR / "chatgpt"
    if not base.exists():
        return 0

    n = 0
    for p in base.rglob("*"):
        if not p.is_file():
            continue

        if p.name.lower().endswith(".html"):
            for doc in ingest_chatgpt_html(p):
                upsert_doc(
                    conn,
                    source="chatgpt",
                    path=str(p),
                    title=doc.get("title"),
                    created_at=doc.get("created_at"),
                    content=doc.get("content") or "",
                )
                n += 1

        if p.name.lower().endswith(".json") and "conversation" in p.name.lower():
            for doc in ingest_chatgpt_conversations_json(p):
                upsert_doc(
                    conn,
                    source="chatgpt",
                    path=str(p),
                    title=doc.get("title"),
                    created_at=doc.get("created_at"),
                    content=doc.get("content") or "",
                )
                n += 1

    conn.commit()
    return n


# ---------------------- Perplexity ingest ----------------------

def ingest_perplexity_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    title = None

    # First heading as title if present.
    m = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    if m:
        title = m.group(1).strip()

    return {
        "title": title or f"Perplexity export: {path.name}",
        "created_at": None,
        "content": text.strip(),
    }


def ingest_perplexity(conn: sqlite3.Connection) -> int:
    base = VAULT_DIR / "perplexity"
    if not base.exists():
        return 0

    n = 0
    for p in base.rglob("*"):
        if not p.is_file():
            continue

        if p.suffix.lower() in {".md", ".txt"}:
            doc = ingest_perplexity_markdown(p)
            upsert_doc(
                conn,
                source="perplexity",
                path=str(p),
                title=doc.get("title"),
                created_at=doc.get("created_at"),
                content=doc.get("content") or "",
            )
            n += 1

    conn.commit()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--init-only", action="store_true")
    args = ap.parse_args()

    conn = _db()
    init_schema(conn)
    if args.init_only:
        return

    n1 = ingest_chatgpt(conn)
    n2 = ingest_perplexity(conn)
    print(json.dumps({"db": str(DB_PATH), "ingested": {"chatgpt": n1, "perplexity": n2}}, indent=2))


if __name__ == "__main__":
    main()
