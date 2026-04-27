from datetime import date
from pathlib import Path

import pytest

from scripts.vault_join import (
    assert_project_has_wiki_config,
    assert_no_duplicate_id,
    assert_no_existing_junction,
    build_wiki_config_patch,
    build_vault_config_patch,
    plan_junctions,
    JoinValidationError,
)
from scripts._vault_common import save_vault_config


def test_assert_wiki_config_present(fake_project: Path):
    assert_project_has_wiki_config(fake_project)  # no raise


def test_assert_wiki_config_missing(tmp_path: Path):
    with pytest.raises(JoinValidationError, match="wiki.config.json"):
        assert_project_has_wiki_config(tmp_path)


def test_assert_no_duplicate_id(initialized_vault: Path):
    assert_no_duplicate_id(initialized_vault, "newone")  # 빈 projects[] — pass

    cfg_path = initialized_vault / "vault.config.json"
    import json
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["projects"].append({"id": "existing", "name": "X"})
    save_vault_config(initialized_vault, cfg)

    with pytest.raises(JoinValidationError, match="duplicate project_id: existing"):
        assert_no_duplicate_id(initialized_vault, "existing")


def test_assert_no_existing_junction(initialized_vault: Path):
    assert_no_existing_junction(initialized_vault, "fresh")  # no raise
    (initialized_vault / "projects" / "taken").mkdir()
    with pytest.raises(JoinValidationError, match="already exists"):
        assert_no_existing_junction(initialized_vault, "taken")


def test_build_wiki_config_patch():
    patch = build_wiki_config_patch(
        vault_id="test-vault",
        joined_at=date(2026, 4, 27),
    )
    assert patch == {
        "vault_membership": {
            "vault_id": "test-vault",
            "joined_at": "2026-04-27",
        }
    }


def test_build_vault_config_patch_full():
    patch = build_vault_config_patch(
        project_id="myagent",
        name="My Agent",
        description="A test agent",
        project_root=Path("E:/MyAgent"),
        wiki_path="docs/wiki",
        handover_path="handover_doc",
        session_archive_path=None,
        recap_path=None,
        status="Active",
        tags=["test"],
        joined_at=date(2026, 4, 27),
    )
    assert patch["id"] == "myagent"
    assert patch["root"] == "E:/MyAgent"
    assert patch["wiki_path"] == "docs/wiki"
    assert "session_archive_path" not in patch  # None 은 키 자체 생략
    assert patch["tags"] == ["test"]


def test_plan_junctions(initialized_vault: Path, fake_project: Path):
    plans = plan_junctions(
        vault_root=initialized_vault,
        project_root=fake_project,
        project_id="fake",
        wiki_path="docs/wiki",
        handover_path="handover_doc",
        session_archive_path=None,
        recap_path=None,
    )
    targets = {(link.name, target.name) for link, target in plans}
    assert ("fake", "wiki") in targets  # projects/fake → docs/wiki
    assert ("fake", "handover_doc") in targets  # handovers/fake → handover_doc
    assert len(plans) == 2  # session_archive/recap 없음
