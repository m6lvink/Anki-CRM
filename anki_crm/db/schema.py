from __future__ import annotations
from typing import Protocol, Any


class DBProtocol(Protocol):
    """Matches Anki's public DBProxy API. Also implemented by SQLiteAdapter for tests."""

    def execute(self, sql: str, *args: Any) -> Any: ...
    def all(self, sql: str, *args: Any) -> list: ...
    def first(self, sql: str, *args: Any) -> tuple | None: ...
    def scalar(self, sql: str, *args: Any) -> Any: ...


class SQLiteAdapter:
    """Wraps sqlite3.Connection to match DBProtocol. Used in tests ONLY."""

    def __init__(self, conn) -> None:
        self._conn = conn
        self._lastrowid: int = 0

    def execute(self, sql: str, *args: Any) -> Any:
        cur = self._conn.execute(sql, args)
        self._lastrowid = cur.lastrowid
        self._conn.commit()
        return cur

    def all(self, sql: str, *args: Any) -> list:
        return self._conn.execute(sql, args).fetchall()

    def first(self, sql: str, *args: Any) -> tuple | None:
        return self._conn.execute(sql, args).fetchone()

    def scalar(self, sql: str, *args: Any) -> Any:
        row = self._conn.execute(sql, args).fetchone()
        return row[0] if row else None

    @property
    def lastrowid(self) -> int:
        return self._lastrowid


CRM_ENTITIES_DDL = """
CREATE TABLE IF NOT EXISTS crm_entities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    entity_type  TEXT    NOT NULL CHECK(entity_type IN ('stakeholder','project')),
    metadata_json TEXT   NOT NULL DEFAULT '{}',
    created_at   TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL,
    UNIQUE(name, entity_type)
)
"""

CRM_LINKS_DDL = """
CREATE TABLE IF NOT EXISTS crm_links (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id     INTEGER NOT NULL,
    entity_id   INTEGER NOT NULL REFERENCES crm_entities(id) ON DELETE CASCADE,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','utc')),
    UNIQUE(card_id, entity_id)
)
"""

CRM_REVIEW_SESSIONS_DDL = """
CREATE TABLE IF NOT EXISTS crm_review_sessions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id        INTEGER NOT NULL,
    entity_ids_json TEXT   NOT NULL DEFAULT '[]',
    started_at     TEXT   NOT NULL,
    duration_ms    INTEGER NOT NULL DEFAULT 0
)
"""

CRM_ENTITIES_IDX = "CREATE INDEX IF NOT EXISTS idx_crm_entities_type ON crm_entities(entity_type)"
CRM_LINKS_CARD_IDX = "CREATE INDEX IF NOT EXISTS idx_crm_links_card ON crm_links(card_id)"
CRM_LINKS_ENTITY_IDX = "CREATE INDEX IF NOT EXISTS idx_crm_links_entity ON crm_links(entity_id)"
CRM_SESSIONS_CARD_IDX = "CREATE INDEX IF NOT EXISTS idx_crm_sessions_card ON crm_review_sessions(card_id)"


def ensure_schema(db: DBProtocol) -> None:
    """Idempotent schema init. Accepts Anki's mw.col.db directly OR a SQLiteAdapter."""
    for ddl in (
        CRM_ENTITIES_DDL,
        CRM_LINKS_DDL,
        CRM_REVIEW_SESSIONS_DDL,
        CRM_ENTITIES_IDX,
        CRM_LINKS_CARD_IDX,
        CRM_LINKS_ENTITY_IDX,
        CRM_SESSIONS_CARD_IDX,
    ):
        db.execute(ddl)


class AnkiDBAdapter:
    """Adapts Anki's DBProxy to match our DBProtocol. Used in production ONLY."""

    def __init__(self, anki_db) -> None:
        self._db = anki_db

    def execute(self, sql: str, *args: Any) -> None:
        self._db.execute(sql, *args)

    def all(self, sql: str, *args: Any) -> list:
        return self._db.all(sql, *args)

    def first(self, sql: str, *args: Any) -> tuple | None:
        return self._db.first(sql, *args)

    def scalar(self, sql: str, *args: Any) -> Any:
        return self._db.scalar(sql, *args)
