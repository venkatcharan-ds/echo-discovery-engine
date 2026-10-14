"""Evidence records used by ECHO research reports."""
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    claim: str
    source_url: str
    retrieved_at: str
    evidence_type: str = "verified_fact"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EvidenceCollector:
    """Collect source-attributed observations; interpretations are not facts."""

    def __init__(self, retrieved_at: str):
        self.retrieved_at = retrieved_at
        self.items: list[EvidenceItem] = []

    def add(self, claim: str, source_url: str, evidence_type: str = "verified_fact") -> str:
        item_id = f"E{len(self.items) + 1:03d}"
        self.items.append(EvidenceItem(item_id, claim, source_url, self.retrieved_at, evidence_type))
        return item_id
