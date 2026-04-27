import json
from datetime import date
from pathlib import Path

from scripts.vault_discover import find_unjoined_projects
from scripts.vault_join import apply_join


def test_finds_wiki_config_projects(tmp_path: Path):
    p1 = tmp_path / "Proj1"
    (p1 / "docs/wiki").mkdir(parents=True)
    (p1 / "wiki.config.json").write_text(json.dumps({"project_id": "p1", "version": "1.1"}))

    p2 = tmp_path / "Proj2"
    (p2 / "docs/wiki").mkdir(parents=True)
    (p2 / "wiki.config.json").write_text(json.dumps({"project_id": "p2", "version": "1.1"}))

    found = find_unjoined_projects(search_root=tmp_path, joined_ids=set())
    ids = {f["project_id"] for f in found}
    assert ids == {"p1", "p2"}


def test_excludes_already_joined(tmp_path: Path):
    p1 = tmp_path / "Proj1"
    (p1 / "docs/wiki").mkdir(parents=True)
    (p1 / "wiki.config.json").write_text(json.dumps({"project_id": "p1"}))

    found = find_unjoined_projects(search_root=tmp_path, joined_ids={"p1"})
    assert found == []
