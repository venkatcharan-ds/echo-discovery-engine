"""Research one public repository using GitHub API metadata."""
from datetime import datetime, timezone
from typing import Any
from .evidence import EvidenceCollector
from .github_client import GitHubAPIError, GitHubClient
from .report import build_research_report

API = "https://api.github.com"


def _pages(client: GitHubClient, url: str, max_pages: int = 3) -> list[dict[str, Any]]:
    rows = []
    for page in range(1, max_pages + 1):
        data = client.get_json(url, params={"per_page": 100, "page": page})
        if not isinstance(data, list):
            raise GitHubAPIError(f"Expected list response from {url}")
        rows.extend(item for item in data if isinstance(item, dict))
        if len(data) < 100:
            break
    return rows


def research_repository(full_name: str, client: GitHubClient | None = None, now: datetime | None = None) -> dict[str, Any]:
    parts = full_name.strip().split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Repository must use owner/name format, e.g. pallets/flask")
    root = f"{API}/repos/{parts[0]}/{parts[1]}"
    client = client or GitHubClient()
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence = EvidenceCollector(stamp)
    repo = client.get_json(root)
    if not isinstance(repo, dict) or not repo.get("full_name"):
        raise GitHubAPIError("Repository response is missing full_name")
    url = repo.get("html_url", f"https://github.com/{full_name}")
    readme_text = ""
    try:
        readme = client.get_json(f"{root}/readme")
        import base64
        readme_text = base64.b64decode(readme.get("content", "")).decode("utf-8", errors="replace")
    except GitHubAPIError as exc:
        if "HTTP 404" not in str(exc):
            raise
        evidence.add("GitHub README endpoint returned 404; README was unavailable at research time.", f"{url}/blob/HEAD/README.md")
    evidence.add(f"Repository full name is {repo['full_name']}.", url)
    evidence.add(f"Repository created at {repo.get('created_at') or 'not supplied'}.", url)
    evidence.add(f"Repository last pushed at {repo.get('pushed_at') or 'not supplied'}.", f"{url}/commits")
    evidence.add(f"GitHub reports {int(repo.get('stargazers_count') or 0)} stars.", url)
    evidence.add(f"Primary language reported by GitHub: {repo.get('language') or 'not specified'}.", url)
    if repo.get("topics"):
        evidence.add("GitHub topics: " + ", ".join(repo["topics"]), url)
    releases = _pages(client, f"{root}/releases")
    all_issues = _pages(client, f"{root}/issues?state=all")
    issues = [item for item in all_issues if "pull_request" not in item]
    commits = _pages(client, f"{root}/commits")
    evidence.add(f"Release records fetched: {len(releases)}.", f"{url}/releases")
    evidence.add(f"Issue records fetched excluding pull requests: {len(issues)}.", f"{url}/issues")
    latest = ((commits[0].get("commit") or {}).get("committer") or {}).get("date") if commits else None
    evidence.add(f"Latest commit date in fetched results: {latest or 'no commit date available'}.", f"{url}/commits")
    return build_research_report(repository=repo, readme_text=readme_text, releases=releases, issues=issues, commits=commits, evidence=evidence.items, researched_at=stamp)
