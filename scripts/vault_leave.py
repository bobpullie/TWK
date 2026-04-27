"""프로젝트를 메타 vault 에서 제거. 원본 폴더는 건드리지 않음.

Usage: python -m scripts.vault_leave --project-id <id> [--vault-root <path>]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts._vault_common import (
    load_vault_config, save_vault_config,
    load_wiki_config, save_wiki_config,
    find_vault_config,
)
from scripts._vault_junction import remove_junction, JunctionError


def run(vault_root: Path, project_id: str) -> None:
    cfg = load_vault_config(vault_root)
    projects = cfg.get("projects", [])
    target = next((p for p in projects if p["id"] == project_id), None)
    if not target:
        print(f"ERROR: project '{project_id}' not registered", file=sys.stderr)
        sys.exit(2)

    project_root = Path(target["root"])

    # Junction 제거 (3종)
    for kind in ("projects", "handovers", "session_archive"):
        link = vault_root / kind / project_id
        if link.exists():
            try:
                remove_junction(link)
                print(f"  ✓ removed junction: {link}")
            except JunctionError as e:
                print(f"  WARN: failed to remove {link}: {e}", file=sys.stderr)

    # vault.config.json 갱신
    cfg["projects"] = [p for p in projects if p["id"] != project_id]
    save_vault_config(vault_root, cfg)

    # wiki.config.json 의 vault_membership 제거
    if (project_root / "wiki.config.json").exists():
        wcfg = load_wiki_config(project_root)
        wcfg.pop("vault_membership", None)
        save_wiki_config(project_root, wcfg)
        print(f"  ✓ cleared vault_membership in {project_root}/wiki.config.json")

    print(f"✓ left {project_id}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vault-root", type=Path)
    p.add_argument("--project-id", required=True)
    args = p.parse_args()
    vault_root = args.vault_root or find_vault_config(Path.cwd())
    if not vault_root:
        print("ERROR: --vault-root required (or run from inside vault)", file=sys.stderr)
        sys.exit(2)
    run(vault_root, args.project_id)


if __name__ == "__main__":
    main()
