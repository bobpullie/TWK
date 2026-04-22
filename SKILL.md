---
name: TWK
upstream: https://github.com/bobpullie/TWK
update_cmd: git -C "$HOME/.claude/skills/TWK" pull origin main
description: >
  TriadWiKi (TWK) — Karpathy LLM Wiki 방법론 Triad Chord Studio 전용 구현체 (구 llm-wiki). 3-Layer (Raw / Wiki / Schema) +
  3 Operations (Ingest / Query / Lint) + Compilation > RAG 원칙.
  에이전트별 도메인 특화는 wiki.config.json으로 분리; 핵심 원칙·템플릿·스크립트는 공통 자산.
triggers:
  - "wiki ingest"
  - "wiki query"
  - "wiki lint"
  - "지식 베이스 구축"
  - "TWK 초기화"
  - "init_wiki"
  - "session artifacts"
  - "세션 산출물 인덱스"
  - "normalize_session_frontmatter"
---

# TriadWiKi (TWK) Skill

> "The key insight is that the wiki is a persistent, compounding artifact — not a
> conversation. Each session adds to it and never takes away."
> — Andrej Karpathy, *llm.wiki* gist

## 언제 사용하는가

| 상황 | 트리거 |
|------|--------|
| 새 에이전트 프로젝트에 wiki 구조를 초기화할 때 | "wiki 만들어줘", "init_wiki" |
| 새 자료(논문·로그·핸드오버)를 wiki에 흡수할 때 | "wiki ingest \<source\>" |
| 기존 wiki에서 선행 지식을 합성해 답변할 때 | "wiki query \<topic\>" |
| wiki 건강도 점검 (모순/stale/고아 탐지) 시 | "wiki lint", 주기 자동 |
| 세션 종료 시 L2 archive + L3 wiki 갱신 시 | session-lifecycle Step N |
| 세션 산출물(L2+handover+recap+L3) frontmatter 자동 정규화 + 통합 타임라인 | `normalize_session_frontmatter.py --apply` (lifecycle step) |

---

## 핵심 원칙 (Karpathy)

1. **Compilation > RAG** — 쿼리 시점 검색 대신 지식을 미리 컴파일해 누적.
   > "Instead of retrieval, compilation: each new piece of information is integrated
   > into the wiki at ingest time, so query is just reading, not searching."

2. **Persistent & Compounding** — wiki는 세션이 끝나도 남아 쌓인다.
   > "The wiki grows with each session. Nothing is deleted — only superseded."

3. **Human Curation, LLM Bookkeeping** — 방향 결정은 인간, 유지·갱신은 LLM.
   > "Humans do curation and direction. LLMs do the bookkeeping."

4. **Cross-Reference First** — 단일 페이지 답변 금지. 여러 페이지 교차 참조로 합성.

5. **Append-Only Log** — `log.md`는 삭제 없이 append만. 지식 이력 보존.

---

## 3-Layer 아키텍처

| Layer | 이름 | 권한 | 내용 | 예시 |
|-------|------|------|------|------|
| **L1** | Raw Sources | Immutable (읽기 전용) | 원본 세션 JSONL, 논문 PDF, 로그 파일 | `~/.claude/projects/<uuid>/*.jsonl` |
| **L2** | Session Archive | LLM 자동 생성, 인간 읽기 전용 | 기계적 Q&A 추출물 (0 토큰, 정보 손실 없음) | `docs/session_archive/YYYYMMDD_sN_raw.md` |
| **L3** | Wiki | LLM 유지·갱신, 인간 큐레이션 | 결정·아키텍처·원리·개념 압축 | `docs/wiki/{decisions,concepts,principles}/` |

> **L2는 Mode B 전용** (Session-Extract). Mode A (Karpathy Pure)에서는 L1 raw/ 폴더가 L2 역할을 겸한다.

---

## 3 Operations

