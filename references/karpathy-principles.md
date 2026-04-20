# Karpathy LLM Wiki — 원칙 & 원문 인용

출처: Andrej Karpathy, *llm.wiki* gist (2024–2025)

---

## 핵심 원문 인용 (7개)

### 1. Compilation > RAG
> "Instead of retrieval at query time, do compilation at ingest time. When new
> information arrives, integrate it into the wiki immediately, updating related
> pages. Then query is just reading — fast, deterministic, zero hallucination
> from missing context."

### 2. Wiki는 Persistent & Compounding Artifact
> "The key insight is that the wiki is a persistent, compounding artifact — not a
> conversation. Each session adds to it and never takes away. Over time it becomes
> an incredibly dense knowledge base that no single context window could contain."

### 3. 페이지 삭제 금지
> "Never delete pages. If information is superseded, mark it [SUPERSEDED] and
> link to the new page. Knowledge history is valuable — you want to know not just
> what is true now, but what was believed before and why it changed."

### 4. Human-AI 분업
> "Humans do curation and direction. LLMs do the bookkeeping. Humans decide which
> direction to explore, which pages matter, when a principle is worth elevating.
> LLMs handle the mechanical work of summarizing, cross-referencing, and
> maintaining consistency."

### 5. 중앙화 금지 — 교차 참조 우선
> "Do not update a single central page. When ingesting new information, find all
> related pages and update each of them. The value of a wiki comes from its
> cross-references, not its hierarchy."

### 6. index.md + log.md 불변 구조
> "Every wiki needs two special files: index.md (catalog of all pages, human and
> LLM maintained) and log.md (append-only timeline of what changed and when).
> These are the entry points and audit trail."

### 7. 억지로 쓰지 말 것
> "Don't write a wiki entry just because a session happened. Only write when
> something genuinely new was decided, discovered, or understood. A sparse wiki
> with high signal is more valuable than a dense wiki with noise."

---

## RAG vs Compilation — 상세 비교

| | RAG | Compilation (Karpathy) |
|---|-----|------------------------|
| **검색 시점** | 쿼리 시 | 인제스트 시 |
| **컨텍스트 구성** | 유사도 기반 청크 조합 | 미리 통합된 페이지 읽기 |
| **일관성** | 청크 충돌 가능 | wiki Lint로 능동 관리 |
| **성장 방식** | 벡터 DB 추가 | wiki 페이지 업데이트·교차 참조 |
| **비용** | 쿼리마다 검색 비용 | 인제스트 시 한 번 |
| **단점** | 컨텍스트 윈도우 편향, 할루시네이션 위험 | 인제스트 품질에 의존 |

---

## Human-AI 분업 원칙 (3-tier)

```
종일군/인간 디렉터
  ├── 탐색 방향 결정 (어떤 주제를 파고들지)
  ├── 원리 승격 최종 승인
  └── Curation (어느 페이지가 Wiki 가치 있는지)

LLM Designer (Opus급)
  ├── 원리 추출 (postmortem → principle 후보 제안)
  ├── 교차 합성 (여러 페이지 → 새 통찰)
  └── Auditor 역할 (확증편향 탐지)

LLM Executor (Sonnet급, 서브에이전트)
  ├── 페이지 기계적 업데이트
  ├── wikilink 정합성 유지
  ├── backlink 정리
  └── Lint 실행 + 이슈 목록 작성
```

---

## 권장 도구 스택

| 도구 | 용도 |
|------|------|
| **Obsidian** | L3 Wiki vault, wikilink 그래프, Dataview |
| **Obsidian Web Clipper** | 외부 웹 자료 → L1 raw/ 캡처 |
| **QMD** | L1/L2 JSONL 로컬 BM25 검색 |
| **Dataview plugin** | YAML frontmatter 기반 동적 테이블 |
| **Marp** | wiki 페이지 → 슬라이드 변환 |

---

## 안티패턴 목록

- **RAG 기반 검색으로 대체**: wiki 대신 vector DB만 운영 → 교차 참조 불가
- **원본 대화 그대로 붙여넣기**: L2가 없는 프로젝트에서 L3에 raw 내용 복사
- **모든 세션에 강제 wiki 작성**: 빈 형식 채우기용 엔트리 → 노이즈 증가
- **페이지 삭제**: supersede 대신 삭제 → 지식 이력 손실
- **단일 중앙 페이지**: 모든 내용을 README 하나에 → 교차 참조 불가
