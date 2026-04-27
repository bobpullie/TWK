"""TWK vault 상태 점검 — 등록된 프로젝트 + junction 건강도.

Usage: python -m scripts.vault_status [--vault-root <path>] [--json]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from scripts._vault_common import load_vault_config, find_vault_config


def collect_status(vault_root: Path) -> dict:
    cfg = load_vault_config(vault_root)
    out = {
        "vault_id": cfg["vault_id"],
        "vault_root": str(vault_root),
        "mirror": cfg.get("mirror_remote", ""),
        "last_sync": _last_sync(Path(cfg["mirror_root"])),
        "projects": {},
    }
    for proj in cfg.get("projects", []):
        pid = proj["id"]
        link = vault_root / "projects" / pid
        handover_link = vault_root / "handovers" / pid

        health = "healthy"
        page_count = 0
        handover_count = 0
        last_activity = "N/A"

        if not link.exists():
            health = "broken"
        else:
            try:
                md_files = list(link.rglob("*.md"))
                page_count = len(md_files)
                if md_files:
                    last_mtime = max(p.stat().st_mtime for p in md_files)
                    last_activity = datetime.fromtimestamp(last_mtime).date().isoformat()
            except OSError:
                health = "broken"

        if handover_link.exists():
            try:
                handover_count = len(list(handover_link.rglob("*.md")))
            except OSError:
                pass

        out["projects"][pid] = {
            "name": proj.get("name", pid),
            "status": proj.get("status", ""),
            "health": health,
            "page_count": page_count,
            "handover_count": handover_count,
            "last_activity": last_activity,
        }
    return out


def _last_sync(mirror_root: Path) -> str:
    if not (mirror_root / ".git").exists():
        return "never"
    try:
        result = subprocess.run(
            ["git", "-C", str(mirror_root), "log", "-1", "--format=%cr"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def format_report(status: dict) -> str:
    lines = [
        f"[{status['vault_id']}] ({status['vault_root']})",
        f"Mirror: {status['mirror']}",
        f"Last sync: {status['last_sync']}",
        "",
        "Projects:",
    ]
    for pid, p in status["projects"].items():
        icon = "✓" if p["health"] == "healthy" else "✗"
        lines.append(
            f"  {icon} {pid:12s} │ {p['page_count']:3d} pages │ "
            f"{p['handover_count']:3d} handovers │ "
            f"{p['last_activity']:10s} │ {p['health']}"
        )
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vault-root", type=Path)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    vault_root = args.vault_root or find_vault_config(Path.cwd())
    if not vault_root:
        print("ERROR: vault.config.json not found", file=sys.stderr)
        sys.exit(2)
    status = collect_status(vault_root)
    if args.json:
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(format_report(status))


if __name__ == "__main__":
    main()
