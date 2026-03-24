from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Sequence

from .schema import DBProtocol
from ..models import Entity, Link, ReviewSession, ENTITY_TYPES


class CRMRepository:
    def __init__(self, db: DBProtocol) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Entity CRUD
    # ------------------------------------------------------------------

    def create_entity(self, name: str, entity_type: str, metadata_json: str = "{}") -> Entity:
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"Invalid entity_type: {entity_type!r}")
        now = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            "INSERT INTO crm_entities (name, entity_type, metadata_json, created_at, updated_at)"
            " VALUES (?,?,?,?,?)",
            name, entity_type, metadata_json, now, now,
        )
        row_id = self._db.scalar("SELECT last_insert_rowid()")
        return self._get_entity_by_id(row_id)

    def get_entity(self, entity_id: int) -> Entity | None:
        return self._get_entity_by_id(entity_id)

    def list_entities(self, entity_type: str | None = None) -> list[Entity]:
        if entity_type is not None:
            rows = self._db.all(
                "SELECT id, name, entity_type, metadata_json, created_at, updated_at"
                " FROM crm_entities WHERE entity_type=? ORDER BY name",
                entity_type,
            )
        else:
            rows = self._db.all(
                "SELECT id, name, entity_type, metadata_json, created_at, updated_at"
                " FROM crm_entities ORDER BY entity_type, name"
            )
        return [Entity(*r) for r in rows]

    def update_entity(
        self,
        entity_id: int,
        name: str | None = None,
        metadata_json: str | None = None,
    ) -> Entity:
        existing = self._get_entity_by_id(entity_id)
        if existing is None:
            raise ValueError(f"Entity {entity_id} not found")
        new_name = name if name is not None else existing.name
        new_meta = metadata_json if metadata_json is not None else existing.metadata_json
        now = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            "UPDATE crm_entities SET name=?, metadata_json=?, updated_at=? WHERE id=?",
            new_name, new_meta, now, entity_id,
        )
        return self._get_entity_by_id(entity_id)

    def delete_entity(self, entity_id: int) -> None:
        self._db.execute("DELETE FROM crm_entities WHERE id=?", entity_id)

    # ------------------------------------------------------------------
    # Link CRUD
    # ------------------------------------------------------------------

    def link_card(self, card_id: int, entity_id: int) -> Link:
        self._db.execute(
            "INSERT OR IGNORE INTO crm_links (card_id, entity_id) VALUES (?,?)",
            card_id, entity_id,
        )
        row = self._db.first(
            "SELECT id, card_id, entity_id, created_at FROM crm_links"
            " WHERE card_id=? AND entity_id=?",
            card_id, entity_id,
        )
        return Link(*row)

    def unlink_card(self, card_id: int, entity_id: int) -> None:
        self._db.execute(
            "DELETE FROM crm_links WHERE card_id=? AND entity_id=?",
            card_id, entity_id,
        )

    def get_links_for_card(self, card_id: int) -> list[Entity]:
        rows = self._db.all(
            """SELECT e.id, e.name, e.entity_type, e.metadata_json, e.created_at, e.updated_at
               FROM crm_entities e
               JOIN crm_links l ON l.entity_id = e.id
               WHERE l.card_id = ?
               ORDER BY e.entity_type, e.name""",
            card_id,
        )
        return [Entity(*r) for r in rows]

    def get_cards_for_entity(self, entity_id: int) -> list[int]:
        rows = self._db.all(
            "SELECT card_id FROM crm_links WHERE entity_id=? ORDER BY card_id",
            entity_id,
        )
        return [r[0] for r in rows]

    # ------------------------------------------------------------------
    # ReviewSession
    # ------------------------------------------------------------------

    def record_session(
        self,
        card_id: int,
        entity_ids: list[int],
        duration_ms: int,
    ) -> ReviewSession:
        now = datetime.now(timezone.utc).isoformat()
        entity_ids_json = json.dumps(entity_ids)
        self._db.execute(
            "INSERT INTO crm_review_sessions (card_id, entity_ids_json, started_at, duration_ms)"
            " VALUES (?,?,?,?)",
            card_id, entity_ids_json, now, duration_ms,
        )
        row_id = self._db.scalar("SELECT last_insert_rowid()")
        row = self._db.first(
            "SELECT id, card_id, entity_ids_json, started_at, duration_ms"
            " FROM crm_review_sessions WHERE id=?",
            row_id,
        )
        return ReviewSession(*row)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_entity_by_id(self, entity_id: int) -> Entity | None:
        row = self._db.first(
            "SELECT id, name, entity_type, metadata_json, created_at, updated_at"
            " FROM crm_entities WHERE id=?",
            entity_id,
        )
        return Entity(*row) if row else None
