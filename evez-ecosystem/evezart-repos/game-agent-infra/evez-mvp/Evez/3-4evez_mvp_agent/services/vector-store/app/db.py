import os
import psycopg

def pg_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "evez")
    pw   = os.getenv("POSTGRES_PASSWORD", "evez")
    db   = os.getenv("POSTGRES_DB", "evez")
    return f"host={host} port={port} user={user} password={pw} dbname={db}"

def get_conn():
    return psycopg.connect(pg_dsn())
