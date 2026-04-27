"""미가입 TWK 프로젝트 탐색.

Usage: python -m scripts.vault_discover --search-root E:/ [--vault-root <path>]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts._vault_common import load_vault_config, find_vault_config


def find_unjoined_projects(
    search_root: Path,
    joined_ids: set[str],
    max_depth: int = 4,
) -> list[dict]:
    """search_root 하위에서 wiki.config.json 가진 폴더 탐색 — joined_ids 제외."""
    found = []
    for cfg_path in search_root.rglob("wiki.config.json"):
        depth = len(cfg_path.relative_to(search_root).parts)
        if depth > max_depth:
            continue
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        pid = cfg.get("project_id")
        if not pid or pid in joined_ids:
            continue
        found.append({
            "project_id": pid,
            "root": str(cfg_path.parent),
            "version": cfg.get("version", "?"),
        })
    return found


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--search-root", type=Path, required=True)
    p.add_argument("--vault-root", type=Path)
    args = p.parse_args()

    joined_ids: set[str] = set()
    vault_root = args.vault_root or find_vault_config(Path.cwd())
    if vault_root:
        cfg = load_vault_config(vault_root)
        joined_ids = {p["id"] for p in cfg.get("projects", [])}

    found = find_unjoined_projects(args.search_root, joined_ids)
    if not found:
        print("(no unjoined TWK projects found)")
        return
    print(f"Found {len(found)} unjoined TWK project(s):\n")
    for f in found:
        print(f"  - {f['project_id']:20s} │ {f['root']} (v{f['version']})")
    print(f"\nTo join: python -m scripts.vault_join --project-root <path>")


if __name__ == "__main__":
    main()
