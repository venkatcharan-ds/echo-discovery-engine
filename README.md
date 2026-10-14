# ECHO Discovery Engine

ECHO is the first milestone of an agent that discovers potentially overlooked open-source software projects and prepares them for deeper research. This milestone is a deterministic GitHub discovery tool, **not yet an LLM agent**.

## What it does

- Searches public GitHub repositories using configurable search filters.
- Collects repository metadata and filters forks and archived projects.
- Ranks candidates with a deterministic heuristic based on inactivity, stars, age, and metadata completeness.
- Writes structured JSON results.
- Uses mocked API responses for offline tests.

The score is only a discovery heuristic. Inactivity does not prove abandonment, and stars or metadata completeness do not prove novelty, usefulness, safety, or revival potential.

## Requirements

- Python 3.11 or newer
- Internet access to query the GitHub REST API
- Optional: a GitHub personal access token in `GITHUB_TOKEN` to increase API limits. Never commit tokens.

## Windows PowerShell setup

```powershell
git clone https://github.com/venkatcharan-ds/echo-discovery-engine.git
cd echo-discovery-engine
git switch milestone-1
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

If PowerShell blocks virtual-environment activation, run this in the current terminal and retry activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Run a discovery search

```powershell
echo-discover --query "language:Python stars:>=50" --min-stars 50 --inactive-days 365 --max-pages 2 --output outputs/candidates.json
```

Alternatively:

```powershell
python -m echo_discovery.cli --query "language:Python stars:>=50" --max-pages 2
```

The default output path is `outputs/candidates.json`. Use `--include-archived` or `--include-forks` to change filtering. Search query syntax follows GitHub repository search syntax.

## Run tests (no network required)

```powershell
pytest -q
```

The HTTP client tests use mocked responses. The tests do not query GitHub.

## Configuration example

See [examples/config.json](examples/config.json) for documented starting values. The current CLI accepts its primary options as flags; the example is a reference configuration for future configuration-file support.

## Project layout

```text
src/echo_discovery/
  github_client.py
  models.py
  search.py
  scoring.py
  cli.py
tests/
examples/config.json
.github/workflows/tests.yml
```

## Limitations and safety

- GitHub search indexes only public repositories visible to the API and is subject to API limits.
- The search query and ranking are heuristic and can miss relevant projects.
- The configured inactivity period is a search hint, not a definitive classification; inspect repository history before conclusions.
- The score does not currently evaluate novelty or revival feasibility.
- ECHO does not clone, install, or execute candidate repositories.
- Milestone 2 will add evidence-backed research; experiment execution will require a separate sandbox design and explicit safety controls.

## Roadmap

1. Discovery engine (this milestone)
2. Research agent with sourced claims and candidate investigation
3. Revival hypothesis generation and prior-art checks
4. Sandboxed, reproducible experiments
5. Dashboard and historical memory
