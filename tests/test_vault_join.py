from pathlib import Path

import pytest

from scripts.vault_join import (
    assert_project_has_wiki_config,
    assert_no_duplicate_id,
    assert_no_existing_junction,
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
