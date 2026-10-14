"""Command-line interface for ECHO discovery."""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .github_client import GitHubAPIError
from .models import Config
from .search import search_candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover potentially overlooked GitHub projects.")
    parser.add_argument("--query", default="language:Python stars:>=50")
    parser.add_argument("--min-stars", type=int, default=50)
    parser.add_argument("--inactive-days", type=int, default=365)
    parser.add_argument("--per-page", type=int, default=30)
    parser.add_argument("--max-pages", type=int, default=2)
    parser.add_argument("--include-archived", action="store_true")
    parser.add_argument("--include-forks", action="store_true")
    parser.add_argument("--output", default="outputs/candidates.json")
    args = parser.parse_args()

    try:
        config = Config(
            query=args.query, min_stars=args.min_stars, inactive_days=args.inactive_days,
            per_page=args.per_page, max_pages=args.max_pages,
            include_archived=args.include_archived, exclude_forks=not args.include_forks,
        )
        results = search_candidates(config)
    except (GitHubAPIError, ValueError) as exc:
        print(f"ECHO discovery error: {exc}", file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([asdict(item) for item in results], indent=2), encoding="utf-8")
    print(f"Saved {len(results)} candidates to {output}")
    for item in results[:10]:
        print(f"{item.score:5.1f}  {item.stars:>6} stars  {item.name} — {item.inactive_days} inactive days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
