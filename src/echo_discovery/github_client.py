"""Small GitHub REST API client with bounded retries and clear errors."""
import os
import time
from typing import Any

import requests


class GitHubAPIError(RuntimeError):
    """Raised when GitHub returns an unusable response."""


class GitHubClient:
    def __init__(self, timeout: float = 15.0, max_retries: int = 2, session: requests.Session | None = None):
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.session = session or requests.Session()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ECHO-Discovery-Engine",
        }
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def search_repositories(self, query: str, page: int = 1, per_page: int = 30) -> dict[str, Any]:
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "page": page, "per_page": per_page, "sort": "stars", "order": "desc"}
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout)
            except requests.RequestException as exc:
                if attempt < self.max_retries:
                    time.sleep(min(0.25 * (2 ** attempt), 1.0))
                    continue
                raise GitHubAPIError(f"GitHub request failed: {exc}") from exc

            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                if attempt < self.max_retries:
                    reset = response.headers.get("X-RateLimit-Reset")
                    wait = 1
                    if reset and reset.isdigit():
                        wait = max(1, min(int(reset) - int(time.time()), 5))
                    time.sleep(wait)
                    continue
                raise GitHubAPIError("GitHub API rate limit reached. Set GITHUB_TOKEN or retry later.")

            if response.status_code in (429, 500, 502, 503, 504) and attempt < self.max_retries:
                time.sleep(min(0.25 * (2 ** attempt), 1.0))
                continue
            if not response.ok:
                raise GitHubAPIError(f"GitHub API returned HTTP {response.status_code}: {response.text[:200]}")
            try:
                payload = response.json()
            except ValueError as exc:
                raise GitHubAPIError("GitHub API returned invalid JSON") from exc
            if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                raise GitHubAPIError("GitHub API response is missing the expected 'items' list")
            return payload
        raise GitHubAPIError("GitHub request failed after retries")
