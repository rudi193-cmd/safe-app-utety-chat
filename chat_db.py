"""
chat_db.py -- UTETY faculty chat database using the 23-cubed lattice structure.

PostgreSQL-only. Schema: utety_chat.
Each entity maps into a 23x23x23 lattice (12,167 cells per entity).

Lattice constants imported from Willow's user_lattice.py.
DB connection follows Willow's core/db.py pattern (psycopg2, pooled).
"""

import os
import sys
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

# Import 23-cubed lattice constants from Willow
sys.path.insert(0, "/mnt/c/Users/Sean/Documents/GitHub/Willow/core")
from user_lattice import DOMAINS, TEMPORAL_STATES, DEPTH_MIN, DEPTH_MAX, LATTICE_SIZE

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

_pool = None
_pool_lock = threading.Lock()

SCHEMA = "utety_chat"

VALID_ROLES = frozenset({"user", "assistant", "system"})


def _resolve_host() -> str:
    """Return localhost, falling back to WSL resolv.conf nameserver."""
    host = "localhost"
    try:
        with open("/etc/resolv.conf") as f:
            for line in f:
                if line.strip().startswith("nameserver"):
                    host = line.strip().split()[1]
                    break
    except FileNotFoundError:
        pass
    return host


def _get_pool():
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is None:
            import psycopg2.pool
            dsn = os.getenv("WILLOW_DB_URL", "")
            if not dsn:
                host = _resolve_host()
                dsn = f"dbname=willow user=willow host={host}"
            _pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=10, dsn=dsn)
    return _pool


def get_connection():
    """Return a pooled Postgres connection with search_path = utety_chat, public."""
    pool = _get_pool()
    conn = pool.getconn()
    try:
        conn.autocommit = False
        cur = conn.cursor()
        cur.execute(f"SET search_path = {SCHEMA}, public")
        cur.close()
        return conn
    except Exception:
        pool.putconn(conn)
        raise


def release_connection(conn):
    """Return a connection to the pool."""
    try:
        conn.rollback()
    except Exception:
        pass
    _get_pool().putconn(conn)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _validate_lattice(domain: str, depth: int, temporal: str):
    if domain not in DOMAINS:
        raise ValueError(f"Invalid domain '{domain}'. Must be one of: {DOMAINS}")
    if not (DEPTH_MIN <= depth <= DEPTH_MAX):
        raise ValueError(f"Invalid depth {depth}. Must be {DEPTH_MIN}-{DEPTH_MAX}")
    if temporal not in TEMPORAL_STATES:
        raise ValueError(f"Invalid temporal '{temporal}'. Must be one of: {TEMPORAL_STATES}")


# ---------------------------------------------------------------------------
# Schema init
# ---------------------------------------------------------------------------

def init_schema(conn):
    """Create the utety_chat schema and all tables. Idempotent."""
    cur = conn.cursor()

    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    cur.execute(f"SET search_path = {SCHEMA}, public")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            faculty_member  TEXT NOT NULL,
            session_title   TEXT,
            started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at        TIMESTAMP,
            was_exported    BOOLEAN DEFAULT FALSE,
            message_count   INTEGER DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            session_id      BIGINT NOT NULL REFERENCES chat_sessions(id),
            sender          TEXT NOT NULL,
            role            TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
            content         TEXT NOT NULL,
            tokens_used     INTEGER,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS lattice_cells (
            id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            entity_id       BIGINT NOT NULL,
            entity_type     TEXT NOT NULL CHECK (entity_type IN ('session','message')),
            domain          TEXT NOT NULL,
            depth           INTEGER NOT NULL CHECK (depth >= 1 AND depth <= 23),
            temporal        TEXT NOT NULL,
            content         TEXT NOT NULL,
            source          TEXT,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_sensitive    BOOLEAN DEFAULT FALSE,
            UNIQUE(entity_id, entity_type, domain, depth, temporal)
        )
    """)

    # Indices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_faculty ON chat_sessions (faculty_member)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_exported ON chat_sessions (was_exported)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages (session_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_sender ON chat_messages (sender)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_messages_role ON chat_messages (role)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lc_entity ON lattice_cells (entity_id, entity_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lc_domain ON lattice_cells (domain)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lc_temporal ON lattice_cells (temporal)")

    conn.commit()


# ---------------------------------------------------------------------------
# CRUD -- all return new dicts (immutable pattern)
# ---------------------------------------------------------------------------

def add_session(conn, *, faculty_member: str, session_title: str = None) -> Dict[str, Any]:
    """Create a new chat session. Returns a dict with the new row (including id)."""
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_sessions (faculty_member, session_title)
        VALUES (%s, %s)
        RETURNING id, faculty_member, session_title, started_at, ended_at,
                  was_exported, message_count, created_at
    """, (faculty_member, session_title))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]
    conn.commit()
    return dict(zip(cols, row))


