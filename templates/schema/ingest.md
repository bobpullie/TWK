# Schema — Ingest Operation

## 정의

새 source (논문, 실험 결과, 외부 자료, 세션 아카이브)를 wiki에 흡수하는 작업.
L1/L2 원본을 보존하면서 관련 wiki 페이지 여러 곳을 업데이트한다.

## 호출 시점

| 트리거 | 비고 |
|--------|------|
| 새 학술 자료·논문 도입 | Mode A L1 raw/ 경유 |
| 실험·결과 확정 | 결과 postmortem 작성 시 |
| 외부 자료 수동 도입 | 수시 (에이전트 판단) |
| 세션 종료 시 새 결정 발견 | Mode B — session-lifecycle 연계 |
| 아카이브 소급 처리 | --backfill 또는 수동 배치 |

## 호출 주체

Sonnet Executor 서브에이전트 (위임 기본).
대량 Ingest (10건+) 또는 원리 승격 판단 필요 시: Opus Advisor 경유.

## 절차

1. **원문 요약** → source 핵심 내용 추출
2. **L1/L2 경로 기록** → 원본 참조 링크 (raw/ 파일 또는 session_archive 경로)
3. **관련 wiki/ 페이지 교차 업데이트** (여러 섹션 페이지에 분산)
4. **신규 페이지 필요 시** → `templates/page-templates/`에서 해당 템플릿 복사 → 내용 채움
5. **wikilink 갱신** → 신규 링크 양방향 점검, 역링크 추가
6. **`log.md` append** → `## YYYY-MM-DD — [Ingest] <요약> | <업데이트 페이지>`
7. **`index.md` 등록** → 신규 페이지 → 해당 섹션에 `[[page]] — 1줄 설명` 추가

## 체크리스트

- [ ] 새 페이지 → index.md 해당 섹션에 등록
- [ ] 참조된 기존 페이지에 역링크 추가
- [ ] log.md 1행 기록
- [ ] 파일명 규칙 준수 (wiki.config.json `naming_conventions` 참조)
- [ ] 페이지 삭제 없음 — 구버전은 `[SUPERSEDED by [[new_page]]]` 처리

## 금지 사항

- RAG 기반 검색으로 관련 페이지 탐색 — 디렉토리 직접 탐색 우선
- 단일 중앙 페이지에만 업데이트 — 교차 참조 분산 필수
- 원본(L1/L2) 파일 수정 — Immutable 유지
