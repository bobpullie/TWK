import json
from pathlib import Path

import pytest

from scripts.session_end_hook import should_run_sync


def test_skips_when_no_vault_membership(tmp_path: Path):
    cfg = {"version": "1.1", "project_id": "x"}
    cfg_path = tmp_path / "wiki.config.json"
    cfg_path.write_text(json.dumps(cfg))
    assert should_run_sync(tmp_path) is False


def test_runs_when_vault_membership_present(tmp_path: Path):
    cfg = {
        "version": "1.2",
        "project_id": "x",
        "vault_membership": {"vault_id": "v1", "joined_at": "2026-04-27"},
    }
    cfg_path = tmp_path / "wiki.config.json"
    cfg_path.write_text(json.dumps(cfg))
    assert should_run_sync(tmp_path) is True


def test_missing_wiki_config_skips(tmp_path: Path):
    assert should_run_sync(tmp_path) is False
