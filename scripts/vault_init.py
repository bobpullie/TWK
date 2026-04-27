"""TWK 메타 vault 초기화 — 빈 구조 생성 + vault.config.json 템플릿 적용.

Usage:
    python vault_init.py --vault-id kji-knowledge-vault \\
        --vault-root E:/TWK_Vault \\
        --mirror-root E:/KJI_WIKI \\
        --mirror-remote https://github.com/bobpullie/KJI_WIKI.git \\
        --allowed-email blueitems7@gmail.com
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from scripts._vault_common import save_vault_config, VAULT_CONFIG_NAME

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = SKILL_ROOT / "templates"

VAULT_SUBDIRS = [".obsidian", "_meta/templates", "projects", "handovers", "session_archive"]


def run(
    vault_id: str,
    vault_root: Path,
    mirror_root: Path,
    mirror_remote: str,
    allowed_emails: list[str],
    mobile_url: str = "kji-wiki.pages.dev",
) -> None:
    if (vault_root / VAULT_CONFIG_NAME).exists():
        print(f"ERROR: vault already initialized at {vault_root}", file=sys.stderr)
        sys.exit(2)

    vault_root.mkdir(parents=True, exist_ok=True)
    for sub in VAULT_SUBDIRS:
        (vault_root / sub).mkdir(parents=True, exist_ok=True)

    template_text = (TEMPLATES / "vault.config.json.template").read_text(encoding="utf-8")
    # Use forward slashes for paths inside JSON to avoid Windows backslash escape issues.
    rendered = (
        template_text
        .replace("{{VAULT_ID}}", vault_id)
        .replace("{{VAULT_ROOT}}", vault_root.as_posix())
        .replace("{{MIRROR_ROOT}}", mirror_root.as_posix())
        .replace("{{MIRROR_REMOTE}}", mirror_remote)
        .replace("{{MOBILE_URL}}", mobile_url)
        .replace("{{ALLOWED_EMAIL}}", allowed_emails[0])
    )
    cfg = json.loads(rendered)
    if len(allowed_emails) > 1:
        cfg["auth"]["allowed_emails"] = allowed_emails
    save_vault_config(vault_root, cfg)

    if (TEMPLATES / "vault_index.md.template").exists():
        shutil.copy(TEMPLATES / "vault_index.md.template", vault_root / "index.md")
    else:
        (vault_root / "index.md").write_text(f"# {vault_id}\n", encoding="utf-8")

    print(f"✓ vault initialized at {vault_root}")
    print(f"  vault_id: {vault_id}")
    print(f"  mirror: {mirror_root} → {mirror_remote}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vault-id", required=True)
    p.add_argument("--vault-root", required=True, type=Path)
    p.add_argument("--mirror-root", required=True, type=Path)
    p.add_argument("--mirror-remote", required=True)
    p.add_argument("--allowed-email", required=True, action="append")
    p.add_argument("--mobile-url", default="kji-wiki.pages.dev")
    args = p.parse_args()
    run(
        vault_id=args.vault_id,
        vault_root=args.vault_root,
        mirror_root=args.mirror_root,
        mirror_remote=args.mirror_remote,
        allowed_emails=args.allowed_email,
        mobile_url=args.mobile_url,
    )


if __name__ == "__main__":
    main()
