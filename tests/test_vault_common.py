import json
from pathlib import Path

import pytest

from scripts._vault_common import (
    load_vault_config, save_vault_config,
    load_wiki_config, save_wiki_config,
    find_vault_config, VaultConfigError,
)


def test_load_save_vault_config_roundtrip(tmp_vault_root: Path):
    cfg = {"version": "0.4", "vault_id": "x", "projects": []}
    save_vault_config(tmp_vault_root, cfg)
    loaded = load_vault_config(tmp_vault_root)
    assert loaded == cfg


def test_load_vault_config_missing_raises(tmp_vault_root: Path):
    with pytest.raises(VaultConfigError, match="vault.config.json not found"):
        load_vault_config(tmp_vault_root)


def test_find_vault_config_walks_up(tmp_path: Path):
    vault = tmp_path / "Vault"
    vault.mkdir()
    (vault / "vault.config.json").write_text('{"version":"0.4","vault_id":"x"}')
    nested = vault / "_meta" / "deep"
    nested.mkdir(parents=True)
    found = find_vault_config(start=nested)
    assert found == vault


def test_find_vault_config_not_found(tmp_path: Path):
    assert find_vault_config(start=tmp_path) is None


def test_load_wiki_config(fake_project: Path):
    cfg = load_wiki_config(fake_project)
    assert cfg["project_id"] == "fake"