| Operation | 트리거 | 주체 | 산출물 |
|-----------|--------|------|--------|
| **Ingest** | 새 source 도입, 실험 결과 확정 | Sonnet 서브에이전트 (위임) | wiki/ 페이지 업데이트, log.md 1행, index.md 등록 |
| **Query** | 선행 지식 조회, 설계 분기 전 조사 | Sonnet Executor (또는 직접 탐색) | 교차 참조 합성 답변, 필요 시 신규 concept/principle 페이지 |
| **Lint** | 5 세션마다 / 10 페이지 추가 시 | Sonnet 위임 or 수동 트리거 | log.md Lint 섹션, 수정 이슈 리스트 |

상세 절차: [`references/operations.md`](references/operations.md)

### 보조 Operation — Session Artifacts Normalize (v1.2~)

세션 종료 시점에 L2 raw · 핸드오버 · recap 등 **wiki 외부 세션 산출물** 의 frontmatter 를 idempotent 하게 자동 주입하고, Dataview 기반 통합 타임라인(`session_artifacts.md`)을 통해 4 폴더를 한 눈에 볼 수 있게 하는 보조 operation.

| 항목 | 값 |
|------|-----|
| 스크립트 | `scripts/normalize_session_frontmatter.py` |
| 설정 | `wiki.config.json` 의 `session_artifacts` 섹션 (folders · date_patterns · wiki_validate_root) |
| 주입 필드 | `date` · `type` · `cssclass` · `tags` · `session` |
| 병합 규칙 | 스칼라: 기존 값 skip · 배열(tags): union (기존 보존 + 누락분 append) |
| Idempotency | 2회차 apply 시 `kept` 만 반환. 재호출 안전 |
| wiki root | 검증만 (필수 필드 `date`·`status` 체크, 쓰기 없음) |
| 템플릿 | `templates/session_artifacts.md.template` (`docs/session_artifacts.md` 로 복사 후 FROM 절 조정) |

**사용 예** (세션 종료 lifecycle step):
```bash
python ~/.claude/skills/TWK/scripts/normalize_session_frontmatter.py --apply
```

---

## Mode A vs Mode B

| 항목 | Mode A — Karpathy Pure | Mode B — Session-Extract |
|------|------------------------|--------------------------|
| L1 소스 | `raw/` 폴더 (논문, 로그, junction) | `~/.claude/projects/<uuid>/*.jsonl` |
| L2 존재 | 없음 (L1이 raw 역할 겸임) | `session_archive/` 기계적 Q&A 추출 |
| L3 생성 | wiki/ 직접 Ingest | extract → 세션 종료 시 wiki 엔트리 추출 |
| 적합한 경우 | 논문·실험 로그 중심 연구 도메인 | LLM 세션이 주 지식 원천인 에이전트 |
| 대표 사례 | 코드군 (FermionQuant) | 리얼군 (Unreal Engine) |
| extract 스크립트 | 불필요 | `scripts/extract_session_raw.py` |

**Hybrid**: 두 모드 동시 사용 가능. L1 raw/에 외부 자료를 두고 L2 session_archive/도 운영.

상세: [`references/3-layer-architecture.md`](references/3-layer-architecture.md)

---

## Frontmatter 계약 (Dataview + Calendar 호환)

모든 L3 wiki 페이지는 다음 통일 frontmatter 를 갖는다. lint.py 가 강제 검증.

```yaml
---
date: 2026-04-20          # 인용 금지 — Dataview Date coerce, Calendar default format
status: Active            # Draft | Active | Accepted | Implemented | Superseded | Archived
aliases: []
tags: [decision, tems]    # 복수형 필수
phase: ""
scope: ""
cssclass: twk-decision    # 템플릿별 고유
---
```

**필수:** `date`, `status`. **선택:** `aliases`, `tags`, `phase`, `scope`, `project`, `cssclass`.

**엄격 규칙:**
- `date` 는 반드시 ISO `YYYY-MM-DD` 무인용. 인용하면 Dataview 가 Text 로 인식하여 날짜 비교·Calendar 교차 쿼리가 깨진다.
- `tags` 는 복수형 (`tag:` 단수는 Obsidian 인덱싱 안 됨).
- Calendar plugin 은 frontmatter `date` 를 직접 읽지 않으므로, Daily Note 파일명(`YYYY-MM-DD.md`) 과 연동해 Dataview 쿼리(`WHERE date = this.file.day`) 로 백링크.

