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


def _write_meta_if_changed(path: Path, new_content: str) -> None:
    """generated_at 라인을 제외한 의미적 내용이 같으면 쓰지 않음 (perpetual diff 방지)."""
    def _strip_timestamp(text: str) -> str:
        return "\n".join(
            line for line in text.splitlines()
            if not line.startswith("generated_at:")
        )

    if path.exists():
        old = path.read_text(encoding="utf-8")
        if _strip_timestamp(old) == _strip_timestamp(new_content):
            return  # 의미 변화 없음 — write skip
    path.write_text(new_content, encoding="utf-8")


def git_commit_and_push(mirror_root: Path, message: str, push: bool = True) -> bool:
    """mirror_root 에 변경 있으면 commit + (옵션) push. 변경 발생 여부 반환."""
    status = subprocess.run(
        ["git", "-C", str(mirror_root), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    )
    if not status.stdout.strip():
        return False

    subprocess.run(["git", "-C", str(mirror_root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(mirror_root), "commit", "-m", message, "-q"],
        check=True,
    )
    if push:
        result = subprocess.run(
            ["git", "-C", str(mirror_root), "push"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"WARN: push failed (commit kept locally): {result.stderr}", file=sys.stderr)
    return True


def run(
    vault_root: Path | None = None,
    project_filter: str | None = None,
    dry_run: bool = False,
    push: bool = True,
) -> None:
    if vault_root is None:
        vault_root = find_vault_config(Path.cwd())
        if vault_root is None:
            print("ERROR: vault.config.json not found (use --vault-root)", file=sys.stderr)
            sys.exit(2)

    cfg = load_vault_config(vault_root)
    mirror_root = Path(cfg["mirror_root"])
    exclude = cfg.get("sync", {}).get("exclude_patterns", [])

    projects = cfg.get("projects", [])
    if project_filter:
        projects = [p for p in projects if p["id"] == project_filter]

    print(f"[vault_sync] vault: {vault_root} → mirror: {mirror_root}")
    if dry_run:
        print("(dry-run — no file changes, no git ops)")

    total_copied = total_deleted = 0
    for proj in projects:
        pid = proj["id"]
        for kind in ("projects", "handovers", "session_archive"):
            src = vault_root / kind / pid
            if not src.exists():
                continue
            dst = mirror_root / kind / pid
            if dry_run:
                print(f"  [dry] {src} → {dst}")
                continue
            stats = mirror_project(src, dst, exclude)
            total_copied += stats["copied"]
            total_deleted += stats["deleted"]
            print(f"  ✓ {kind}/{pid}: copied={stats['copied']} deleted={stats['deleted']}")

    if not dry_run:
        # _meta/projects.md 자동 생성
        project_stats = collect_project_stats(vault_root)
        meta_md = generate_meta_projects(cfg, project_stats)
        meta_dir = mirror_root / "_meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        _write_meta_if_changed(meta_dir / "projects.md", meta_md)

        # vault.config.json 도 mirror 로 복사
        from scripts._vault_common import save_vault_config
        save_vault_config(mirror_root, cfg)

        # index.md 복사 (vault → mirror)
        if (vault_root / "index.md").exists():
            shutil.copy2(vault_root / "index.md", mirror_root / "index.md")

        # git commit + push
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"vault sync: {ts} ({len(projects)} projects, +{total_copied} -{total_deleted})"
        pushed = git_commit_and_push(mirror_root, msg, push=push)
        if pushed:
            print(f"✓ committed: {msg}" + (" + pushed" if push else " (push skipped)"))
        else:
            print("✓ no changes — skip commit")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--vault-root", type=Path)
    p.add_argument("--project")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-push", action="store_true")
    args = p.parse_args()
    run(
        vault_root=args.vault_root,
        project_filter=args.project,
        dry_run=args.dry_run,
        push=not args.no_push,
    )


if __name__ == "__main__":
    main()
