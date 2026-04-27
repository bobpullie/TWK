import subprocess
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


def test_collect_project_stats_basic(tmp_path: Path):
    """page_count + last_activity 가 plain 디렉토리에서 정확히 수집되는지."""
    from scripts.vault_sync import collect_project_stats

    vault_root = tmp_path / "vault"
    proj = vault_root / "projects" / "alpha"
    proj.mkdir(parents=True)
    (proj / "a.md").write_text("# A", encoding="utf-8")
    (proj / "sub").mkdir()
    (proj / "sub" / "b.md").write_text("# B", encoding="utf-8")
    (proj / "ignore.txt").write_text("not md")  # rglob *.md 만 카운트

    stats = collect_project_stats(vault_root)
    assert "alpha" in stats
    assert stats["alpha"]["page_count"] == 2
    # last_activity 는 ISO date 형식 문자열
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", stats["alpha"]["last_activity"])


def test_collect_project_stats_empty_project(tmp_path: Path):
    """md 파일 0 인 프로젝트는 last_activity = 'N/A'."""
    from scripts.vault_sync import collect_project_stats

    vault_root = tmp_path / "vault"
    proj = vault_root / "projects" / "empty"
    proj.mkdir(parents=True)

    stats = collect_project_stats(vault_root)
    assert stats["empty"]["page_count"] == 0
    assert stats["empty"]["last_activity"] == "N/A"


def test_git_commit_and_push_no_changes(tmp_path: Path, monkeypatch):
    """변경 없으면 commit/push 모두 skip."""
    from scripts.vault_sync import git_commit_and_push

    mirror = tmp_path / "mirror"
    mirror.mkdir()
    subprocess.run(["git", "-C", str(mirror), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(mirror), "config", "user.email", "test@test.com"], check=True)
    subprocess.run(["git", "-C", str(mirror), "config", "user.name", "Test"], check=True)
    (mirror / "init.md").write_text("init")
    subprocess.run(["git", "-C", str(mirror), "add", "."], check=True)
    subprocess.run(["git", "-C", str(mirror), "commit", "-m", "init", "-q"], check=True)

    pushed = git_commit_and_push(mirror, message="x", push=False)
    assert pushed is False  # 변경 없음


def test_git_commit_creates_commit(tmp_path: Path):
    from scripts.vault_sync import git_commit_and_push

    mirror = tmp_path / "mirror"
    mirror.mkdir()
    subprocess.run(["git", "-C", str(mirror), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(mirror), "config", "user.email", "test@test.com"], check=True)
    subprocess.run(["git", "-C", str(mirror), "config", "user.name", "Test"], check=True)

    (mirror / "new.md").write_text("hello")
    pushed = git_commit_and_push(mirror, message="vault sync test", push=False)
    assert pushed is True
    log = subprocess.run(
        ["git", "-C", str(mirror), "log", "--oneline"],
        capture_output=True, text=True,
    )
    assert "vault sync test" in log.stdout


def test_meta_projects_skip_write_when_only_timestamp_differs(tmp_path: Path):
    """generated_at 만 다르면 파일 미변경 (perpetual diff 방지)."""
    from scripts.vault_sync import _write_meta_if_changed

    path = tmp_path / "projects.md"
    old = (
        "---\n"
        "auto_generated: true\n"
        "generated_at: 2026-04-26T10:00:00\n"
        "---\n"
        "# Projects\n"
    )
    path.write_text(old, encoding="utf-8")
    old_mtime = path.stat().st_mtime

    new = (
        "---\n"
        "auto_generated: true\n"
        "generated_at: 2026-04-27T11:00:00\n"  # 다른 timestamp
        "---\n"
        "# Projects\n"  # 동일 의미 내용
    )
    _write_meta_if_changed(path, new)

    # 파일 미변경 확인
    assert path.read_text(encoding="utf-8") == old  # 원본 유지
