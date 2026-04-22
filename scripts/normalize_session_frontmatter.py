"""세션 산출물 frontmatter 자동 정규화.

범위 C 폴더의 .md 파일에 누락된 frontmatter 필드(date · type · cssclass ·
tags · session)를 idempotent 하게 주입한다. wiki_validate_root 는 검증만.

폴더 목록·date 패턴·wiki root 는 `wiki.config.json` 의 `session_artifacts`
섹션에서 읽는다. 섹션 부재 시 기본값(위상군 3 폴더) 사용.

세션 종료 lifecycle step 5.5 에서 호출.
"""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)

FLOW_STYLE_KEYS = {"tags", "aliases"}

ARRAY_KEYS = {"tags", "aliases"}

SESSION_PATTERN = re.compile(r"[_-]s(?:ession)?(\d+)", re.IGNORECASE)

WIKI_REQUIRED_FIELDS = ["date", "status"]

DEFAULT_CONFIG_PATH = Path("wiki.config.json")

# `wiki.config.json` 에 session_artifacts 섹션이 없을 때의 fallback.
_DEFAULT_FOLDERS = [
    {"path": "docs/session_archive", "type": "raw", "cssclass": "twk-raw", "tags": ["session", "raw", "L2"]},
    {"path": "handover_doc", "type": "handover", "cssclass": "twk-handover", "tags": ["session", "handover"]},
    {"path": "qmd_drive/recaps", "type": "recap", "cssclass": "twk-recap", "tags": ["session", "recap"]},
]
_DEFAULT_DATE_PATTERNS = [r"^(\d{4})-(\d{2})-(\d{2})", r"^(\d{4})(\d{2})(\d{2})"]
_DEFAULT_WIKI_ROOT = "docs/wiki"


def load_runtime_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """`wiki.config.json` 의 session_artifacts 섹션을 로드 (defaults fallback)."""
    try:
        with open(config_path, encoding="utf-8") as f:
            sa = json.load(f).get("session_artifacts", {})
    except (FileNotFoundError, json.JSONDecodeError):
        sa = {}
    return {
        "folders": sa.get("folders", _DEFAULT_FOLDERS),
        "date_patterns": sa.get("date_patterns", _DEFAULT_DATE_PATTERNS),
        "wiki_validate_root": sa.get("wiki_validate_root", _DEFAULT_WIKI_ROOT),
    }


_runtime = load_runtime_config()

FOLDER_CONFIG = {
    f["path"]: {"type": f["type"], "cssclass": f["cssclass"], "tags": list(f["tags"])}
    for f in _runtime["folders"]
}

DATE_PATTERNS = [re.compile(p) for p in _runtime["date_patterns"]]

WIKI_ROOT = _runtime["wiki_validate_root"]

FOLDER_PATHS = {key: key for key in FOLDER_CONFIG}


def build_template(folder_key: str, filename: str, path: Path | None) -> dict:
    """폴더 config + 파일명 파싱 결과로 template dict 구성.

    Args:
        folder_key: FOLDER_CONFIG 의 키 (e.g. "handover_doc")
        filename: 파일 이름 (basename)
        path: mtime fallback 용 Path (없으면 mtime fallback 불가 — date 생략)

    Raises:
        KeyError: folder_key 가 FOLDER_CONFIG 에 없을 때
    """
    if folder_key not in FOLDER_CONFIG:
        raise KeyError(f"unknown folder: {folder_key}")
    base = FOLDER_CONFIG[folder_key]
    tpl: dict = {}
    date = extract_date_from_filename(filename)
    if date is None and path is not None:
        date = mtime_date(path)
    if date is not None:
        tpl["date"] = date
    tpl["type"] = base["type"]
    tpl["cssclass"] = base["cssclass"]
    tpl["tags"] = list(base["tags"])
    session = extract_session_from_filename(filename)
    if session:
        tpl["session"] = session
    return tpl


def mtime_date(path: Path) -> str:
    """파일 mtime 의 날짜 부분을 YYYY-MM-DD 로 반환."""
    ts = path.stat().st_mtime
    return datetime.date.fromtimestamp(ts).strftime("%Y-%m-%d")


def extract_date_from_filename(name: str) -> str | None:
    """파일명 맨 앞에서 YYYY-MM-DD 또는 YYYYMMDD 를 추출.

    성공 시 'YYYY-MM-DD' 문자열, 실패 시 None.
    """
    for pat in DATE_PATTERNS:
        m = pat.match(name)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            return f"{y}-{mo}-{d}"
    return None


def extract_session_from_filename(name: str) -> str | None:
    """파일명에서 'session{N}' 또는 's{N}' 패턴으로 session 번호 추출.

    성공 시 'S{N}', 실패 시 None.
    """
    m = SESSION_PATTERN.search(name)
    if m:
        return f"S{m.group(1)}"
    return None


def merge_frontmatter(existing: dict, template: dict) -> tuple[dict, bool]:
    """template 값을 existing 에 병합.

    규칙:
      - 스칼라: 기존 값 있으면 skip, 없을 때만 주입
      - 배열(tags/aliases): union 병합. 기존 순서 보존 + 누락분 append.

    Returns:
        (merged_dict, changed_flag)
    """
    result = dict(existing)
    changed = False
    for key, new_value in template.items():
        if key in ARRAY_KEYS:
            current = result.get(key, [])
            if not isinstance(current, list):
                current = [current]
            additions = [v for v in new_value if v not in current]
            if additions:
                result[key] = current + additions
                changed = True
            elif key not in result:
                result[key] = current
                changed = True
        else:
            if key not in result:
                result[key] = new_value
                changed = True
    return result, changed


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """markdown 문자열을 (frontmatter dict, body) 로 분리.

    frontmatter 가 없으면 ({}, content) 반환.
    """
    if not content:
        return {}, ""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    meta = yaml.load(m.group(1), Loader=yaml.BaseLoader) or {}
    body = content[m.end():]
    return meta, body


