"""프로젝트를 메타 vault 에 합류시킨다.

Usage (대화형):  python vault_join.py
Usage (명시):    python vault_join.py --project-root E:/MyAgent --project-id myagent --description "..."
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts._vault_common import (
    load_vault_config, load_wiki_config, find_vault_config,
    VAULT_CONFIG_NAME, WIKI_CONFIG_NAME,
)


class JoinValidationError(Exception):
    """vault_join 사전 검증 실패."""


def assert_project_has_wiki_config(project_root: Path) -> None:
    if not (project_root / WIKI_CONFIG_NAME).exists():
        raise JoinValidationError(
            f"{WIKI_CONFIG_NAME} not found at {project_root} — run init_wiki.py first"
        )


def assert_no_duplicate_id(vault_root: Path, project_id: str) -> None:
    cfg = load_vault_config(vault_root)
    existing_ids = {p.get("id") for p in cfg.get("projects", [])}
    if project_id in existing_ids:
        raise JoinValidationError(f"duplicate project_id: {project_id}")


def assert_no_existing_junction(vault_root: Path, project_id: str) -> None:
    target = vault_root / "projects" / project_id
    if target.exists():
        raise JoinValidationError(f"junction target already exists: {target}")
