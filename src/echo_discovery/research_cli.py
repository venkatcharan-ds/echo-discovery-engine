"""CLI for investigating repositories discovered by ECHO."""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .github_client import GitHubAPIError
from .investigator import research_repository


def _names_from_json(path: Path) -> list[str]:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        payload = payload.get("candidates", payload.get("repositories", payload))
    if not isinstance(payload, list):
        raise ValueError("Batch input must be a JSON list or an object containing candidates/repositories")
    names: list[str] = []
    for row in payload:
        if isinstance(row, str):
            name = row
        elif isinstance(row, dict):
            name = row.get("name") or row.get("full_name") or row.get("repository")
        else:
            name = None
        if isinstance(name, str) and name.count("/") == 1:
            names.append(name)
    return list(dict.fromkeys(names))


def main() -> int:
    parser = argparse.ArgumentParser(description="Research public GitHub repositories with source-attributed evidence.")
    parser.add_argument("repository", nargs="?", help="Repository in owner/name format")
    parser.add_argument("--batch", help="JSON file produced by echo-discover")
    parser.add_argument("--output", default="outputs/research")
    args = parser.parse_args()
    if bool(args.repository) == bool(args.batch):
        parser.error("provide exactly one of repository or --batch")

    output = Path(args.output)
    try:
        if args.repository:
            report = research_repository(args.repository)
            output_path = output if output.suffix.lower() == ".json" else output / (args.repository.replace("/", "__") + ".json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Saved research report: {output_path}")
            return 0

        names = _names_from_json(Path(args.batch))
        if not names:
            raise ValueError("No valid owner/name repositories found in batch JSON")
        output.mkdir(parents=True, exist_ok=True)
        failed = 0
        for name in names:
            try:
                report = research_repository(name)
                path = output / (name.replace("/", "__") + ".json")
                path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"Saved {name}: {path}")
            except (GitHubAPIError, ValueError) as exc:
                failed += 1
                print(f"Failed {name}: {exc}", file=sys.stderr)
        print(f"Research complete: {len(names) - failed} succeeded, {failed} failed")
        return 1 if failed else 0
    except (GitHubAPIError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ECHO research error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
