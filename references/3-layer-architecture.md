# 3-Layer Architecture — 상세 명세

## Layer 정의

### L1 — Raw Sources (Immutable)

| 속성 | 내용 |
|------|------|
| **목적** | 원본 보존. 절대 수정/삭제 없음 |
| **권한** | 읽기 전용 (LLM + 인간) |
| **형식** | JSONL, PDF, 로그 파일, 이미지 — 원본 그대로 |
| **예시 (Mode A)** | `raw/papers/`, `raw/backtest_logs/`, `raw/handover_archives/` |
| **예시 (Mode B)** | `~/.claude/projects/<agent-uuid>/*.jsonl` |

L1은 wiki의 "사실 기준" (source of truth). 나중에 wiki 내용이 의심스러울 때 여기서 검증.

### L2 — Session Archive (Mode B 전용)

| 속성 | 내용 |
|------|------|
| **목적** | L1 JSONL에서 인간 가독 Q&A를 기계적으로 추출 (토큰 소모 0) |
| **권한** | LLM 자동 생성, 인간 읽기 전용 |
| **형식** | `YYYYMMDD_session{N}_raw.md` (Q1/A1/Q2/A2 구조) |
| **제외 항목** | tool_use, tool_result, thinking, sidechain, isMeta, 시스템 주입 래퍼 |
| **생성 스크립트** | `scripts/extract_session_raw.py --config wiki.config.json` |

L2는 L3 wiki 작성의 원재료. "이 결정이 어떤 맥락에서 내려졌는지"를 L3에서 L2로 wikilink.

### L3 — Wiki (Curated Knowledge)

| 속성 | 내용 |
|------|------|
| **목적** | 정제된 지식 베이스. 6개월 후 새 에이전트가 보더라도 이해 가능한 수준 |
| **권한** | LLM 유지·갱신, 인간 큐레이션·방향 결정 |
| **형식** | Obsidian-compatible Markdown + wikilink |
| **필수 파일** | `index.md` (카탈로그), `log.md` (append-only 이력) |

---

## Mode A — Karpathy Pure

논문·실험 로그·외부 자료가 주 지식 원천인 도메인용.

```
project_root/
├── wiki.config.json
├── {wiki_root}/             # L3 Wiki (default: fermion_wiki/wiki/ or docs/wiki/)
│   ├── index.md
│   ├── log.md
│   ├── ideas/
│   ├── concepts/
│   ├── principles/
│   ├── postmortems/
│   └── [domain-sections]/  # config의 sections 목록에서 정의
│
├── raw/                     # L1 Raw Sources
│   ├── papers/
│   ├── logs/
│   ├── archives/
│   └── specs/
│
└── schema/                  # L3 Config
    ├── ingest.md
    ├── query.md
    ├── lint.md
    └── templates/
```

**특징:**
- L2 (session_archive) 없음
- `raw/`는 외부 디렉토리로의 junction/symlink 가능
- Ingest 시 `raw/`에 원본 경로 기록 후 wiki/ 업데이트

---

## Mode B — Session-Extract

LLM 세션이 주 지식 원천인 에이전트 도메인용.

```
project_root/
├── wiki.config.json
├── docs/
│   ├── session_archive/           # L2 — 기계적 Q&A 추출
│   │   └── YYYYMMDD_session{N}_raw.md
│   └── wiki/                      # L3 Wiki
│       ├── index.md
│       ├── log.md
│       └── [sections]/
│
└── scripts/
    └── (또는) ~/.claude/skills/TWK/scripts/extract_session_raw.py
```

**특징:**
- `extract_session_raw.py --config wiki.config.json` 로 L2 생성
- L3 wiki 엔트리에서 `[[../session_archive/YYYYMMDD_sN_raw]]`로 L2 drill-down
- `--backfill`로 전체 JSONL 소급 추출 가능

---

## Hybrid Mode

Mode A + Mode B 동시 운영. 외부 자료 + 세션 기록 모두 중요한 경우.

```
project_root/
├── wiki.config.json          # "mode": "hybrid"
├── raw/                      # L1a — 외부 자료
├── docs/
│   ├── session_archive/      # L1b/L2 — 세션 JSONL 추출물
│   └── wiki/                 # L3
└── schema/
```

---

## index.md 구조 (L3 진입점)

```markdown
# [Project] Wiki — Index

> 마지막 갱신: YYYY-MM-DD Session N

## [Section 1]
- [[page_name]] — 1줄 요약

## [Section 2]
- [[page_name]] — 1줄 요약

---
*관리: LLM (Ingest/Lint 시 자동 갱신), 큐레이션: 인간*
```

## log.md 구조 (append-only)

```markdown
# Wiki Change Log

## YYYY-MM-DD — [Ingest] source 요약 | 업데이트된 페이지 목록
## YYYY-MM-DD — [Query] 질문 요약 | 참조 페이지 목록
## YYYY-MM-DD — [Lint] 모순 N건 / Stale N건 / 고아 N건 / 공백 N건
```

최신이 위 또는 아래 — 프로젝트에서 통일. 한 번 정하면 변경 금지.
