# Obsidian 통합 가이드

## 기본 설정

Obsidian vault를 wiki_root (또는 프로젝트 루트)로 설정.
Vault settings에서 "Files & Links" → "Use [[Wikilinks]]" 활성화 필수.

```
wiki.config.json:
  "obsidian": {
    "vault_path": ".",      // Obsidian vault 루트 (project_root 기준)
    "dataview_enabled": true
  }
```

---

## Wikilink 규약

### 기본 형식
```
[[page_name]]                     // 같은 섹션 내 페이지
[[section/page_name]]             // 섹션 지정
[[page_name|표시 텍스트]]          // 표시 텍스트 별도 지정
[[../session_archive/YYYYMMDD_sN_raw]]  // L2 drill-down (Mode B)
```

### 파일명 규칙
| 파일 유형 | 규칙 | 예시 |
|----------|------|------|
| 세션 기반 (날짜 포함) | `YYYYMMDD_<name>.md` | `20260420_compass_v4_p0.md` |
| 엔티티 (재사용) | `<name>.md` | `HY.md`, `VIX.md` |
| 결정 (ADR 스타일) | `YYYY-MM-DD_<kebab>.md` | `2026-04-20_atlas-optimization.md` |
| 버전 관리 | `YYYYMMDD_<name>_v<n>.md` | `20260420_strategy_v2.md` |

### Wikilink 건전성 원칙
- 새 페이지 생성 시 관련 기존 페이지에 역링크 추가 (양방향)
- `[[X]]` 작성 전 파일 존재 여부 확인 (lint.py가 dangling link 탐지)
- 페이지 이름 변경 시 Obsidian "Rename" 기능 사용 (자동 링크 업데이트)

---

## Backlink 자동화

Obsidian의 backlink 패널 (우측 사이드바)에서 자동 표시.
"Backlinks in document" 옵션 활성화 시 페이지 하단에 자동 표시.

**활용 패턴:**
- Lint의 "고아 페이지" 탐지를 Obsidian backlink 패널로 시각 확인
- `index.md`에 없어도 backlink 있으면 연결된 페이지로 간주

---

## Graph View 활용

Obsidian Graph View (Ctrl+G 또는 `그래프 뷰 열기`)로 wiki 구조 시각화.

**필터 설정 권장:**
```
노드 필터: -"docs/session_archive"  // L2 archive 제외 (노이즈)
태그 필터: session                  // 특정 태그 하이라이트
```

**패턴 독해:**
- 고밀도 노드 (연결 많음) → 핵심 개념/원리
- 고립 노드 → Lint 고아 페이지 후보
- 클러스터 → 도메인 섹션 경계

---

## Dataview 쿼리

Obsidian Dataview 플러그인 설치 후 YAML frontmatter 기반 동적 쿼리.

### 기본 예시 (index.md용)
```dataview
TABLE date, status, phase, scope
FROM "docs/wiki/decisions"
SORT date DESC
```

### 상태별 필터
```dataview
LIST
FROM "docs/wiki"
WHERE status = "Active"
SORT file.mtime DESC
```

### 섹션 통계
```dataview
TABLE length(rows) AS count
FROM "docs/wiki"
GROUP BY split(file.folder, "/")[2] AS section
```

### Stale 페이지 탐지
```dataview
TABLE date, status
FROM "docs/wiki"
WHERE status = "Active" AND date(date) < date(today) - dur(30 days)
```

**YAML frontmatter 예시 (decision.md 스타일):**
```yaml
---
date: 2026-04-20
status: Implemented
phase: 운영중
scope: 지식 관리
project: ALL
tags: [knowledge-system, wiki]
---
```

---

## QMD 연동

QMD (로컬 BM25/dense 검색)와 Obsidian wiki 연동:

```bash
# wiki/ 디렉토리 QMD 컬렉션으로 인덱싱
qmd index --collection wiki --path docs/wiki/

# wiki 내 검색
qmd search --collection wiki "관련 키워드"
```

**QMD + wiki 분업:**
- QMD → L1 (JSONL) / L2 (session_archive) 전체 검색
- Obsidian 직접 탐색 → L3 (wiki) 구조적 탐색
- 두 경로 모두 제공; 에이전트는 wiki를 우선, QMD는 보강

---

## Obsidian Web Clipper 연동 (Mode A)

외부 웹 자료를 L1 raw/로 캡처:
1. Obsidian Web Clipper 브라우저 익스텐션 설치
2. 클립 대상 vault + 폴더를 `raw/web-clips/`로 설정
3. 클립 후 Ingest Operation 실행 (`/wiki ingest raw/web-clips/<file>`)

---

## 진입점 북마크 권장

Obsidian 좌측 사이드바에 즐겨찾기 추가:
- `docs/wiki/index.md` — L3 Wiki 진입점
- `docs/wiki/log.md` — 최근 변경 타임라인
- `docs/session_archive/` — L2 Archive 폴더 (Mode B)
