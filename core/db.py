"""
db.py -- Database connection abstraction for UTETY Chat.

PostgreSQL-only. All data lives in Postgres (same cluster as Willow).
Requires WILLOW_DB_URL=postgresql://... in the environment.
All code calls get_connection() -- never sqlite3.connect() directly.

Schema layout:
  Willow knowledge data: <user_schema>.knowledge, <user_schema>.knowledge_entities, etc.
  UTETY Chat own tables: utety_chat schema (created on first use if needed)
"""
import os
import re as _re
import threading

DATABASE_URL    = os.getenv("WILLOW_DB_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "WILLOW_DB_URL is not set. Set it to postgresql://user:pass@host:port/db"
    )
WILLOW_USERNAME = os.getenv("WILLOW_USERNAME", "Sweet-Pea-Rudi19")  # Willow user schema

_pg_pool      = None
_pg_pool_lock = threading.Lock()


def _get_pg_pool():
    global _pg_pool
    if _pg_pool is not None:
        return _pg_pool
    with _pg_pool_lock:
        if _pg_pool is None:
            try:
                import psycopg2.pool
                _pg_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2, maxconn=20, dsn=DATABASE_URL
                )
            except ImportError:
                raise RuntimeError(
                    "psycopg2 not installed. Run: pip install psycopg2-binary"
                )
    return _pg_pool


class _PgCursor:
    """Wraps psycopg2 cursor to provide a sqlite3-compatible interface."""

    def __init__(self, cur):
        self._cur       = cur
        self.description = cur.description
        self.rowcount    = cur.rowcount
        self.lastrowid   = None

    def __getattr__(self, name):
        return getattr(self._cur, name)

    def execute(self, sql, params=None):
        self._cur.execute(sql, params)
        self.description = self._cur.description
        self.rowcount    = self._cur.rowcount
        return self

    def executemany(self, sql, seq):
        import psycopg2.extras
        psycopg2.extras.execute_batch(self._cur, sql, seq)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    def fetchmany(self, n):
        return self._cur.fetchmany(n)

    def __iter__(self):
        return iter(self._cur)


class _PgConn:
    """Wraps a pooled psycopg2 connection."""

    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def cursor(self):
        import psycopg2.extras
        return _PgCursor(
            self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        )

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def close(self):
        try:
            self._conn.rollback()
        except Exception:
            pass
        self._pool.putconn(self._conn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        try:
            self._conn.rollback()
        except Exception:
            pass
        self._pool.putconn(self._conn)


def _safe_schema_name(name: str) -> str:
    """Convert a username to a safe PostgreSQL schema name (lowercase, underscores)."""
    s = _re.sub(r"[^a-z0-9]", "_", name.lower())
    return s[:63]


def get_willow_schema(username: str = None) -> str:
    """Return the Postgres schema name for a given Willow username."""
    return _safe_schema_name(username or WILLOW_USERNAME)


def get_connection(schema: str = None):
    """Return a pooled Postgres connection scoped to UTETY Chat's own schema.

    schema: if set, SET search_path = {schema}, public after connecting.
            Defaults to utety_chat.
    """
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = False
        pg_conn = _PgConn(pool, conn)
        safe = _safe_schema_name(schema or "utety_chat")
        cur  = conn.cursor()
        cur.execute(f"SET search_path = {safe}, public")
        cur.close()
        return pg_conn
    except Exception:
        pool.putconn(conn)
        raise


def get_willow_connection(username: str = None):
    """Return a connection with search_path set to the Willow user's knowledge schema."""
    schema = get_willow_schema(username)
    pool   = _get_pg_pool()
    conn   = pool.getconn()
    try:
        conn.autocommit = False
        pg_conn = _PgConn(pool, conn)
        cur = conn.cursor()
        cur.execute(f"SET search_path = {schema}, public")
        cur.close()
        return pg_conn
    except Exception:
        pool.putconn(conn)
        raise


def init_schema(schema_name: str = "utety_chat") -> str:
    """Create a PostgreSQL schema if it does not exist. Returns the safe schema name."""
    safe = _safe_schema_name(schema_name)
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {safe}")
        cur.close()
    finally:
        pool.putconn(conn)
    return safe
