"""Initialize a new LLM Wiki structure for a project.

새 프로젝트에 wiki 구조를 초기화. wiki.config.json 생성 + 디렉토리 + 기본 파일 세팅.

Usage:
    python init_wiki.py --mode B --wiki-root docs/wiki --sections decisions,concepts,principles
    python init_wiki.py --mode A --wiki-root fermion_wiki/wiki --sections ideas,concepts,postmortems,principles
    python init_wiki.py --mode B --project-id my-agent --dry-run
    python init_wiki.py --help
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
PAGE_TEMPLATES_DIR = TEMPLATES_DIR / "page-templates"
SCHEMA_TEMPLATES_DIR = TEMPLATES_DIR / "schema"

VALID_MODES = ["karpathy-pure", "session-extract", "hybrid"]
MODE_ALIASES = {"A": "karpathy-pure", "B": "session-extract"}

INDEX_MD_TEMPLATE = """\
# {project_id} Wiki — Index

> 마지막 갱신: {today} (초기화)

{dataview_block}

---

{sections_toc}

---
*관리: LLM (Ingest/Lint 시 자동 갱신), 큐레이션: 인간*
*이 파일은 wiki의 진입점. Obsidian에서 북마크 권장.*
"""

DATAVIEW_BLOCK = """\
```dataview
TABLE date, status, scope
FROM "{wiki_root}"
WHERE file.name != "index" AND file.name != "log"
SORT date DESC
LIMIT 20
```
"""

LOG_MD_TEMPLATE = """\
# Wiki Change Log

> append-only. 삭제 금지. 최신이 위.

## {today} — [Init] wiki 초기화 | 섹션: {sections}
"""

SECTION_TOC_TEMPLATE = """\
## {section_name_title}

