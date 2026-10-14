from datetime import datetime, timezone

from echo_discovery.scoring import score_candidate


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_score_is_deterministic_and_bounded():
    repo = {
        "pushed_at": "2020-01-01T00:00:00Z",
        "created_at": "2018-01-01T00:00:00Z",
        "stargazers_count": 500,
        "description": "A useful tool",
        "html_url": "https://github.com/example/tool",
        "language": "Python",
    }
    first = score_candidate(repo, now=NOW)
    assert first == score_candidate(repo, now=NOW)
    assert 0 <= first[0] <= 100
    assert first[1] is not None and first[1] > 1000


def test_missing_dates_are_handled():
    score, inactive_days = score_candidate({"stargazers_count": 0}, now=NOW)
    assert score >= 0
    assert inactive_days is None
