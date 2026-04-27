"""세션 종료 통합 hook — normalize + vault sync.

각 프로젝트 .claude/rules/session-lifecycle.md step 5.6 에서 호출:
    python ~/.claude/skills/TWK/scripts/session_end_hook.py --auto

`--auto` 모드:
- wiki.config.json 의 vault_membership 있으면 → vault sync
- 없으면 → skip (정상 종료)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from scripts._vault_common import WIKI_CONFIG_NAME

SKILL_ROOT = Path(__file__).resolve().parent.parent


def should_run_sync(project_root: Path) -> bool:
    cfg_path = project_root / WIKI_CONFIG_NAME
    if not cfg_path.exists():
        return False
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return "vault_membership" in cfg


def find_vault_root_for_project(project_root: Path) -> Path | None:
    """wiki.config.json.vault_membership.vault_id 와 매칭되는 vault 위치를 찾는다.

    MVP: 프로젝트 자체 wiki.config.json 의 vault_membership 만 보고,
    실제 vault_root 는 환경변수 TWK_VAULT_ROOT 또는 별도 인자로 받는다.
    """
    import os
    env_vault = os.environ.get("TWK_VAULT_ROOT")
    if env_vault and Path(env_vault).exists():
        return Path(env_vault)
    return None


def run(project_root: Path, vault_root: Path | None = None, auto: bool = False) -> int:
    """returns: exit code"""
    # Step 1: normalize (있으면)
    normalize_script = SKILL_ROOT / "scripts" / "normalize_session_frontmatter.py"
    if normalize_script.exists() and (project_root / WIKI_CONFIG_NAME).exists():
        result = subprocess.run(
            [sys.executable, str(normalize_script), "--apply", "--config",
             str(project_root / WIKI_CONFIG_NAME)],
            cwd=str(project_root),
        )
        if result.returncode != 0:
            print("WARN: normalize step failed (continuing)", file=sys.stderr)

    # Step 2: vault sync (조건부)
    if auto and not should_run_sync(project_root):
        print("[session_end_hook] vault_membership 없음 — sync skip")
        return 0

    if vault_root is None:
        vault_root = find_vault_root_for_project(project_root)
    if vault_root is None:
        print("WARN: vault_root 미해결 — sync skip (TWK_VAULT_ROOT 환경변수 설정 권장)",
              file=sys.stderr)
        return 0

    sync_script = SKILL_ROOT / "scripts" / "vault_sync.py"
    result = subprocess.run(
        [sys.executable, str(sync_script), "--vault-root", str(vault_root)],
    )
    return result.returncode


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project-root", type=Path, default=Path.cwd())
    p.add_argument("--vault-root", type=Path)
    p.add_argument("--auto", action="store_true",
                   help="vault_membership 없으면 sync skip (정상 종료)")
    args = p.parse_args()
    sys.exit(run(args.project_root, args.vault_root, args.auto))


if __name__ == "__main__":
    main()
