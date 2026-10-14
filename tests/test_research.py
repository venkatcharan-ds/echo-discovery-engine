import base64
from datetime import datetime, timezone

from echo_discovery.investigator import research_repository


class FakeResearchClient:
    def __init__(self, missing_readme=False):
        self.missing_readme = missing_readme
        self.calls = []

    def get_json(self, url, params=None):
        self.calls.append((url, params))
        if url.endswith("/repos/demo/project"):
            return {
                "full_name": "demo/project",
                "html_url": "https://github.com/demo/project",
                "description": "A demo project",
                "created_at": "2020-01-01T00:00:00Z",
                "updated_at": "2022-01-01T00:00:00Z",
                "pushed_at": "2022-01-01T00:00:00Z",
                "stargazers_count": 25,
                "forks_count": 3,
                "open_issues_count": 1,
                "language": "Python",
                "topics": ["demo"],
                "license": {"spdx_id": "MIT"},
            }
        if url.endswith("/readme"):
            if self.missing_readme:
                from echo_discovery.github_client import GitHubAPIError
                raise GitHubAPIError("GitHub API returned HTTP 404: Not Found")
            return {"content": base64.b64encode(b"# Demo\n\nQuick start example\n").decode()}
        if "/releases" in url or "/issues?" in url or "/commits" in url:
            if "/commits" in url:
                return [{"commit": {"committer": {"date": "2022-01-01T00:00:00Z"}}}]
            return []
        raise AssertionError(f"Unexpected URL: {url}")


def test_research_report_has_evidence_sources_and_timestamp():
    client = FakeResearchClient()
    report = research_repository("demo/project", client=client,
                                 now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert report["repository"]["full_name"] == "demo/project"
    assert report["research_timestamp"] == "2026-01-01T00:00:00Z"
    assert report["evidence"]
    assert all(item["source_url"].startswith("https://github.com/") for item in report["evidence"])
    assert all(item["retrieved_at"] == report["research_timestamp"] for item in report["evidence"])
    assert report["historical_activity"]["fetched_commit_count"] == 1
    assert "abandonment" in report["historical_activity"]["interpretation"]


def test_missing_readme_is_reported_not_fatal():
    report = research_repository("demo/project", client=FakeResearchClient(missing_readme=True))
    assert any("README endpoint returned 404" in item["claim"] for item in report["evidence"])
    assert any(item["opportunity"] == "Create or restore a project README"
               for item in report["modernization_opportunities"])


def test_invalid_repository_name_rejected():
    import pytest
    with pytest.raises(ValueError):
        research_repository("not-a-repository")
