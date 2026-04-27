"""End-to-end smoke test — init → join 2개 → sync → status → leave 1개 → sync."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from scripts.vault_init import run as vault_init_run
from scripts.vault_join import apply_join
from scripts.vault_leave import run as vault_leave_run
from scripts.vault_sync import run as vault_sync_run
from scripts.vault_status import collect_status
from scripts._vault_common import load_vault_config


@pytest.mark.skipif(sys.platform != "win32", reason="full integration uses Win32 junctions")
def test_full_lifecycle(tmp_path: Path):
    vault = tmp_path / "Vault"
    mirror = tmp_path / "Mirror"
    proj1 = tmp_path / "Proj1"
    proj2 = tmp_path / "Proj2"

    # Setup: 2개 가짜 프로젝트
    for proj, pid in [(proj1, "p1"), (proj2, "p2")]:
        (proj / "docs/wiki/concepts").mkdir(parents=True)
        (proj / "handover_doc").mkdir()
        (proj / "wiki.config.json").write_text(json.dumps({
            "version": "1.1", "project_id": pid,
            "paths": {"wiki_root": "docs/wiki"},
        }))
        (proj / "docs/wiki" / "index.md").write_text(f"# {pid} wiki")
        (proj / "docs/wiki/concepts" / "X.md").write_text(f"# {pid} concept X")

    # 1. init
    vault_init_run(
        vault_id="test", vault_root=vault, mirror_root=mirror,
        mirror_remote="https://github.com/x/y.git",
        allowed_emails=["a@b.com"],
    )
    assert (vault / "vault.config.json").exists()

    # 2. join 2개
    for proj, pid in [(proj1, "p1"), (proj2, "p2")]:
        apply_join(
            vault_root=vault, project_root=proj,
            project_id=pid, name=pid.upper(), description=f"{pid} desc",
            wiki_path="docs/wiki", handover_path="handover_doc",
            session_archive_path=None, recap_path=None,
            status="Active", tags=[pid], joined_at=date(2026, 4, 27),
        )

    cfg = load_vault_config(vault)
    assert len(cfg["projects"]) == 2

    # 3. status — 2개 모두 healthy
    status = collect_status(vault)
    assert status["projects"]["p1"]["health"] == "healthy"
    assert status["projects"]["p1"]["page_count"] == 2  # index + concepts/X
    assert status["projects"]["p2"]["health"] == "healthy"

    # 4. mirror 초기화 (git init) + sync
    mirror.mkdir(exist_ok=True)
    subprocess.run(["git", "-C", str(mirror), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(mirror), "config", "user.email", "test@test.com"], check=True)
    subprocess.run(["git", "-C", str(mirror), "config", "user.name", "Test"], check=True)

    vault_sync_run(vault_root=vault, push=False)

    # 5. mirror 에 파일 복사 확인
    assert (mirror / "projects/p1/index.md").exists()
    assert (mirror / "projects/p2/concepts/X.md").exists()
    assert (mirror / "_meta/projects.md").exists()

    meta_text = (mirror / "_meta/projects.md").read_text(encoding="utf-8")
    assert "## p1" in meta_text
    assert "## p2" in meta_text
    assert "name:: P1" in meta_text

    # 6. leave p1
    vault_leave_run(vault_root=vault, project_id="p1")
    assert not (vault / "projects/p1").exists()
    cfg = load_vault_config(vault)
    assert {p["id"] for p in cfg["projects"]} == {"p2"}

    # 7. 다시 sync — p1 mirror 에서 제거됨
    vault_sync_run(vault_root=vault, push=False)
    assert not (mirror / "projects/p1").exists()
    assert (mirror / "projects/p2").exists()

    # 7b. _meta/projects.md 도 p1 제거 반영
    meta_after = (mirror / "_meta/projects.md").read_text(encoding="utf-8")
    assert "## p1" not in meta_after
    assert "## p2" in meta_after

    # 7c. mirror 의 vault.config.json 도 leave 반영
    mirror_cfg = json.loads((mirror / "vault.config.json").read_text(encoding="utf-8"))
    assert {p["id"] for p in mirror_cfg["projects"]} == {"p2"}
