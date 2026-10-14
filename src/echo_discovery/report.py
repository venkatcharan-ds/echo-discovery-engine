"""Build transparent research reports from source-backed GitHub observations."""
from __future__ import annotations

import re
from typing import Any, Iterable

from .evidence import EvidenceItem


def _readme_signals(text: str) -> list[str]:
    signals: list[str] = []
    if not text.strip():
        return signals
    headings = re.findall(r"(?m)^#{1,3}\s+(.+?)\s*$", text)
    if headings:
        signals.append("README contains these headings: " + ", ".join(headings[:12]))
    for label, pattern in (
        ("installation instructions", r"(?i)\b(install|installation|getting started)\b"),
        ("usage examples", r"(?i)\b(usage|quick start|example)\b"),
        ("testing guidance", r"(?i)\b(testing|pytest|unittest|tests)\b"),
        ("contribution guidance", r"(?i)\b(contribut(e|ing|ions))\b"),
    ):
        if re.search(pattern, text):
            signals.append(f"README text appears to mention {label}.")
    return signals


def build_research_report(*, repository: dict[str, Any], readme_text: str,
                          releases: list[dict[str, Any]], issues: list[dict[str, Any]],
                          commits: list[dict[str, Any]], evidence: Iterable[EvidenceItem],
                          researched_at: str) -> dict[str, Any]:
    evidence_rows = [item.to_dict() for item in evidence]
    evidence_ids = [item["id"] for item in evidence_rows]
    repo_url = repository.get("html_url") or ""
    name = repository.get("full_name") or repo_url.rstrip("/").split("/")[-2:]
    if isinstance(name, list):
        name = "/".join(name)
    readme_signals = _readme_signals(readme_text)
    language = repository.get("language")
    stars = int(repository.get("stargazers_count") or 0)
    open_issues = sum(1 for item in issues if item.get("state") == "open")

    modernization: list[dict[str, Any]] = []
    if not readme_text.strip():
        modernization.append({
            "opportunity": "Create or restore a project README",
            "rationale": "The README endpoint did not provide readable content during this investigation.",
            "evidence_ids": [item["id"] for item in evidence_rows if "README" in item["claim"]],
            "confidence": "medium",
            "validation_steps": ["Check whether documentation exists in another branch or project site",
                                 "Document installation, usage, support status, and contribution steps"],
        })
    elif not any("usage examples" in signal.lower() for signal in readme_signals):
        modernization.append({
            "opportunity": "Evaluate whether a concise quick-start example is needed",
            "rationale": "The fetched README text did not match common usage-example markers; this heuristic can miss other wording.",
            "evidence_ids": [],
            "confidence": "low",
            "validation_steps": ["Review the README manually", "Ask a maintainer or user to validate the onboarding path"],
        })
    if not releases:
        modernization.append({
            "opportunity": "Assess whether tagged releases and a changelog would improve adoption",
            "rationale": "No release records were returned by the public GitHub releases endpoint; tags may exist separately.",
            "evidence_ids": [item["id"] for item in evidence_rows if "releases endpoint" in item["claim"]],
            "confidence": "low",
            "validation_steps": ["Check tags and package registries", "Confirm whether the project needs formal release management"],
        })
    if not any("testing guidance" in signal.lower() for signal in readme_signals):
        modernization.append({
            "opportunity": "Check automated test coverage and CI status",
            "rationale": "The fetched README did not match common testing-guidance markers; this does not establish that tests or CI are absent.",
            "evidence_ids": [],
            "confidence": "low",
            "validation_steps": ["Inspect repository test files and workflow configuration", "Run tests only in a controlled sandbox with maintainer permission"],
        })

    hypotheses = [{
        "hypothesis": "A focused documentation and maintenance review may reveal low-risk ways to improve contributor onboarding.",
        "rationale": "Documentation and public repository metadata provide an initial basis for review, but do not prove that the project needs revival.",
        "supporting_evidence_ids": evidence_ids[:min(3, len(evidence_ids))],
        "counter_evidence": ["A quiet repository may be complete, intentionally stable, or maintained elsewhere."],
        "confidence": "low",
        "validation_steps": ["Review open issues and recent history", "Check project website, package registry, and successor repositories", "Ask maintainers or users about current needs"],
    }]

    summary = repository.get("description") or "GitHub did not provide a repository description."
    return {
        "schema_version": "1.0",
        "research_timestamp": researched_at,
        "repository": {
            "full_name": name,
            "url": repo_url,
            "description": summary,
            "created_at": repository.get("created_at"),
            "updated_at": repository.get("updated_at"),
            "pushed_at": repository.get("pushed_at"),
            "stars": stars,
            "forks": int(repository.get("forks_count") or 0),
            "open_issues_count_reported_by_github": int(repository.get("open_issues_count") or 0),
            "language": language,
            "topics": repository.get("topics") or [],
            "license": (repository.get("license") or {}).get("spdx_id") if isinstance(repository.get("license"), dict) else None,
        },
        "historical_activity": {
            "latest_fetched_commit_date": ((commits[0].get("commit") or {}).get("committer") or {}).get("date") if commits else None,
            "fetched_commit_count": len(commits),
            "fetched_release_count": len(releases),
            "fetched_issue_count_excluding_pull_requests": len(issues),
            "fetched_open_issue_count": open_issues,
            "interpretation": "These are bounded public API observations, not proof of abandonment or project health.",
        },
        "technical_signals": {
            "primary_language_reported_by_github": language,
            "topics_reported_by_github": repository.get("topics") or [],
            "readme_signals": readme_signals,
            "note": "Language and README text are weak signals; dependencies and architecture have not been independently verified.",
        },
        "limitations_and_unknowns": [
            "Investigation uses public GitHub API data and bounded pagination; older records may not be included.",
            "A missing release or README endpoint result does not prove no tags or documentation exist elsewhere.",
            "No code was cloned, installed, built, or executed.",
            "Novelty, maintainer intent, security, dependency health, user demand, and revival feasibility remain unverified.",
        ],
        "modernization_opportunities": modernization,
        "revival_hypotheses": hypotheses,
        "evidence": evidence_rows,
    }