상세: [`references/obsidian-integration.md`](references/obsidian-integration.md).
템플릿: [`templates/page-templates/`](templates/page-templates/) 7종 (decision/concept/principle/postmortem/idea/entity/daily-note).

---

## 프로젝트별 customization — `wiki.config.json`

모든 프로젝트 특화 설정은 `wiki.config.json` 하나로 관리. 스킬 자체는 수정 불필요.

```json
{
  "version": "1.0",
  "project_id": "my-agent",
  "mode": "session-extract",
  "paths": {
    "wiki_root": "docs/wiki",
    "raw_root": "fermion_wiki/raw",
    "session_archive_root": "docs/session_archive",
    "sessions_jsonl": "~/.claude/projects/<agent-uuid>/*.jsonl"
  },
  "sections": [
    {"name": "decisions",   "template": "decision",  "phase_tag": null},
    {"name": "concepts",    "template": "concept",   "phase_tag": null},
    {"name": "principles",  "template": "principle", "phase_tag": null}
  ],
  "auditors": [],
  "lint_cadence": {"every_sessions": 5, "every_pages": 10},
  "obsidian": {"vault_path": ".", "dataview_enabled": true}
}
```

템플릿: [`templates/wiki.config.json.template`](templates/wiki.config.json.template)

---

## 글로벌 vs 로컬 책임 분리

| 글로벌 스킬 (`~/.claude/skills/TWK/`) | 로컬 프로젝트 |
|---------------------------------------------|--------------|
| 원칙·운영 방법론 (SKILL.md + references/) | 실제 wiki/ 파일들 |
| 페이지 템플릿 (templates/page-templates/) | wiki.config.json |
| 스키마 템플릿 (templates/schema/) | session-lifecycle.md 통합 스니펫 |
| 스크립트 (scripts/) | 프로젝트별 Auditor 정의 |
| session-lifecycle 스니펫 | — |

---

## 워크플로 통합

### session-lifecycle 통합
`templates/rule-snippets/session-lifecycle-wiki-step.md`를 프로젝트의
`session-lifecycle.md`에 복사 삽입. Mode A/B 각각 스니펫 제공.

### subagent-brief 연계
- **Ingest / Lint** → Sonnet 서브에이전트 위임 기본
  ```
  Task: [Wiki Ingest] <source 요약>
  Target: wiki/ 관련 섹션
  Rule: RAG 금지, Compilation 원칙, cross-reference 우선
  Output: 업데이트된 페이지 목록 + log.md append
  ```
- **Query** → 복잡도에 따라 분기
  - 단순 조회: 에이전트 직접 수행
  - 교차 합성 필요: Sonnet 위임
  - 원리 승격 판단: Opus Advisor 호출

---

## 설치 절차

```bash
# 1. 새 프로젝트에 wiki 구조 초기화
python ~/.claude/skills/TWK/scripts/init_wiki.py \
  --mode B \
  --wiki-root docs/wiki \
  --sections decisions,concepts,principles \
  --project-id my-agent

# 2. wiki.config.json 수정 (sessions_jsonl 경로 등)

# 3. session-lifecycle.md에 wiki 스니펫 삽입
# templates/rule-snippets/session-lifecycle-wiki-step.md 참조

# 4. (Mode B) 기존 세션 소급 추출
python ~/.claude/skills/TWK/scripts/extract_session_raw.py \
  --config ./wiki.config.json --backfill

# 5. (선택) Lint 실행
python ~/.claude/skills/TWK/scripts/lint.py \
  --config ./wiki.config.json
```

---

## References

| 파일 | 내용 |
|------|------|
| [`references/karpathy-principles.md`](references/karpathy-principles.md) | 원칙 + 원문 인용 7개 |
| [`references/3-layer-architecture.md`](references/3-layer-architecture.md) | L1/L2/L3 상세 + Mode A/B 디렉토리 구조 |
| [`references/operations.md`](references/operations.md) | Ingest/Query/Lint 상세 절차 |
| [`references/obsidian-integration.md`](references/obsidian-integration.md) | wikilink/backlink/Dataview/QMD 연동 |
| [`references/project-integration.md`](references/project-integration.md) | 리얼군·코드군 케이스 스터디 + 결정 가이드 |
