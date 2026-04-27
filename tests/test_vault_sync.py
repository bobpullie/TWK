from pathlib import Path

import pytest

from datetime import date

from scripts.vault_sync import mirror_project, should_exclude, generate_meta_projects


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


def test_generate_meta_projects(tmp_path: Path):
    cfg = {
        "version": "0.4",
        "vault_id": "x",
        "projects": [
            {
                "id": "wesang",
                "name": "DnT 위상군",
                "description": "Topological Systems Architect",
                "status": "Active",
                "joined_at": "2026-04-26",
            },
        ],
    }
    project_stats = {"wesang": {"page_count": 27, "last_activity": "2026-04-22"}}
    output = generate_meta_projects(cfg, project_stats)
    assert "## wesang" in output
    assert "name:: DnT 위상군" in output
    assert "page_count:: 27" in output
    assert "last_activity:: 2026-04-22" in output
    assert "status:: 🟢 Active" in output  # 이모지 변환
