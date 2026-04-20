# 프로젝트 통합 케이스 스터디

## 케이스 1 — 리얼군 (Mode B, Session-Extract)

**프로젝트 경로:** `E:\00_unrealAgent`
**도메인:** Unreal Engine 씬 구축, Landscape/Material 시스템

### 선택 이유
- 에이전트-인간 대화 세션이 주 지식 원천
- 논문보다 실시간 구현 결정과 트러블슈팅이 중심
- L1 JSONL → L2 기계적 추출 → L3 결정·구조 패턴에 적합

### 레이어 매핑
| Layer | 경로 | 내용 |
|-------|------|------|
| L1 | `~/.claude/projects/e--00-unrealAgent/*.jsonl` | 원본 세션 JSONL (자동) |
| L2 | `docs/KJI_memo/YYYYMMDD_sessionN_raw.md` | Q&A 기계적 추출 (0 토큰) |
| L3 | `docs/wiki/{decisions,architecture,pipeline,reference}/` | 결정·구조 압축 |

### L3 섹션 구성
| 섹션 | 내용 | 파일명 규칙 |
|------|------|------------|
| `decisions/` | ADR 스타일 기술 결정 | `YYYY-MM-DD_<kebab>.md` |
| `architecture/` | 컴포넌트 구조, 책임 분리 | `<kebab>.md` |
| `pipeline/` | 입출력·트리거가 명확한 절차 | `<kebab>.md` |
| `reference/` | 속성표·비교표·수치 | `<kebab>.md` |

### Frontmatter 스타일 (YAML)
```yaml
---
date: 2026-04-20
status: Implemented
phase: 운영중
scope: 씬 렌더링 최적화
project: ALL
tags: [landscape, atlas, optimization]
---
```

### session-lifecycle 통합 포인트
```
Step 2.5 → extract_session_raw.py → L2 Q&A archive
Step 2.6 → L3 wiki 엔트리 추출·갱신 (의미있는 결정만)
[Stop Hook] → session_end_sync.py → QMD_drive/sessions/
```

### 도메인 특화 포인트 (범용화 시 제거된 것들)
- `KJI_memo/` 폴더명 → `session_archive/`로 일반화
- `e--00-unrealAgent` UUID 하드코딩 → `--config` 기반
- Dataview가 `decisions/` 자동 테이블화 (index.md에 쿼리 삽입)
- "6개월 뒤 이 프로젝트를 처음 보는 사람이 이해하도록" 가이드라인 → SKILL.md 원칙화

---

## 케이스 2 — 코드군 (Mode A, Karpathy Pure)

**프로젝트 경로:** `E:\QuantProject\DnT_Fermion`
**도메인:** 퀀트 리서치, 알고리즘 트레이딩 전략

### 선택 이유
- 논문·백테스트 로그·핸드오버 아카이브 등 외부 자료가 주 지식 원천
- HDIL 10-Phase 연구 사이클과 wiki 섹션을 1:1 매핑
- 엔티티 재사용 (지표·전략) 중심 — 세션 기반보다 엔티티 기반이 적합

### 레이어 매핑
| Layer | 경로 | 내용 |
|-------|------|------|
| L1 | `fermion_wiki/raw/` (junction 링크) | papers/, backtest_logs/, handover_archives/, specs_archive/ |
| L3 | `fermion_wiki/wiki/` | 8개 섹션 (ideas, hypotheses, indicators 등) |
| Config | `fermion_wiki/schema/` | ingest.md, query.md, lint.md, templates/ |

*Mode A이므로 L2 session_archive 없음.*

### L3 섹션 구성 (8개)
| 섹션 | HDIL Phase 매핑 | 내용 |
|------|----------------|------|
| `ideas/` | P1 Ideation | 아이디어 원장 |
| `hypotheses/` | P3 Hypothesis | 검증 가능한 가설 |
| `indicators/` | P2 Research | 지표 엔티티 (재사용) |
| `strategies/` | P4 Design | 전략 엔티티 (재사용) |
| `concepts/` | 수시 | 개념 정의 (학술) |
| `postmortems/` | P5/P6 | 실험 사후 분석 |
| `diagnostics/` | P7 Diagnostic | 진단 결과 |
| `principles/` | P10 Consolidation | 일반화 원리 |

### Frontmatter 스타일 (YAML 없음 — wikilink + Taxonomy 주석 중심)
```markdown
<!-- Taxonomy: T2 Specification + T6 Regime -->
<!-- Status: Concluded -->
```

### Auditor 통합
- **Results/Reality Auditor (Opus급)** — Postmortem 검증 필수
- 대량 Ingest (10건+) 시 확증편향 탐지 + 대안 설명 요구
- Auditor 판정 슬롯이 postmortem 템플릿에 내장

### 도메인 특화 포인트 (범용화 시 config으로 분리된 것들)
- HDIL 10-Phase → `sections[].phase_tag` config 필드로 일반화
- `Results/Reality Auditor` → `auditors[]` config 필드로 일반화
- `quant-doctrine.md` (원리 승격 최종 관문) → 프로젝트 로컬 파일
- Taxonomy T1-T6/S1-S3 → postmortem.md 템플릿의 주석 블록으로 포함

---

## "내 프로젝트는 어떤 모드?" 결정 가이드

```
질문 1: 지식의 주 원천은 무엇인가?
  ├── 에이전트-인간 대화 세션이 대부분 → Mode B (Session-Extract)
  ├── 논문·외부 자료·실험 로그가 대부분 → Mode A (Karpathy Pure)
  └── 둘 다 비슷하게 중요 → Hybrid

질문 2: 지식 단위는 무엇인가?
  ├── 결정(Decision) / 아키텍처 설명이 중심 → decisions/architecture 섹션 중심 (리얼군 패턴)
  ├── 재사용 엔티티 (지표·전략·개념)가 중심 → entity 섹션 중심 (코드군 패턴)
  └── 원리·교훈 축적이 목적 → principles/postmortems 섹션 중심

질문 3: 위크플로우 사이클이 있는가?
  ├── 없음 → 기본 섹션 (decisions, concepts, principles)으로 시작
  └── 있음 (예: HDIL, TEMS 사이클 등) → sections[].phase_tag로 사이클 매핑

추천 시작점:
  새 에이전트 → Mode B + sections: [decisions, concepts, principles]
  연구 에이전트 → Mode A + sections: [ideas, concepts, postmortems, principles]
  혼합 에이전트 → Hybrid + 커스텀 섹션
```

---

## 공통 패턴 vs 도메인 특화 항목

| 항목 | 리얼군 특화 | 코드군 특화 | 범용 스킬 자산 |
|------|-----------|-----------|--------------|
| L3 섹션 이름 | decisions, architecture, pipeline, reference | ideas, hypotheses, indicators, strategies, concepts, postmortems, diagnostics, principles | config의 `sections[]` |
| Frontmatter 스타일 | YAML 필수 (Dataview) | YAML 없음 (주석 기반) | 양쪽 템플릿 제공 |
| 파일명 | `YYYY-MM-DD_<kebab>.md` | `YYYYMMDD_<name>.md` or `<name>.md` | page-templates 주석에 양쪽 명시 |
| Auditor | 없음 | Results/Reality Auditor (Opus) | `auditors[]` config 필드 |
| 사이클 매핑 | 없음 | HDIL 10-Phase | `sections[].phase_tag` |
| 세션 추출 | extract_session_raw.py | 없음 (Mode A) | scripts/ 범용화 제공 |