def add_message(conn, *, session_id: int, sender: str, role: str, content: str,
                tokens_used: int = None) -> Dict[str, Any]:
    """Insert a chat message and increment session message_count. Returns the new row as a dict."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO chat_messages (session_id, sender, role, content, tokens_used)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, session_id, sender, role, content, tokens_used, created_at
    """, (session_id, sender, role, content, tokens_used))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]

    cur.execute("""
        UPDATE chat_sessions SET message_count = message_count + 1
        WHERE id = %s
    """, (session_id,))

    conn.commit()
    return dict(zip(cols, row))


def place_in_lattice(conn, entity_id: int, entity_type: str, domain: str, depth: int,
                     temporal: str, content: str, source: str = None,
                     is_sensitive: bool = False) -> Dict[str, Any]:
    """Map an entity to a lattice cell. Upserts on (entity_id, entity_type, domain, depth, temporal).
    Returns the cell row as a dict."""
    if entity_type not in ("session", "message"):
        raise ValueError(f"Invalid entity_type '{entity_type}'. Must be 'session' or 'message'")
    _validate_lattice(domain, depth, temporal)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO lattice_cells (entity_id, entity_type, domain, depth, temporal, content, source, is_sensitive)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (entity_id, entity_type, domain, depth, temporal)
        DO UPDATE SET content = EXCLUDED.content, source = EXCLUDED.source, is_sensitive = EXCLUDED.is_sensitive
        RETURNING id, entity_id, entity_type, domain, depth, temporal, content, source, created_at, is_sensitive
    """, (entity_id, entity_type, domain, depth, temporal, content, source, is_sensitive))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]
    conn.commit()
    return dict(zip(cols, row))


def get_session_transcript(conn, session_id: int) -> Dict[str, Any]:
    """Return a session with all its messages, oldest first. Immutable result."""
    cur = conn.cursor()

    cur.execute("SELECT * FROM chat_sessions WHERE id = %s", (session_id,))
    session_row = cur.fetchone()
    if session_row is None:
        return {"session": None, "messages": []}
    scols = [d[0] for d in cur.description]
    session = dict(zip(scols, session_row))

    cur.execute("""
        SELECT * FROM chat_messages
        WHERE session_id = %s
        ORDER BY created_at ASC
    """, (session_id,))
    rows = cur.fetchall()
    mcols = [d[0] for d in cur.description]
    messages = [dict(zip(mcols, r)) for r in rows]

    return {"session": session, "messages": messages}


def search_sessions(conn, query: str, faculty_member: str = None) -> List[Dict[str, Any]]:
    """Search sessions by title or message content (case-insensitive ILIKE).
    Optionally filter by faculty_member. Returns list of session dicts."""
    cur = conn.cursor()
    if faculty_member is not None:
        cur.execute("""
            SELECT DISTINCT s.* FROM chat_sessions s
            LEFT JOIN chat_messages m ON m.session_id = s.id
            WHERE (s.session_title ILIKE %s OR m.content ILIKE %s)
              AND s.faculty_member = %s
            ORDER BY s.started_at DESC
        """, (f"%{query}%", f"%{query}%", faculty_member))
    else:
        cur.execute("""
            SELECT DISTINCT s.* FROM chat_sessions s
            LEFT JOIN chat_messages m ON m.session_id = s.id
            WHERE s.session_title ILIKE %s OR m.content ILIKE %s
            ORDER BY s.started_at DESC
        """, (f"%{query}%", f"%{query}%"))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


def get_faculty_stats(conn, faculty_member: str) -> Dict[str, Any]:
    """Return aggregate stats for a faculty member. Immutable result."""
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) AS total_sessions,
               COALESCE(SUM(message_count), 0) AS total_messages,
               COUNT(*) FILTER (WHERE was_exported) AS exported_sessions,
               MIN(started_at) AS first_session,
               MAX(started_at) AS last_session
        FROM chat_sessions
        WHERE faculty_member = %s
    """, (faculty_member,))
    row = cur.fetchone()
    cols = [d[0] for d in cur.description]
    stats = dict(zip(cols, row))

    cur.execute("""
        SELECT COALESCE(SUM(tokens_used), 0) AS total_tokens
        FROM chat_messages m
        JOIN chat_sessions s ON s.id = m.session_id
        WHERE s.faculty_member = %s
    """, (faculty_member,))
    token_row = cur.fetchone()
    stats["total_tokens"] = token_row[0]

    return stats
