import json

from echo_discovery.research_cli import _names_from_json


def test_batch_names_accept_discovery_candidate_objects(tmp_path):
    path = tmp_path / "candidates.json"
    path.write_text(json.dumps([
        {"name": "demo/one", "score": 70},
        {"full_name": "demo/two"},
        {"name": "bad"},
        "demo/one",
    ]), encoding="utf-8")
    assert _names_from_json(path) == ["demo/one", "demo/two"]