def process_file(path: Path, folder_key: str, dry_run: bool) -> str:
    """단일 파일에 frontmatter 병합 적용.

    Returns:
        "kept" | "updated" | "added" | "dry-run"
    """
    content = path.read_text(encoding="utf-8")
    existing_meta, body = parse_frontmatter(content)
    template = build_template(folder_key, path.name, path)
    merged_meta, changed = merge_frontmatter(existing_meta, template)

    if not changed:
        return "kept"
    if dry_run:
        return "dry-run"

    new_content = serialize_frontmatter(merged_meta, body)
    path.write_text(new_content, encoding="utf-8")
    return "added" if not existing_meta else "updated"


def validate_wiki_file(path: Path) -> list[str]:
    """docs/wiki/** 파일의 필수 필드 검증. 수정 없음.

    Returns:
        누락 필드별 warning 메시지 리스트. 이상 없으면 [].
    """
    content = path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(content)
    warnings = []
    for field in WIKI_REQUIRED_FIELDS:
        if field not in meta:
            warnings.append(f"{path.name}: '{field}' 누락")
    return warnings


def serialize_frontmatter(meta: dict, body: str) -> str:
    """(meta, body) 를 markdown 문자열로 합성.

    meta 가 비면 body 만 반환. tags/aliases 는 flow style (인라인) 로 출력.
    """
    if not meta:
        return body
    lines = []
    for key, value in meta.items():
        if key in FLOW_STYLE_KEYS and isinstance(value, list):
            joined = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{joined}]")
        elif isinstance(value, list):
            joined = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{joined}]")
        else:
            # yaml.safe_dump 으로 escape 처리 후 trailing newline 제거.
            # BaseLoader 로 parse 되므로 모든 scalar 는 str — PyYAML 이 date-like
            # 문자열에 자동으로 추가하는 quote 를 제거하여 round-trip 시 원본과
            # 동일한 표현 유지.
            dumped = yaml.safe_dump({key: value}, allow_unicode=True, default_flow_style=False)
            line = dumped.rstrip()
            # "key: 'value'" → "key: value" (ISO date 등 안전한 문자열만)
            prefix = f"{key}: "
            if line.startswith(prefix):
                rest = line[len(prefix):]
                if len(rest) >= 2 and rest[0] == "'" and rest[-1] == "'":
                    unquoted = rest[1:-1]
                    # escape 된 single quote 없고, 콜론/해시/YAML 특수문자 없을 때만
                    if "''" not in unquoted and not any(c in unquoted for c in ":#\n"):
                        line = f"{prefix}{unquoted}"
            lines.append(line)
    fm = "---\n" + "\n".join(lines) + "\n---\n"
    if body and not body.startswith("\n"):
        fm += "\n"
    return fm + body


import argparse
import sys


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--dry-run", action="store_true", help="실제 쓰기 없이 동작 확인")
    ap.add_argument("--apply", action="store_true", help="실제 적용")
    ap.add_argument(
        "--only",
        choices=list(FOLDER_PATHS.keys()) + ["wiki"],
        help="특정 폴더만 처리",
    )
    ap.add_argument("--project-root", default=".", help="프로젝트 루트 (기본: .)")
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        print("[error] --dry-run 또는 --apply 중 하나 필수", file=sys.stderr)
        return 2

    root = Path(args.project_root).resolve()

    # 처리 대상 결정
    if args.only == "wiki":
        return _run_wiki_validate(root)
    if args.only:
        folder_keys = [args.only]
    else:
        folder_keys = list(FOLDER_PATHS.keys())

    total_counts = {"added": 0, "updated": 0, "kept": 0, "dry-run": 0}
    for key in folder_keys:
        folder = root / FOLDER_PATHS[key]
        if not folder.exists():
            print(f"[warn] 폴더 없음: {folder}", file=sys.stderr)
            continue
        print(f"\n[{key}] scanning {folder} ...")
        for md in sorted(folder.rglob("*.md")):
            action = process_file(md, key, args.dry_run)
            rel = md.relative_to(root)
            print(f"  [{action:<8}] {rel}")
            total_counts[action] = total_counts.get(action, 0) + 1

    # wiki 검증 (--only 지정 안 했을 때만)
    if args.only is None:
        _run_wiki_validate(root)

    print(f"\n[summary] {total_counts}")
    return 0


def _run_wiki_validate(root: Path) -> int:
    wiki_dir = root / WIKI_ROOT
    if not wiki_dir.exists():
        print(f"[warn] wiki 폴더 없음: {wiki_dir}", file=sys.stderr)
        return 0
    print(f"\n[wiki validate] scanning {wiki_dir} ...")
    all_warnings = []
    for md in sorted(wiki_dir.rglob("*.md")):
        if md.name in {"log.md"}:
            continue
        warnings = validate_wiki_file(md)
        all_warnings.extend(warnings)
    if all_warnings:
        for w in all_warnings:
            print(f"  [warn] {w}", file=sys.stderr)
    else:
        print("  (이상 없음)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
