"""TWK vault sync — junction → mirror 복사 + git push.

Usage:
    python vault_sync.py                         # vault.config.json 자동 탐색
    python vault_sync.py --vault-root E:/TWK_Vault
    python vault_sync.py --dry-run               # 변경 미리보기
    python vault_sync.py --project wesang        # 특정 프로젝트만
    python vault_sync.py --no-push               # mirror 만 갱신, push skip
"""
from __future__ import annotations

import argparse
import fnmatch
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts._vault_common import load_vault_config, find_vault_config

STATUS_ICON = {"Active": "🟢 Active", "Maintenance": "🟡 Maintenance", "Dormant": "⚪ Dormant"}


def should_exclude(rel_path: Path, patterns: list[str]) -> bool:
    """rel_path 가 exclude 패턴에 해당하면 True."""
    rel_str = str(rel_path).replace("\\", "/")
    name = rel_path.name
    for pat in patterns:
        pat_norm = pat.replace("\\", "/")
        if fnmatch.fnmatch(rel_str, pat_norm):
            return True
        if fnmatch.fnmatch(name, pat_norm):
            return True
    return False


def mirror_project(src: Path, dst: Path, exclude_patterns: list[str]) -> dict:
    """src 의 파일을 dst 로 mirror. 통계 dict 반환."""
    src = src.resolve()
    dst.mkdir(parents=True, exist_ok=True)

    src_files: set[Path] = set()
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        if should_exclude(rel, exclude_patterns):
            continue
        src_files.add(rel)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or target.read_bytes() != p.read_bytes():
            shutil.copy2(p, target)

    deleted = 0
    for p in dst.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(dst)
        if rel not in src_files:
            p.unlink()
            deleted += 1

    return {"copied": len(src_files), "deleted": deleted}


def generate_meta_projects(vault_cfg: dict, project_stats: dict[str, dict]) -> str:
    """vault.config.json 을 Dataview-readable markdown 으로 풀어냄.

    Precondition: each project in vault_cfg["projects"] MUST have a non-empty "id" field
    (validated upstream by vault_join). Other fields default sensibly when missing.
    """
    lines = [
        "---",
        "auto_generated: true",
        "generated_by: vault_sync.py",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "---",
        "",
        "# Projects (auto-generated, do not edit)",
        "",
    ]
    for proj in vault_cfg.get("projects", []):
        pid = proj["id"]
        stats = project_stats.get(pid, {})
        # Unknown status → render plain text (no icon); missing key → "Active" default
        status_display = STATUS_ICON.get(proj.get("status", "Active"), proj.get("status", ""))
        lines.append(f"## {pid}")
        lines.append(f"- name:: {proj.get('name', pid)}")
        lines.append(f"- project_id:: {pid}")
        lines.append(f"- description:: {proj.get('description', '')}")
        lines.append(f"- status:: {status_display}")
        lines.append(f"- last_activity:: {stats.get('last_activity', 'N/A')}")
        lines.append(f"- page_count:: {stats.get('page_count', 0)}")
        lines.append(f"- joined_at:: {proj.get('joined_at', '')}")
        lines.append("")
    return "\n".join(lines)


def collect_project_stats(vault_root: Path) -> dict[str, dict]:
    """junction 을 따라 각 프로젝트의 page_count + last_activity 수집."""
    projects_dir = vault_root / "projects"
    stats = {}
    for proj_dir in projects_dir.iterdir():
        if not proj_dir.is_dir():
            continue
        pid = proj_dir.name
        md_files = list(proj_dir.rglob("*.md"))
        page_count = len(md_files)
        last_mtime = max((p.stat().st_mtime for p in md_files), default=0)
        last_activity = (
            datetime.fromtimestamp(last_mtime).date().isoformat()
            if last_mtime else "N/A"
        )
        stats[pid] = {"page_count": page_count, "last_activity": last_activity}
    return stats
