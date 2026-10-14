from datetime import datetime, timezone

from echo_discovery.models import Config
from echo_discovery.search import search_candidates


class FakeClient:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def search_repositories(self, query, page=1, per_page=30):
        self.calls.append((query, page, per_page))
        return {"items": self.pages[page - 1] if page <= len(self.pages) else []}


def repo(name, **overrides):
    item = {
        "full_name": name, "description": "Example project", "stargazers_count": 120,
        "created_at": "2019-01-01T00:00:00Z", "updated_at": "2022-01-01T00:00:00Z",
        "pushed_at": "2021-01-01T00:00:00Z", "language": "Python",
        "license": {"spdx_id": "MIT"}, "html_url": f"https://github.com/{name}",
        "fork": False, "archived": False,
    }
    item.update(overrides)
    return item


def test_search_filters_forks_archives_and_sorts():
    client = FakeClient([[
        repo("org/older", pushed_at="2018-01-01T00:00:00Z"),
        repo("org/fork", fork=True),
        repo("org/archived", archived=True),
        repo("org/recent", pushed_at="2025-12-01T00:00:00Z"),
    ]])
    config = Config(query="language:Python", per_page=10, max_pages=1)
    results = search_candidates(config, client=client,
                                now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert [r.name for r in results] == ["org/older", "org/recent"]
    assert all(not r.is_fork and not r.is_archived for r in results)
    assert results[0].score >= results[1].score
    assert "heuristic" in results[0].score_label


def test_min_stars_is_applied_even_when_query_has_a_different_stars_filter():
    from echo_discovery.search import build_query

    query = build_query(Config(query="language:Python stars:>=50", min_stars=200))
    assert "stars:>=200" in query


def test_duplicate_repositories_are_removed():
    item = repo("org/project")
    client = FakeClient([[item, item]])
    results = search_candidates(Config(query="language:Python", per_page=10, max_pages=1), client=client)
    assert len(results) == 1
