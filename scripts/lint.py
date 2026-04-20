"""LLM Wiki universal linter.

범용 wiki 건전성 점검 스크립트.
점검 항목: orphan pages / dangling wikilinks / stale pages / missing frontmatter

Usage:
    python lint.py --config wiki.config.json            # 전체 점검
    python lint.py --config wiki.config.json --dry-run  # 파일 수정 없이 보고만
    python lint.py --config wiki.config.json --check orphan
    python lint.py --config wiki.config.json --check stale --stale-days 30
    python lint.py --config wiki.config.json --check dangling
    python lint.py --config wiki.config.json --check frontmatter
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import NamedTuple

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:[|#][^\]]*?)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

# Dataview/Calendar 호환 검증용 정규식
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")
QUOTED_RE = re.compile(r'^[\'"].*[\'"]$')


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_wiki_root(config: dict, config_dir: Path) -> Path:
    wiki_root = config.get("paths", {}).get("wiki_root", "docs/wiki")
    p = Path(wiki_root)
    if not p.is_absolute():
        p = config_dir / p
    return p.resolve()


def get_required_fields(config: dict) -> list[str]:
    return config.get("frontmatter", {}).get("required_fields", [])


def get_stale_days(config: dict) -> int:
    return config.get("lint", {}).get("stale_days", 30)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class LintIssue(NamedTuple):
    kind: str        # orphan | dangling | stale | frontmatter
    path: Path
    detail: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_md_files(wiki_root: Path) -> list[Path]:
    if not wiki_root.exists():
        return []
    return [
        p for p in wiki_root.rglob("*.md")
        if p.name not in ("index.md", "log.md")
    ]


def collect_index_links(wiki_root: Path) -> set[str]:
    """index.md에 등록된 wikilink 타겟 집합."""
    index = wiki_root / "index.md"
    if not index.exists():
        return set()
    text = index.read_text(encoding="utf-8", errors="ignore")
    return {m.group(1).strip() for m in WIKILINK_RE.finditer(text)}


def extract_wikilinks(text: str) -> list[str]:
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(text)]


def parse_frontmatter(text: str) -> dict:
    """Values 에서 따옴표를 제거한 표준 dict 반환 (검증 완료 후 조회용).

    원문 그대로(quote 포함)가 필요하면 parse_frontmatter_raw 사용.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    result: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def parse_frontmatter_raw(text: str) -> dict:
    """원문 값(따옴표·리스트 기호 포함) 그대로 반환. 검증용."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    result: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def build_all_page_names(md_files: list[Path], wiki_root: Path) -> set[str]:
    """위키 내 모든 페이지 이름 집합 (확장자 없이, 상대경로 포함)."""
    names: set[str] = set()
    for f in md_files:
        # 파일명만
        names.add(f.stem)
        # wiki_root 기준 상대경로 (확장자 없이)
        try:
            rel = f.relative_to(wiki_root)
            names.add(str(rel.with_suffix("")).replace("\\", "/"))
            names.add(str(rel.with_suffix("")))
        except ValueError:
            pass
    return names


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_orphan(md_files: list[Path], wiki_root: Path) -> list[LintIssue]:
    """어떤 페이지에서도 wikilink 역참조가 없는 페이지."""
    issues: list[LintIssue] = []
    # 모든 페이지에서 나가는 wikilink 수집
    referenced: set[str] = set()
    index_links = collect_index_links(wiki_root)
    referenced.update(index_links)

    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for link in extract_wikilinks(text):
            referenced.add(link.strip())
            referenced.add(link.split("/")[-1])  # 마지막 세그먼트도 추가

    for f in md_files:
        name = f.stem
        rel = str(f.relative_to(wiki_root).with_suffix("")).replace("\\", "/")
        if name not in referenced and rel not in referenced:
            issues.append(LintIssue(
                kind="orphan",
                path=f,
                detail=f"backlink 없음 (index.md 포함 어디서도 참조 안 됨)",
            ))
    return issues


def check_dangling(md_files: list[Path], wiki_root: Path) -> list[LintIssue]:
    """[[X]] 링크가 실제 파일을 가리키지 않는 경우."""
    issues: list[LintIssue] = []
    all_names = build_all_page_names(md_files, wiki_root)
    # index.md, log.md도 유효 이름에 추가
    all_names.add("index")
    all_names.add("log")

    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for link in extract_wikilinks(text):
            target = link.strip()
            # 외부 링크(http) 무시
            if target.startswith("http"):
                continue
            # 상대경로 정규화: ../xxx → xxx
            target_stem = target.split("/")[-1].replace(".md", "")
            if target_stem not in all_names and target not in all_names:
                issues.append(LintIssue(
                    kind="dangling",
                    path=f,
                    detail=f"[[{link}]] → 대상 파일 없음",
                ))
    return issues


def check_stale(md_files: list[Path], stale_days: int) -> list[LintIssue]:
    """frontmatter date 기준 N일 초과 + status Active인 페이지."""
    issues: list[LintIssue] = []
    threshold = date.today() - timedelta(days=stale_days)

    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        fm = parse_frontmatter(text)
        if not fm:
            continue
        status = fm.get("status", "")
        date_str = fm.get("date", "")
        if status.lower() not in ("active", "draft"):
            continue
        if not date_str:
            continue
        try:
            page_date = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if page_date < threshold:
            delta = (date.today() - page_date).days
            issues.append(LintIssue(
                kind="stale",
                path=f,
                detail=f"마지막 갱신 {delta}일 전 (status={status})",
            ))
    return issues


def check_frontmatter(md_files: list[Path], required_fields: list[str]) -> list[LintIssue]:
    """필수 frontmatter 필드 누락 + Dataview/Calendar 호환성 점검.

    검사 항목:
      1) 필수 필드 누락 (config.frontmatter.required_fields)
      2) date 인용 금지 (Dataview Date coerce 차단)
      3) date ISO 포맷 (YYYY-MM-DD) — Calendar plugin 기본 format 일치
      4) 단수형 `tag:` 사용 금지 (Obsidian/Dataview 는 tags 복수형만 인덱싱)
    """
    issues: list[LintIssue] = []

    for f in md_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        raw = parse_frontmatter_raw(text)
        fm = parse_frontmatter(text)

        # (1) frontmatter 자체가 없으면 스킵 (다른 lint 에서 커버)
        if not raw:
            if required_fields:
                issues.append(LintIssue(
                    kind="frontmatter",
                    path=f,
                    detail="frontmatter 블록이 없음",
                ))
            continue

        # (2) 필수 필드
        missing = [field for field in required_fields if field not in fm]
        if missing:
            issues.append(LintIssue(
                kind="frontmatter",
                path=f,
                detail=f"필수 필드 누락: {', '.join(missing)}",
            ))

        # (3) date 검증
        date_raw = raw.get("date", "")
        date_clean = fm.get("date", "")
        if date_raw:
            if QUOTED_RE.match(date_raw):
                issues.append(LintIssue(
                    kind="frontmatter",
                    path=f,
                    detail=(
                        f"date 값이 인용 처리됨({date_raw}). "
                        "Dataview 가 Text 로 처리하여 Date 비교·Calendar 연동이 깨진다. "
                        "따옴표 제거 권장."
                    ),
                ))
            elif date_clean and not (
                ISO_DATE_RE.match(date_clean) or ISO_DATETIME_RE.match(date_clean)
            ):
                issues.append(LintIssue(
                    kind="frontmatter",
                    path=f,
                    detail=(
                        f"date 포맷 비표준({date_clean}). "
                        "Dataview + Calendar 호환을 위해 YYYY-MM-DD 권장."
                    ),
                ))

        # (4) 단수형 tag:
        if "tag" in raw and "tags" not in raw:
            issues.append(LintIssue(
                kind="frontmatter",
                path=f,
                detail="단수 `tag:` 사용 중. Obsidian/Dataview 는 `tags:` 복수형만 인덱싱.",
            ))

    return issues


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(issues: list[LintIssue], wiki_root: Path) -> None:
    by_kind: dict[str, list[LintIssue]] = {}
    for issue in issues:
        by_kind.setdefault(issue.kind, []).append(issue)

    kind_labels = {
        "orphan": "고아 페이지 (backlink 없음)",
        "dangling": "끊어진 wikilink",
        "stale": "Stale 페이지",
        "frontmatter": "frontmatter 누락",
    }

    total = len(issues)
    if total == 0:
        print("[lint] 이슈 없음 — wiki 건강 양호")
        return

    print(f"[lint] 총 {total}건 발견\n")
    for kind, label in kind_labels.items():
        items = by_kind.get(kind, [])
        if not items:
            continue
        print(f"## {label} ({len(items)}건)")
        for issue in items:
            try:
                rel = issue.path.relative_to(wiki_root)
            except ValueError:
                rel = issue.path
            print(f"  - {rel}: {issue.detail}")
        print()


def append_log(log_path: Path, issues: list[LintIssue]) -> None:
    """log.md에 Lint 결과 append."""
    counts = {}
    for issue in issues:
        counts[issue.kind] = counts.get(issue.kind, 0) + 1

    today = datetime.now().strftime("%Y-%m-%d")
    summary = (
        f"모순 {counts.get('contradiction', 0)}건 / "
        f"Stale {counts.get('stale', 0)}건 / "
        f"고아 {counts.get('orphan', 0)}건 / "
        f"공백 {counts.get('frontmatter', 0)}건"
    )
    entry = f"\n## {today} — [Lint] {summary}\n"

    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8")
        log_path.write_text(existing + entry, encoding="utf-8")
    else:
        log_path.write_text(f"# Wiki Change Log\n{entry}", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--config",
        default="wiki.config.json",
        help="wiki.config.json 경로 (기본: ./wiki.config.json)",
    )
    ap.add_argument(
        "--check",
        choices=["orphan", "dangling", "stale", "frontmatter", "all"],
        default="all",
        help="점검 항목 선택 (기본: all)",
    )
    ap.add_argument(
        "--stale-days",
        type=int,
        default=None,
        help="Stale 기준 일수 (config보다 우선)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="파일 수정(log.md append) 없이 보고만",
    )
    ap.add_argument(
        "--no-log",
        action="store_true",
        help="log.md에 기록하지 않음",
    )
    args = ap.parse_args()

    config_path = Path(args.config)
    config_dir = config_path.parent.resolve()
    config = load_config(config_path)

    wiki_root = get_wiki_root(config, config_dir)
    required_fields = get_required_fields(config)
    stale_days = args.stale_days or get_stale_days(config)

    if not wiki_root.exists():
        print(f"[error] wiki_root 없음: {wiki_root}", file=sys.stderr)
        return 1

    md_files = collect_md_files(wiki_root)
    if not md_files:
        print(f"[lint] wiki_root에 .md 파일 없음: {wiki_root}")
        return 0

    print(f"[lint] 점검 중: {wiki_root} ({len(md_files)}개 파일)\n", file=sys.stderr)

    all_issues: list[LintIssue] = []
    check = args.check

    if check in ("orphan", "all"):
        all_issues.extend(check_orphan(md_files, wiki_root))
    if check in ("dangling", "all"):
        all_issues.extend(check_dangling(md_files, wiki_root))
    if check in ("stale", "all"):
        all_issues.extend(check_stale(md_files, stale_days))
    if check in ("frontmatter", "all"):
        all_issues.extend(check_frontmatter(md_files, required_fields))

    print_report(all_issues, wiki_root)

    if not args.dry_run and not args.no_log and all_issues:
        log_path = wiki_root / "log.md"
        append_log(log_path, all_issues)
        print(f"[lint] log.md 기록 완료: {log_path}", file=sys.stderr)

    return 0 if not all_issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
