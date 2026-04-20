# 3 Operations — Ingest · Query · Lint 상세

## Ingest Operation

### 정의
새 source (논문, 실험 결과, 세션 아카이브, 외부 자료)를 wiki에 흡수하는 작업.
원본(L1/L2)을 보존하면서 관련 wiki 페이지 여러 곳을 업데이트한다.

### 트리거 조건
- 새 학술 자료·논문 도입
- 실험/백테스트 결과 확정
- 세션 종료 시 새 결정·아키텍처 발견 (Mode B)
- 핸드오버 아카이브 소급 처리

### 주체
- **기본**: Sonnet 서브에이전트 위임
- **대량 Ingest (10건+) 또는 원리 승격 필요 시**: Opus Advisor 검증 경유 권장

서브에이전트 위임 템플릿:
```
Task: [Wiki Ingest] <source 1줄 요약>
Context:
  - wiki_root: <경로>
  - source: <L1 또는 L2 경로>
  - related_sections: <예상 관련 섹션 목록>
Rules:
  - RAG 기반 검색 금지 — Compilation 원칙
  - 단일 중앙 페이지 업데이트 금지 — 교차 참조 우선
  - 페이지 삭제 금지 — 구버전은 [SUPERSEDED] 처리
Output:
  - 업데이트된 페이지 경로 목록
  - log.md append 결과
  - index.md 갱신 여부
```

### 절차 (7단계)
1. **원문 요약** — source 핵심 내용 추출 (논문이면 abstract + method + finding 3단 요약)
2. **L1 연결** — 원본 파일 경로 또는 URL을 `raw/` 또는 L2 archive 경로로 기록
3. **wiki/ 교차 업데이트** — 관련 섹션 여러 페이지에 내용 추가 (중앙화 금지)
4. **신규 페이지 생성** (필요 시) — `templates/page-templates/`에서 해당 템플릿 복사
5. **wikilink 건전성 점검** — 신규 링크가 실제 파일을 가리키는지 양방향 확인
6. **log.md append** — `## YYYY-MM-DD — [Ingest] <요약> | <업데이트 페이지 목록>`
7. **index.md 등록** — 새 페이지 생성 시 해당 섹션에 `[[page_name]] — 1줄 설명` 추가

### 체크리스트
- [ ] 새 페이지 → index.md 등록
- [ ] 기존 관련 페이지에 역링크(backlink) 추가
- [ ] log.md 1행 기록
- [ ] 파일명 규칙 준수 (wiki.config.json 또는 섹션별 컨벤션)

---

## Query Operation

### 정의
기존 wiki/ 페이지들을 탐색·합성해 답변을 생성하는 작업.
쿼리 시점에 검색 없이 Compilation된 wiki를 읽는다 (Karpathy 핵심 원칙).

### 트리거 조건
- 선행 지식 조회 (관련 실험·결정 유무 확인)
- 설계 분기 전 사전 조사 ("이런 접근 전에 비슷한 게 있었나?")
- 원리·개념 정의 확인

### 주체 분기
| 복잡도 | 주체 |
|--------|------|
| 단순 조회 (페이지 1~2개) | 에이전트 직접 수행 |
| 교차 합성 (페이지 3개+) | Sonnet 서브에이전트 위임 |
| 원리 승격 판단 필요 | Opus Advisor 호출 |
| 직접 탐색 | 인간이 Obsidian에서 `Ctrl+Shift+F` |

### 절차
1. **관련 wiki 페이지 탐색** — 키워드로 섹션 디렉토리 탐색 또는 wikilink 그래프 네비게이션
2. **교차 참조로 답변 합성** — 단일 페이지 답변 금지; 여러 페이지 내용 결합
3. **새 synthesis 페이지 작성** (필요 시) — 여러 개념 결합으로 새 통찰 발생 시 `concepts/` 또는 `principles/`에 신규 페이지
4. **log.md 기록** — `## YYYY-MM-DD — [Query] <질문 요약> | <참조 페이지 목록>`

### 주의사항
- Query는 wiki를 **읽기 전용**으로 소비. 내용 수정이 필요하면 Ingest로 전환.
- 합성 결과가 기존 페이지와 모순 발견 시 → Lint 트리거 고려.
- RAG 기반 검색(벡터 유사도) 금지 — wiki 디렉토리 직접 탐색 우선.

---

## Lint Operation

### 정의
wiki 건전성 정기 점검. 4종 이슈 탐지 (모순 / Stale / 고아 / 공백).

### 트리거 주기
- **세션 기반**: config의 `lint_cadence.every_sessions` (기본 5 세션마다)
- **페이지 기반**: config의 `lint_cadence.every_pages` (기본 10 페이지 추가 시)
- **수동**: `python ~/.claude/skills/TWK/scripts/lint.py --config wiki.config.json`
- **자동 (선택)**: session-lifecycle dayclose 시 조건 확인

### 주체
Sonnet 서브에이전트 위임 (자동 실행). 이슈 수정은 인간 승인 후 진행.

### 점검 4항목

| # | 항목 | 탐지 기준 | 조치 |
|---|------|----------|------|
| 1 | **모순 탐지** | 동일 개념·엔티티에 대해 서로 다른 결론이 다른 페이지에 존재 | 최신 교훈 기준으로 구버전에 `[SUPERSEDED by [[new_page]]]` 추가 |
| 2 | **Stale 정보** | ≥30일 미갱신 페이지 중 이후 실험 교훈과 상충하는 내용 존재 | 업데이트 또는 `[STALE — 검토 필요: YYYY-MM-DD]` 플래그 |
| 3 | **고아 페이지** | 어떤 페이지에서도 backlink 없는 md 파일 (index.md 등록만으로 불충분) | index.md 확인 + 관련 페이지에 wikilink 추가 |
| 4 | **교차 참조 공백** | 엔티티 페이지는 있으나 관련 실험·결과·원리 wikilink 0건 | 미연결 상태 명시 + 향후 인제스트 후보 등록 |

### 산출물
```markdown
## YYYY-MM-DD — [Lint] 모순 N건 / Stale N건 / 고아 N건 / 공백 N건

### 수정 완료
- [page_name]: [내용]

### 수정 보류 (인간 승인 필요)
- [page_name]: [이슈 설명]
```

`log.md`에 append. 수정 완료 건과 보류 건 분리 기록.

### scripts/lint.py 기능
- Orphan pages: `index.md`에 등록되지 않은 md 파일 탐지
- Dangling wikilinks: `[[X]]` 패턴이지만 실제 파일 없는 링크
- Stale pages: frontmatter `date` 기준 N일 초과 + `status: Active`
- Missing frontmatter: config에서 required로 정의된 필드 누락
- 상세: [`scripts/lint.py`](../scripts/lint.py) `--help`