*(아직 없음)*
"""


def normalize_mode(mode: str) -> str:
    return MODE_ALIASES.get(mode, mode)


def make_sections_config(sections: list[str]) -> list[dict]:
    template_map = {
        "decisions": "decision",
        "ideas": "idea",
        "postmortems": "postmortem",
        "concepts": "concept",
        "principles": "principle",
        "hypotheses": "entity",
        "indicators": "entity",
        "strategies": "entity",
        "architecture": "entity",
        "pipeline": "entity",
        "reference": "entity",
        "diagnostics": "entity",
    }
    phase_map = {
        "ideas": "P1",
        "hypotheses": "P3",
        "postmortems": "P5",
        "principles": "P10",
    }
    return [
        {
            "name": s,
            "template": template_map.get(s, "entity"),
            "phase_tag": phase_map.get(s),
        }
        for s in sections
    ]


def build_config(
    project_id: str,
    mode: str,
    wiki_root: str,
    sections: list[str],
    raw_root: str,
    session_archive_root: str,
) -> dict:
    return {
        "version": "1.0",
        "project_id": project_id,
        "mode": mode,
        "paths": {
            "wiki_root": wiki_root,
            "raw_root": raw_root,
            "session_archive_root": session_archive_root,
            "sessions_jsonl": f"~/.claude/projects/<agent-uuid>/*.jsonl",
        },
        "sections": make_sections_config(sections),
        "auditors": [],
        "frontmatter": {
            "required_fields": ["date", "status"],
            "optional_fields": ["phase", "scope", "project", "tags"],
        },
        "lint_cadence": {
            "every_sessions": 5,
            "every_pages": 10,
        },
        "obsidian": {
            "vault_path": ".",
            "dataview_enabled": True,
        },
    }


def build_index_md(
    project_id: str,
    wiki_root_str: str,
    sections: list[str],
    dataview_enabled: bool,
) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    sections_toc = "\n".join(
        SECTION_TOC_TEMPLATE.format(section_name_title=s.capitalize())
        for s in sections
    )
    dataview_block = (
        DATAVIEW_BLOCK.format(wiki_root=wiki_root_str)
        if dataview_enabled
        else ""
    )
    return INDEX_MD_TEMPLATE.format(
        project_id=project_id,
        today=today,
        dataview_block=dataview_block,
        sections_toc=sections_toc,
    )


def build_log_md(sections: list[str]) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_MD_TEMPLATE.format(
        today=today,
        sections=", ".join(sections),
    )


def create_structure(
    project_root: Path,
    config: dict,
    wiki_root: Path,
    mode: str,
    sections: list[str],
    dry_run: bool,
) -> None:
    """디렉토리 구조 + 기본 파일 생성."""
    paths = config["paths"]
    wiki_root_str = paths["wiki_root"]
    project_id = config["project_id"]
    dataview_enabled = config["obsidian"]["dataview_enabled"]

    actions: list[tuple[str, Path, str | None]] = []  # (type, path, content)

    # wiki/ 섹션 디렉토리
    for section in sections:
        actions.append(("mkdir", wiki_root / section, None))

    # index.md
    actions.append((
        "write",
        wiki_root / "index.md",
        build_index_md(project_id, wiki_root_str, sections, dataview_enabled),
    ))

    # log.md
    actions.append((
        "write",
        wiki_root / "log.md",
        build_log_md(sections),
    ))

    # schema/ 디렉토리 + templates 복사
    schema_dir = project_root / "schema"
    actions.append(("mkdir", schema_dir, None))
    actions.append(("mkdir", schema_dir / "templates", None))

    for tmpl in ["ingest.md", "query.md", "lint.md"]:
        src = SCHEMA_TEMPLATES_DIR / tmpl
        dst = schema_dir / tmpl
        if src.exists():
            actions.append(("copy", dst, str(src)))

    # page templates 복사
    for tmpl in PAGE_TEMPLATES_DIR.glob("*.md"):
        actions.append(("copy", schema_dir / "templates" / tmpl.name, str(tmpl)))

    # session_archive 디렉토리 (Mode B / hybrid)
    if mode in ("session-extract", "hybrid"):
        archive_root = paths.get("session_archive_root", "docs/session_archive")
        archive_dir = project_root / archive_root
        if not archive_dir.is_absolute():
            archive_dir = project_root / archive_root
        actions.append(("mkdir", archive_dir, None))

    # raw/ 디렉토리 (Mode A / hybrid)
    if mode in ("karpathy-pure", "hybrid"):
        raw_root = paths.get("raw_root", "raw")
        raw_dir = project_root / raw_root
        actions.append(("mkdir", raw_dir, None))

    # wiki.config.json
    config_path = project_root / "wiki.config.json"
    actions.append((
        "write",
        config_path,
        json.dumps(config, indent=2, ensure_ascii=False),
    ))

    # 실행
    for action_type, target, extra in actions:
        if action_type == "mkdir":
            if dry_run:
                print(f"[dry-run] mkdir {target}")
            else:
                target.mkdir(parents=True, exist_ok=True)
                print(f"[ok] mkdir {target}")
        elif action_type == "write":
            if dry_run:
                print(f"[dry-run] write {target}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(extra, encoding="utf-8")
                print(f"[ok] write {target}")
        elif action_type == "copy":
            src_path = Path(extra)
            if dry_run:
                print(f"[dry-run] copy {src_path.name} → {target}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, target)
                print(f"[ok] copy {src_path.name} → {target}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--mode",
        default="B",
        help="wiki 모드: A (karpathy-pure) / B (session-extract) / hybrid (기본: B)",
    )
    ap.add_argument(
        "--wiki-root",
        default="docs/wiki",
        help="wiki L3 루트 디렉토리 (기본: docs/wiki)",
    )
    ap.add_argument(
        "--sections",
        default="decisions,concepts,principles",
        help="콤마 구분 섹션 목록 (기본: decisions,concepts,principles)",
    )
    ap.add_argument(
        "--project-id",
        default=None,
        help="프로젝트 ID (기본: 현재 디렉토리명)",
    )
    ap.add_argument(
        "--project-root",
        default=".",
        help="프로젝트 루트 경로 (기본: 현재 디렉토리)",
    )
    ap.add_argument(
        "--raw-root",
        default="raw",
        help="L1 raw 디렉토리 (Mode A/hybrid용, 기본: raw)",
    )
    ap.add_argument(
        "--session-archive-root",
        default="docs/session_archive",
        help="L2 session archive 디렉토리 (Mode B/hybrid용, 기본: docs/session_archive)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 파일 생성 없이 수행될 작업만 출력",
    )
    args = ap.parse_args()

    mode = normalize_mode(args.mode)
    if mode not in VALID_MODES:
        print(f"[error] 유효하지 않은 모드: {args.mode}. 선택: A/B/karpathy-pure/session-extract/hybrid")
        return 1

    project_root = Path(args.project_root).resolve()
    project_id = args.project_id or project_root.name
    sections = [s.strip() for s in args.sections.split(",") if s.strip()]
    wiki_root = project_root / args.wiki_root

    if not sections:
        print("[error] 섹션 목록이 비어있음. --sections 지정 필요.")
        return 1

    print(f"\n[init_wiki] 설정:")
    print(f"  project_id : {project_id}")
    print(f"  mode       : {mode}")
    print(f"  project_root: {project_root}")
    print(f"  wiki_root  : {wiki_root}")
    print(f"  sections   : {sections}")
    print(f"  dry-run    : {args.dry_run}\n")

    config = build_config(
        project_id=project_id,
        mode=mode,
        wiki_root=args.wiki_root,
        sections=sections,
        raw_root=args.raw_root,
        session_archive_root=args.session_archive_root,
    )

    create_structure(
        project_root=project_root,
        config=config,
        wiki_root=wiki_root,
        mode=mode,
        sections=sections,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        print(f"\n[init_wiki] 완료!")
        print(f"  다음 단계:")
        print(f"  1. wiki.config.json에서 paths.sessions_jsonl 경로 업데이트")
        print(f"  2. session-lifecycle.md에 wiki 스니펫 삽입")
        print(f"     참조: ~/.claude/skills/TWK/templates/rule-snippets/session-lifecycle-wiki-step.md")
        if mode in ("session-extract", "hybrid"):
            print(f"  3. (Mode B) 기존 세션 소급 추출:")
            print(f"     python ~/.claude/skills/TWK/scripts/extract_session_raw.py --config wiki.config.json --backfill")
    else:
        print("\n[init_wiki] dry-run 완료 — 실제 파일 변경 없음.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
