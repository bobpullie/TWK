from datetime import date
from pathlib import Path

import pytest

from scripts.vault_leave import run as vault_leave_run
from scripts.vault_join import apply_join
from scripts._vault_common import load_vault_config, load_wiki_config


def test_leave_removes_membership(initialized_vault: Path, fake_project: Path):
    apply_join(
        vault_root=initialized_vault, project_root=fake_project,
        project_id="fake", name="Fake", description="x",
        wiki_path="docs/wiki", handover_path="handover_doc",
        session_archive_path=None, recap_path=None,
        status="Active", tags=[], joined_at=date(2026, 4, 27),
    )

    vault_leave_run(vault_root=initialized_vault, project_id="fake")

    vcfg = load_vault_config(initialized_vault)
    assert vcfg["projects"] == []
    wcfg = load_wiki_config(fake_project)
    assert "vault_membership" not in wcfg
    assert not (initialized_vault / "projects" / "fake").exists()
    assert not (initialized_vault / "handovers" / "fake").exists()
    # 원본은 보존
    assert (fake_project / "docs" / "wiki" / "index.md").exists()


def test_leave_unknown_project_aborts(initialized_vault: Path):
    with pytest.raises(SystemExit):
        vault_leave_run(vault_root=initialized_vault, project_id="nonexistent")
