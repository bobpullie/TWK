from pathlib import Path

import pytest

from scripts.vault_sync import mirror_project, should_exclude
from scripts._vault_common import load_vault_config


def test_should_exclude_workspace_json():
    assert should_exclude(Path(".obsidian/workspace.json"), [".obsidian/workspace.json", "*.tmp"])
    assert should_exclude(Path("foo.tmp"), ["*.tmp"])
    assert not should_exclude(Path("foo.md"), ["*.tmp"])


def test_mirror_project_copies_files(tmp_path: Path):
    src = tmp_path / "src"
    (src / "concepts").mkdir(parents=True)
    (src / "concepts" / "X.md").write_text("# X", encoding="utf-8")
    (src / "concepts" / "X.tmp").write_text("temp", encoding="utf-8")

    dst = tmp_path / "dst"
    mirror_project(src, dst, exclude_patterns=["*.tmp"])

    assert (dst / "concepts" / "X.md").read_text(encoding="utf-8") == "# X"
    assert not (dst / "concepts" / "X.tmp").exists()


def test_mirror_project_deletes_extras(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "keep.md").write_text("keep")

    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "stale.md").write_text("delete me")
    (dst / "keep.md").write_text("old")

    mirror_project(src, dst, exclude_patterns=[])

    assert not (dst / "stale.md").exists()
    assert (dst / "keep.md").read_text() == "keep"
