from pathlib import Path

import pytest

from scripts.vault_init import run as vault_init_run
from scripts._vault_common import load_vault_config


def test_init_creates_structure(tmp_path: Path):
    vault = tmp_path / "Vault"
    mirror = tmp_path / "Mirror"
    vault_init_run(
        vault_id="test-vault",
        vault_root=vault,
        mirror_root=mirror,
        mirror_remote="https://github.com/x/y.git",
        allowed_emails=["a@b.com"],
    )
    assert (vault / "vault.config.json").exists()
    assert (vault / ".obsidian").is_dir()
    assert (vault / "index.md").exists()
    assert (vault / "_meta" / "templates").is_dir()
    assert (vault / "projects").is_dir()
    assert (vault / "handovers").is_dir()


def test_init_writes_config(tmp_path: Path):
    vault = tmp_path / "Vault"
    vault_init_run(
        vault_id="kji-knowledge-vault",
        vault_root=vault,
        mirror_root=tmp_path / "Mirror",
        mirror_remote="https://github.com/bobpullie/KJI_WIKI.git",
        allowed_emails=["blueitems7@gmail.com"],
    )
    cfg = load_vault_config(vault)
    assert cfg["version"] == "0.4"
    assert cfg["vault_id"] == "kji-knowledge-vault"
    assert cfg["projects"] == []
    assert "blueitems7@gmail.com" in cfg["auth"]["allowed_emails"]


def test_init_existing_vault_aborts(tmp_path: Path):
    vault = tmp_path / "Vault"
    vault.mkdir()
    (vault / "vault.config.json").write_text("{}")
    with pytest.raises(SystemExit):
        vault_init_run(
            vault_id="x", vault_root=vault,
            mirror_root=tmp_path / "Mirror",
            mirror_remote="https://github.com/x/y.git",
            allowed_emails=["x@y.com"],
        )
