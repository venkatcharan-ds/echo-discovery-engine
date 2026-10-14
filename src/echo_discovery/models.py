"""Typed models and configuration for ECHO discovery."""
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Config:
    query: str = "language:Python"
    per_page: int = 30
    max_pages: int = 2
    min_stars: int = 50
    inactive_days: int = 365
    include_archived: bool = False
    exclude_forks: bool = True
    timeout_seconds: float = 15.0

    def __post_init__(self) -> None:
        if not 1 <= self.per_page <= 100:
            raise ValueError("per_page must be between 1 and 100")
        if self.max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if self.min_stars < 0 or self.inactive_days < 0:
            raise ValueError("min_stars and inactive_days cannot be negative")


@dataclass(frozen=True)
class RepositoryCandidate:
    name: str
    description: str | None
    stars: int
    created_at: str | None
    updated_at: str | None
    pushed_at: str | None
    language: str | None
    license: str | None
    url: str
    is_fork: bool
    is_archived: bool
    inactive_days: int | None
    score: float
    score_label: str = "heuristic; not proof of abandonment or revival potential"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
