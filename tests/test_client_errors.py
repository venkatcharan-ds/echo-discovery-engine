import responses

from echo_discovery.github_client import GitHubAPIError, GitHubClient


@responses.activate
def test_http_error_is_reported():
    responses.add(responses.GET, "https://api.github.com/search/repositories",
                  json={"message": "bad credentials"}, status=401)
    client = GitHubClient(max_retries=0)
    try:
        client.search_repositories("language:Python")
        assert False, "expected GitHubAPIError"
    except GitHubAPIError as exc:
        assert "401" in str(exc)


@responses.activate
def test_invalid_payload_is_reported():
    responses.add(responses.GET, "https://api.github.com/search/repositories",
                  json={"message": "unexpected"}, status=200)
    client = GitHubClient(max_retries=0)
    try:
        client.search_repositories("language:Python")
        assert False, "expected GitHubAPIError"
    except GitHubAPIError as exc:
        assert "items" in str(exc)
