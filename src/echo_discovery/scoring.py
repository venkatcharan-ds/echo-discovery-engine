"""Deterministic candidate-ranking heuristics; not a verdict about project quality."""
from datetime import datetime, timezone
from typing import Any


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def score_candidate(repo: dict[str, Any], now: datetime | None = None) -> tuple[float, int | None]:
    """Return (0-100 heuristic score, inactive days).

    The score prioritizes inactivity and modest community interest. It does not
    estimate whether an idea is novel, safe, useful, or technically revivable.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    pushed = parse_datetime(repo.get("pushed_at"))
    created = parse_datetime(repo.get("created_at"))
    inactive_days = max(0, (now - pushed).days) if pushed else None

    inactivity = min((inactive_days or 0) / 1095, 1) * 45
    stars = max(0, int(repo.get("stargazers_count") or 0))
    community = min(stars / 1000, 1) * 25
    age_days = max(0, (now - created).days) if created else 0
    maturity = min(age_days / 1095, 1) * 15
    completeness = sum(bool(repo.get(k)) for k in (
        "description", "html_url", "created_at", "pushed_at", "language"
    )) / 5 * 15

    return round(inactivity + community + maturity + completeness, 2), inactive_days
