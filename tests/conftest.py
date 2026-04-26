"""TWK vault aggregator pytest fixtures."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def tmp_vault_root(tmp_path: Path) -> Path:
    """빈 메타 vault 폴더 (vault_init 전 상태)."""
    root = tmp_path / "TWK_Vault"
    root.mkdir()
    return root


@pytest.fixture
def fake_project(tmp_path: Path) -> Path:
    """가짜 프로젝트 폴더 — wiki.config.json + docs/wiki/ + handover_doc/ 포함."""
    proj = tmp_path / "FakeAgent"
    (proj / "docs" / "wiki").mkdir(parents=True)
    (proj / "handover_doc").mkdir(parents=True)
    cfg = {
        "version": "1.1",
        "project_id": "fake",
        "mode": "session-extract",
        "paths": {"wiki_root": "docs/wiki"},
    }
    (proj / "wiki.config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    (proj / "docs" / "wiki" / "index.md").write_text("# Fake Wiki\n", encoding="utf-8")
    return proj


@pytest.fixture
def initialized_vault(tmp_vault_root: Path) -> Path:
    """vault_init.py 실행된 상태의 메타 vault."""
    from scripts.vault_init import run as vault_init_run
    vault_init_run(
        vault_id="test-vault",
        vault_root=tmp_vault_root,
        mirror_root=tmp_vault_root.parent / "Mirror",
        mirror_remote="https://github.com/test/test.git",
        allowed_emails=["test@example.com"],
    )
    return tmp_vault_root
