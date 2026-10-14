"""Research API client helper."""
from .github_client import GitHubClient

class ResearchGitHubClient(GitHubClient):
    def get_json(self, url, params=None):
        raise NotImplementedError("Research API transport is not configured")
