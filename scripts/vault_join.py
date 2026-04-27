"""프로젝트를 메타 vault 에 합류시킨다.

Usage (대화형):  python vault_join.py
Usage (명시):    python vault_join.py --project-root E:/MyAgent --project-id myagent --description "..."
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date as DateType
from pathlib import Path

from scripts._vault_common import (
    load_vault_config, load_wiki_config, save_vault_config, save_wiki_config,
    find_vault_config,
    VAULT_CONFIG_NAME, WIKI_CONFIG_NAME,
)
# create_junction is imported by name so tests can monkeypatch scripts.vault_join.create_junction
from scripts._vault_junction import create_junction, remove_junction, JunctionError


class JoinValidationError(Exception):
    """vault_join 사전 검증 실패."""


class JoinError(Exception):
    """vault_join 적용 실패."""


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


def apply_join(
    vault_root: Path,
    project_root: Path,
    project_id: str,
    name: str,
    description: str,
    wiki_path: str,
    handover_path: str | None,
    session_archive_path: str | None,
    recap_path: str | None,
    status: str,
    tags: list[str],
    joined_at: DateType,
) -> None:
    """프로젝트를 메타 vault 에 합류 — 트랜잭션 (실패 시 전체 원복).

    1) 사전 검증 → 2) wcfg/vcfg 백업 → 3) wcfg 패치 + vcfg append + junction 생성.
    실패 시 wcfg/vcfg 원복 + 생성된 junction 제거.

    Raises:
        JoinValidationError: 사전 검증 실패 (입력 오류, 상태 무변경).
        JoinError: 적용 도중 실패 (전체 원복 후 재발 — 환경 점검 필요).

    Note:
        rollback 은 configs 와 created junctions 만 원복.
        mkdir 로 생성된 빈 부모 디렉토리(예: vault_root/handovers/)는 청소하지 않음.
    """
    # 사전 검증 (실패 시 JoinValidationError — try 블록 밖)
    assert_project_has_wiki_config(project_root)
    assert_no_duplicate_id(vault_root, project_id)
    assert_no_existing_junction(vault_root, project_id)

    # 패치 준비 — deep copy via JSON round-trip
    wcfg = load_wiki_config(project_root)
    vcfg = load_vault_config(vault_root)
    wcfg_backup = json.loads(json.dumps(wcfg))
    vcfg_backup = json.loads(json.dumps(vcfg))

    vault_id = vcfg["vault_id"]
    wiki_patch = build_wiki_config_patch(vault_id, joined_at)
    vault_entry = build_vault_config_patch(
        project_id, name, description, project_root,
        wiki_path, handover_path, session_archive_path, recap_path,
        status, tags, joined_at,
    )
    junctions = plan_junctions(
        vault_root, project_root, project_id,
        wiki_path, handover_path, session_archive_path, recap_path,
    )

    created_junctions: list[Path] = []
    try:
        wcfg_new = {**wcfg, **wiki_patch}
        save_wiki_config(project_root, wcfg_new)

        vcfg_new = {**vcfg, "projects": vcfg["projects"] + [vault_entry]}
        save_vault_config(vault_root, vcfg_new)

        for link, target in junctions:
            create_junction(link, target)
            created_junctions.append(link)

    except (JunctionError, OSError) as e:
        # 롤백 — config 원복 후 부분 생성된 junction 제거
        save_wiki_config(project_root, wcfg_backup)
        save_vault_config(vault_root, vcfg_backup)
        for link in created_junctions:
            try:
                remove_junction(link)
            except JunctionError:
                pass
        raise JoinError(f"join failed, rolled back: {e}") from e
