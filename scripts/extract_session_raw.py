"""Extract raw Q&A from a Claude Code session JSONL.

Generic version of the Mode B session extractor.
원본: E:/00_unrealAgent/scripts/extract_session_raw.py (리얼군 특화) → config 기반으로 범용화.

기계적 추출 (토큰 소모 0) — user text + assistant text 만 Q1/A1/Q2/A2... 포맷으로 dump.
제외: tool_use, tool_result, thinking, sidechain (서브에이전트), isMeta, 시스템 주입 래퍼.

Usage:
    python extract_session_raw.py --config wiki.config.json           # config 기반 (latest JSONL)
    python extract_session_raw.py --config wiki.config.json --backfill  # 전체 소급 추출
    python extract_session_raw.py --project-uuid <UUID>               # UUID 직접 지정
    python extract_session_raw.py --jsonl <PATH>                      # JSONL 경로 직접
    python extract_session_raw.py --config wiki.config.json --dry-run # stdout만, 파일 저장 없음
    python extract_session_raw.py --session-id <SESSION_UUID>         # 특정 세션 UUID
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 시스템 주입 래퍼 태그 제거용 정규식
SYSTEM_WRAPPER_RE = re.compile(
    r"<(ide_opened_file|ide_selection|system-reminder|command-name|command-message|"
    r"command-args|local-command-stdout|local-command-stderr|user-prompt-submit-hook|"
    r"preflight-memory-check)>.*?</\1>",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    """wiki.config.json 로드. 없으면 기본값 반환."""
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def resolve_paths(config: dict, config_dir: Path) -> tuple[Path, Path]:
    """config에서 sessions_jsonl glob 패턴과 session_archive_root를 해석.

    Returns:
        (sessions_dir, output_dir)
    """
    paths = config.get("paths", {})

    # sessions_jsonl에서 디렉토리 추출
    sessions_jsonl = paths.get("sessions_jsonl", "")
    if sessions_jsonl:
        sessions_jsonl_expanded = sessions_jsonl.replace(
            "~", str(Path.home())
        )
        # glob 패턴에서 디렉토리 부분 추출 (마지막 /이전)
        sessions_dir = Path(sessions_jsonl_expanded).parent
    else:
        sessions_dir = Path.home() / ".claude" / "projects"

    # session_archive_root 해석
    archive_root = paths.get("session_archive_root", "docs/session_archive")
    if not Path(archive_root).is_absolute():
        output_dir = config_dir / archive_root
    else:
        output_dir = Path(archive_root)

    return sessions_dir, output_dir


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def clean_user_text(s: str) -> str:
    s = SYSTEM_WRAPPER_RE.sub("", s)
    return s.strip()


def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for b in content:
        if isinstance(b, dict) and b.get("type") == "text":
            t = b.get("text") or ""
            if t:
                parts.append(t)
    return "\n\n".join(parts)


def iter_turns(jsonl_path: Path):
    """JSONL에서 (role, text) 튜플 yield. tool_use, thinking, sidechain 제외."""
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = r.get("type")
            if t not in ("user", "assistant"):
                continue
            if r.get("isMeta") or r.get("isSidechain"):
                continue
            content = (r.get("message") or {}).get("content")
            raw = extract_text(content)
            if t == "user":
                cleaned = clean_user_text(raw)
                if cleaned:
                    yield ("user", cleaned)
            else:
                text = raw.strip()
                if text:
                    yield ("assistant", text)


# ---------------------------------------------------------------------------
# Session numbering and dedup
# ---------------------------------------------------------------------------

def next_session_number(output_dir: Path, date_str: str) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    return len(list(output_dir.glob(f"{date_str}_session*_raw.md"))) + 1


def already_extracted(jsonl_path: Path, output_dir: Path) -> bool:
    """Source 헤더에 JSONL 파일명이 포함된 기존 파일이 있으면 이미 추출된 것."""
    marker = f"`{jsonl_path.name}`"
    for f in output_dir.glob("*_raw.md"):
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:300]
            if marker in head:
                return True
        except OSError:
            pass
    return False


def date_from_mtime(jsonl_path: Path) -> str:
    return datetime.fromtimestamp(jsonl_path.stat().st_mtime).strftime("%Y%m%d")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render(jsonl_path: Path, session_n: int, date_str: str) -> tuple[str, int, int]:
    date_display = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    lines = [
        f"# Session {session_n} — {date_display}",
        "",
        f"> Source: `{jsonl_path.name}`",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    q = a = 0
    for role, text in iter_turns(jsonl_path):
        if role == "user":
            q += 1
            lines += [f"## Q{q}", "", text, ""]
        else:
            a += 1
            lines += [f"## A{a}", "", text, ""]
    return "\n".join(lines), q, a


# ---------------------------------------------------------------------------
# JSONL discovery
# ---------------------------------------------------------------------------

def find_latest_jsonl(sessions_dir: Path) -> Path:
    if not sessions_dir.exists():
        sys.exit(f"[error] sessions_dir 없음: {sessions_dir}")
    jsonls = sorted(
        sessions_dir.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not jsonls:
        sys.exit(f"[error] JSONL 없음: {sessions_dir}")
    return jsonls[0]


def find_jsonl_by_id(sessions_dir: Path, session_id: str) -> Path:
    p = sessions_dir / f"{session_id}.jsonl"
    if not p.exists():
        sys.exit(f"[error] JSONL 없음: {p}")
    return p


# ---------------------------------------------------------------------------
# Extract one
# ---------------------------------------------------------------------------

def extract_one(jsonl_path: Path, output_dir: Path,
                date_str: str, dry_run: bool = False) -> bool:
    """단일 JSONL 추출. 성공 시 True, 빈 세션이면 False."""
    output_dir.mkdir(parents=True, exist_ok=True)
    session_n = next_session_number(output_dir, date_str)
    md, q, a = render(jsonl_path, session_n, date_str)
    if q == 0 and a == 0:
        return False
    if dry_run:
        sys.stdout.write(md)
        return True
    out_path = output_dir / f"{date_str}_session{session_n}_raw.md"
    out_path.write_text(md, encoding="utf-8")
    print(f"[ok] {out_path} (Q={q}, A={a})", file=sys.stderr)
    return True


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
        "--project-uuid",
        help="Claude Code project UUID (sessions_jsonl 대신 직접 지정)",
    )
    ap.add_argument(
        "--session-id",
        help="특정 Claude Code session UUID",
    )
    ap.add_argument(
        "--jsonl",
        help="JSONL 경로 직접 지정 (override)",
    )
    ap.add_argument(
        "--output-dir",
        help="session_archive 출력 디렉토리 (config.paths.session_archive_root 대신)",
    )
    ap.add_argument(
        "--backfill",
        action="store_true",
        help="sessions_dir 전체 JSONL 소급 추출 (이미 추출된 것 skip)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="파일 저장 없이 stdout으로만 출력",
    )
    args = ap.parse_args()

    # Config 로드
    config_path = Path(args.config)
    config_dir = config_path.parent.resolve()
    config = load_config(config_path)

    # 경로 해석
    if args.project_uuid:
        sessions_dir = Path.home() / ".claude" / "projects" / args.project_uuid
        _, default_output_dir = resolve_paths(config, config_dir)
    else:
        sessions_dir, default_output_dir = resolve_paths(config, config_dir)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else default_output_dir

    # --backfill 모드
    if args.backfill:
        if not sessions_dir.exists():
            sys.exit(f"[error] sessions_dir 없음: {sessions_dir}")
        jsonls = sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        total = skipped = done = empty = 0
        for jp in jsonls:
            total += 1
            if already_extracted(jp, output_dir):
                skipped += 1
                print(f"[skip] {jp.name} (이미 추출됨)", file=sys.stderr)
                continue
            date_str = date_from_mtime(jp)
            ok = extract_one(jp, output_dir, date_str, dry_run=args.dry_run)
            if ok:
                done += 1
            else:
                empty += 1
                print(f"[empty] {jp.name} (Q&A 없음)", file=sys.stderr)
        print(
            f"\n[backfill 완료] total={total} done={done} "
            f"skipped={skipped} empty={empty}",
            file=sys.stderr,
        )
        return 0

    # 단일 JSONL 처리
    if args.jsonl:
        jsonl_path = Path(args.jsonl)
        if not jsonl_path.exists():
            sys.exit(f"[error] JSONL 없음: {jsonl_path}")
        date_str = date_from_mtime(jsonl_path)
    elif args.session_id:
        jsonl_path = find_jsonl_by_id(sessions_dir, args.session_id)
        date_str = date_from_mtime(jsonl_path)
    else:
        jsonl_path = find_latest_jsonl(sessions_dir)
        date_str = datetime.now().strftime("%Y%m%d")  # 현재 세션 = today

    extract_one(jsonl_path, output_dir, date_str, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
