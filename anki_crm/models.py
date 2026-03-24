from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar, FrozenSet

ENTITY_TYPES: FrozenSet[str] = frozenset({"stakeholder", "project"})


@dataclass(frozen=True)
class Entity:
    id: int
    name: str
    entity_type: str
    metadata_json: str = "{}"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def create(cls, name: str, entity_type: str, metadata_json: str = "{}") -> "Entity":
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"entity_type must be one of {ENTITY_TYPES}, got {entity_type!r}")
        now = datetime.now(timezone.utc).isoformat()
        return cls(id=0, name=name, entity_type=entity_type, metadata_json=metadata_json, created_at=now, updated_at=now)


@dataclass(frozen=True)
class Link:
    id: int
    card_id: int
    entity_id: int
    created_at: str = ""


@dataclass(frozen=True)
class ReviewSession:
    id: int
    card_id: int
    entity_ids_json: str
    started_at: str
    duration_ms: int
