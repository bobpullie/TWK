"""프로젝트를 메타 vault 에 합류시킨다.

Usage (대화형):  python vault_join.py
Usage (명시):    python vault_join.py --project-root E:/MyAgent --project-id myagent --description "..."
"""
from __future__ import annotations

import argparse
import sys
from datetime import date as DateType
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


def build_wiki_config_patch(vault_id: str, joined_at: DateType) -> dict:
    return {
        "vault_membership": {
            "vault_id": vault_id,
            "joined_at": joined_at.isoformat(),
        }
    }


def build_vault_config_patch(
    project_id: str,
    name: str,
    description: str,
    project_root: Path,
    wiki_path: str,
    handover_path: str | None,
    session_archive_path: str | None,
    recap_path: str | None,
    status: str,
    tags: list[str],
    joined_at: DateType,
) -> dict:
    entry = {
        "id": project_id,
        "name": name,
        "description": description,
        "root": project_root.as_posix(),  # Windows 경로 구분자 정규화 (T5/T8 lesson)
        "wiki_path": wiki_path,
        "status": status,
        "tags": tags,
        "joined_at": joined_at.isoformat(),
    }
    if handover_path:
        entry["handover_path"] = handover_path
    if session_archive_path:
        entry["session_archive_path"] = session_archive_path
    if recap_path:
        entry["recap_path"] = recap_path
    return entry


def plan_junctions(
    vault_root: Path,
    project_root: Path,
    project_id: str,
    wiki_path: str,
    handover_path: str | None,
    session_archive_path: str | None,
    recap_path: str | None,
) -> list[tuple[Path, Path]]:
    """반환: [(link_path, target_path), ...]"""
    plans = []
    plans.append((vault_root / "projects" / project_id, project_root / wiki_path))
    if handover_path and (project_root / handover_path).exists():
        plans.append((vault_root / "handovers" / project_id, project_root / handover_path))
    if session_archive_path and (project_root / session_archive_path).exists():
        plans.append((vault_root / "session_archive" / project_id, project_root / session_archive_path))
    if recap_path and (project_root / recap_path).exists():
        # recap 은 vault 에 포함하지 않음 (각 프로젝트 로컬 — TCL #116)
        pass
    return plans
