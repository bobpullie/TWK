# Schema — Lint Operation

## 정의

wiki 건전성 정기 점검. 4종 이슈 탐지 및 보고.

## 호출 주기

config의 `lint_cadence` 기준:
- `every_sessions`: N 세션마다 (기본 5)
- `every_pages`: N 페이지 추가 시 (기본 10)
- 수동: `python ~/.claude/skills/TWK/scripts/lint.py --config wiki.config.json`

## 호출 주체

Sonnet 서브에이전트 (자동 실행 권장).
이슈 수정 실행은 에이전트 수행 가능하나, 원리 페이지 변경은 인간 승인 필요.

## 점검 4항목

| # | 항목 | 탐지 기준 | 조치 |
|---|------|----------|------|
| 1 | **모순 탐지** | 동일 개념·엔티티에 상충 기술이 다른 페이지에 공존 | 최신 근거 기준 구버전에 `[SUPERSEDED by [[new_page]]]` + 후속 페이지 링크 |
| 2 | **Stale 정보** | frontmatter `date` 기준 ≥30일 미갱신 + `status: Active` + 이후 결과와 상충 | 업데이트 또는 `[STALE — 검토 필요: YYYY-MM-DD]` 플래그 추가 |
| 3 | **고아 페이지** | 어떤 페이지에서도 wikilink 역참조 없음 (index.md 등록만으로 불충분) | index.md 확인 + 관련 페이지에 `[[page]]` 역링크 추가 |
| 4 | **교차 참조 공백** | 엔티티/결정 페이지는 있으나 관련 페이지와 wikilink 연결 0건 | 미연결 상태 명시 + 향후 Ingest 후보로 log.md 기록 |

## 산출물 형식 (log.md append)

```markdown
## YYYY-MM-DD — [Lint] 모순 N건 / Stale N건 / 고아 N건 / 공백 N건

### 수정 완료
- `page_name.md`: [이슈 내용] → [조치 내용]

### 수정 보류 (인간 승인 필요)
- `page_name.md`: [이슈 설명] — 이유: [왜 자동 수정 보류인지]

### 이번 Lint 요약
- 총 점검 페이지: N
- 수정 완료: N건
- 보류: N건
- 다음 Lint 예정: Session N+5 또는 페이지 N+10 추가 시
```

## scripts/lint.py 실행

```bash
# 전체 점검
python ~/.claude/skills/TWK/scripts/lint.py --config wiki.config.json

# 특정 항목만
python ~/.claude/skills/TWK/scripts/lint.py --config wiki.config.json --check orphan
python ~/.claude/skills/TWK/scripts/lint.py --config wiki.config.json --check stale --stale-days 30

# Dry-run (수정 없이 보고만)
python ~/.claude/skills/TWK/scripts/lint.py --config wiki.config.json --dry-run
```
