"""Search and normalize repository candidates."""
from datetime import datetime, timedelta, timezone
from typing import Any

from .github_client import GitHubClient
from .models import Config, RepositoryCandidate
from .scoring import score_candidate


def build_query(config: Config) -> str:
    query = config.query.strip()
    # The explicit CLI/config value overrides a stars qualifier in the base query.
    if "stars:" in query:
        start = query.index("stars:")
        end = query.find(" ", start)
        end = len(query) if end < 0 else end
        query = query[:start] + f"stars:>={config.min_stars}" + query[end:]
    else:
        query += f" stars:>={config.min_stars}"
    if "pushed:<" not in query and config.inactive_days:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=config.inactive_days)).date().isoformat()
        query += f" pushed:<{cutoff}"
    if not config.include_archived and "archived:" not in query:
        query += " archived:false"
    return query


def search_candidates(config: Config, client: GitHubClient | None = None,
                      now: datetime | None = None) -> list[RepositoryCandidate]:
    client = client or GitHubClient(timeout=config.timeout_seconds)
    query = build_query(config)
    candidates: list[RepositoryCandidate] = []
    seen: set[str] = set()

    for page in range(1, config.max_pages + 1):
        payload = client.search_repositories(query, page=page, per_page=config.per_page)
        items: list[dict[str, Any]] = payload["items"]
        if not items:
            break
        for repo in items:
            name = repo.get("full_name")
            if not name or name in seen:
                continue
            seen.add(name)
            if config.exclude_forks and repo.get("fork", False):
                continue
            if not config.include_archived and repo.get("archived", False):
                continue
            score, inactive_days = score_candidate(repo, now=now)
            license_data = repo.get("license")
            candidates.append(RepositoryCandidate(
                name=name,
                description=repo.get("description"),
                stars=int(repo.get("stargazers_count") or 0),
                created_at=repo.get("created_at"),
                updated_at=repo.get("updated_at"),
                pushed_at=repo.get("pushed_at"),
                language=repo.get("language"),
                license=license_data.get("spdx_id") if isinstance(license_data, dict) else None,
                url=repo.get("html_url") or "",
                is_fork=bool(repo.get("fork", False)),
                is_archived=bool(repo.get("archived", False)),
                inactive_days=inactive_days,
                score=score,
            ))
        if len(items) < config.per_page:
            break

    return sorted(candidates, key=lambda item: (item.score, item.stars), reverse=True)
