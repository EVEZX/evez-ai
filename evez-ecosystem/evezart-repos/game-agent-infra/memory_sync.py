#!/usr/bin/env python3
"""
Memory Sync - Saves to both MEMORY.md and mem0 (SQLite)
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

MEM0_DB = "/root/.openclaw/memory/main.sqlite"
MEMORY_MD = "/root/.openclaw/workspace/MEMORY.md"

def save_memory(key: str, value: str, source: str = "system"):
    """Save to both mem0 SQLite and MEMORY.md"""
    
    # 1. Save to mem0 SQLite
    try:
        conn = sqlite3.connect(MEM0_DB)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                source TEXT,
                timestamp TEXT
            )
        """)
        
        cursor.execute(
            "INSERT INTO memories (key, value, source, timestamp) VALUES (?, ?, ?, ?)",
            (key, value, source, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        mem0_status = "✅ mem0"
    except Exception as e:
        mem0_status = f"❌ mem0 error: {e}"
    
    # 2. Save to MEMORY.md
    try:
        md_path = Path(MEMORY_MD)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"\n- **{timestamp}** [{source}] {key}: {value}\n"
        
        if md_path.exists():
            content = md_path.read_text()
        else:
            content = "# MEMORY.md\n\n"
        
        md_path.write_text(content + entry)
        md_status = "✅ MEMORY.md"
    except Exception as e:
        md_status = f"❌ MEMORY.md error: {e}"
    
    return f"{mem0_status} | {md_status}"


if __name__ == "__main__":
    result = save_memory("test", "This is a test memory", "system")
    print(result)