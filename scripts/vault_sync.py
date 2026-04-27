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
