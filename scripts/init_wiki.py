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

LOG_MD_TEMPLATE = """\
# Wiki Change Log

> append-only. 삭제 금지. 최신이 위.

## {today} — [Init] wiki 초기화 | 섹션: {sections}
"""

# ----------------------------------------------------------------------------
# index.md 템플릿 파일 (위상군 스타일) — TWK v1.2+
# ----------------------------------------------------------------------------
INDEX_TEMPLATE_FILE = TEMPLATES_DIR / "index.md.template"
INDEX_SECTION_BLOCK_TEMPLATE_FILE = TEMPLATES_DIR / "index_section_block.md.template"
SESSION_ARTIFACTS_TEMPLATE_FILE = TEMPLATES_DIR / "session_artifacts.md.template"

SECTION_LABELS = {
    "ideas": "아이디어",
    "hypotheses": "가설",
    "strategies": "전략",
    "systems": "시스템",
    "indicators": "지표",
    "concepts": "개념",
    "backtests": "백테스트",
    "postmortems": "사후분석",
    "diagnostics": "진단",
    "principles": "원리",
    "decisions": "결정",
    "patterns": "패턴",
    "architecture": "아키텍처",
    "pipeline": "파이프라인",
    "reference": "레퍼런스",
}

SECTION_DESCS = {
    "ideas": "아이디어 단계 (HDIL P1~P3)",
    "hypotheses": "검증 가능 가설 (HDIL P3)",
    "strategies": "활성 / 동결 / 폐기 전략",
    "systems": "엔진·데이터·파이프라인 런타임 시스템",
    "indicators": "매크로·기술 지표",
    "concepts": "수식·원리·용어 정의",
    "backtests": "백테스트·Ablation·A/B·WF 검증 기록",
    "postmortems": "실제 실패·성공 원인 분석 (HDIL P5·P6)",
    "diagnostics": "실패 원인 진단·밸런싱 (HDIL P7)",
    "principles": "Doctrine 편입 후보 (HDIL P10)",
    "decisions": "아키텍처·정책 결정 (ADR)",
    "patterns": "반복되는 위상 패턴",
    "architecture": "시스템 아키텍처",
    "pipeline": "데이터·배포 파이프라인",
    "reference": "외부 레퍼런스·링크",
}

SECTION_CALLOUTS = {
    "ideas": "example",
    "hypotheses": "example",
    "strategies": "check",
    "systems": "info",
    "indicators": "info",
    "concepts": "info",
    "backtests": "abstract",
    "postmortems": "bug",
    "diagnostics": "warning",
    "principles": "quote",
    "decisions": "check",
    "patterns": "abstract",
    "architecture": "info",
    "pipeline": "info",
    "reference": "info",
}

# date 기반 정렬이 의미있는 섹션 vs 이름 기반
SECTION_SORT_BY_DATE = {
    "ideas", "hypotheses", "backtests", "postmortems",
    "diagnostics", "decisions",
}

# phase 컬럼을 표시할 섹션
SECTION_SHOW_PHASE = {
    "ideas", "hypotheses", "backtests", "diagnostics",
}


def _load_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _render_section_block(section: str, wiki_root_str: str) -> str:
    """섹션 이름 하나를 받아 Dataview 블록 생성."""
    template = _load_template(INDEX_SECTION_BLOCK_TEMPLATE_FILE)
    # 주석(<!-- ... -->) 제거 (init_wiki 문맥에선 불필요)
    template = _strip_html_comments(template)

    label = SECTION_LABELS.get(section, section.capitalize())
    desc = SECTION_DESCS.get(section, "")
    callout = SECTION_CALLOUTS.get(section, "info")
    sort_field = "date DESC" if section in SECTION_SORT_BY_DATE else "file.name ASC"

    # Dataview 컬럼 구성 (phase 포함 여부)
    col_entity = SECTION_LABELS.get(section, section.capitalize())
    if section in SECTION_SHOW_PHASE:
        columns = (
            f'  file.link as "{col_entity}",\n'
            f'  status as "상태",\n'
            f'  phase as "Phase",\n'
            f'  date as "날짜"'
        )
    elif section in SECTION_SORT_BY_DATE:
        columns = (
            f'  file.link as "{col_entity}",\n'
            f'  status as "상태",\n'
            f'  date as "날짜"'
        )
    else:
        columns = (
            f'  file.link as "{col_entity}",\n'
            f'  status as "상태",\n'
            f'  scope as "범위"'
        )

    replacements = {
        "{{SECTION_NAME}}": section,
        "{{SECTION_NAME_TITLE}}": section.capitalize(),
        "{{SECTION_LABEL}}": label,
        "{{SECTION_DESC}}": desc,
        "{{CALLOUT_TYPE}}": callout,
        "{{DATAVIEW_COLUMNS}}": columns,
        "{{WIKI_ROOT}}": wiki_root_str,
        "{{SORT_FIELD}}": sort_field,
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def _strip_html_comments(text: str) -> str:
    """<!-- ... --> 블록 (멀티라인) 제거. 템플릿 내부 주석을 최종 산출물에서 제외."""
    import re
    return re.sub(r"<!--.*?-->\s*", "", text, flags=re.DOTALL)


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
    """index.md 본문 생성 — 위상군 스타일 템플릿 기반 (v1.2+).

    `dataview_enabled=False` 인 경우에도 템플릿 뼈대는 유지 (Dataview 블록은 코드펜스로 렌더만
    안 될 뿐). 기존 프로젝트 입장에서 호환성 유지.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    template = _load_template(INDEX_TEMPLATE_FILE)
    # 템플릿 머리의 <!-- ... --> 주석 블록 제거 (최종 index.md 에 안 노출)
    template = _strip_html_comments(template)

    sections_blocks = "\n---\n\n".join(
        _render_section_block(s, wiki_root_str) for s in sections
    )

    replacements = {
        "{{PROJECT_ID}}": project_id,
        "{{PROJECT_ID_LOWER}}": project_id.lower(),
        "{{TODAY}}": today,
        "{{WIKI_ROOT}}": wiki_root_str,
        "{{SECTIONS_BLOCKS}}": sections_blocks,
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


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

    # session_artifacts.md — 위상군 스타일 index embed 대상 (TWK v1.2+)
    # 배치 관행: wiki_root 의 부모 디렉토리 (index 와 동일 depth 에서 한 단계 상위).
    # 예) wiki_root=docs/wiki → docs/session_artifacts.md
    # Obsidian shortest-path resolution 으로 `![[session_artifacts]]` 가 index 에서 해석됨.
    if SESSION_ARTIFACTS_TEMPLATE_FILE.exists():
        session_artifacts_dst = wiki_root.parent / "session_artifacts.md"
        actions.append((
            "copy_if_missing",
            session_artifacts_dst,
            str(SESSION_ARTIFACTS_TEMPLATE_FILE),
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
        elif action_type == "copy_if_missing":
            src_path = Path(extra)
            if target.exists():
                print(f"[skip] {target} (이미 존재 — 덮어쓰지 않음)")
            elif dry_run:
                print(f"[dry-run] copy_if_missing {src_path.name} → {target}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, target)
                print(f"[ok] copy_if_missing {src_path.name} → {target}")


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
