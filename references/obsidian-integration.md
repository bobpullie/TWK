# Obsidian 통합 가이드 (Dataview + Calendar + Wikilink)

## 기본 설정

Obsidian vault를 wiki_root (또는 프로젝트 루트)로 설정.
Vault settings에서 "Files & Links" → "Use [[Wikilinks]]" 활성화 필수.

```
wiki.config.json:
  "obsidian": {
    "vault_path": ".",
    "dataview_enabled": true,
    "daily_notes": {
      "enabled": true,
      "folder": "docs/daily",
      "format": "YYYY-MM-DD",
      "template_path": "docs/templates/daily-note.md"
    }
  }
```

필요 커뮤니티 플러그인:
- **Dataview** (blacksmithgu) — YAML frontmatter 기반 동적 쿼리
- **Calendar** (liamcain) — 월 캘린더 UI + Daily Notes 탐색

코어 플러그인:
- **Daily Notes** — Calendar 가 `format`/`folder` 값을 참조

---

## 프론트매터 규약 (Dataview + Calendar 양립)

TWK 는 모든 L3 wiki 페이지에 통일 frontmatter 를 부여한다.

```yaml
---
date: 2026-04-20          # 인용 금지 — Dataview Date 타입으로 자동 coerce.
status: Active            # Draft | Active | Accepted | Implemented | Superseded | Archived
aliases: []               # Obsidian 별칭 검색
tags: [decision, tems]    # 복수형 필수. 단수 `tag:` 는 인덱싱 안 됨.
phase: Phase-0-3
scope: wesang-all-agents
cssclass: twk-decision    # .obsidian/snippets/*.css 로 타입별 스타일 지정
---
```

**핵심 규칙 (lint.py 가 검증):**

| 규칙 | 이유 |
|------|------|
| `date:` 무인용 ISO `YYYY-MM-DD` | Dataview 가 Date 객체로 자동 변환 → `WHERE date > date(today)` 가능. 따옴표 들어가면 Text 타입이 되어 비교 깨짐. |
| Calendar default format 과 동일 (`YYYY-MM-DD`) | Calendar plugin 은 Daily Notes 의 format 만 읽음. daily note 파일명과 모든 wiki 페이지 frontmatter date 가 같은 포맷이어야 Dataview 교차 쿼리가 깔끔. |
| `tags:` 복수형 | Obsidian 태그 패널 + Dataview `file.tags` 모두 복수형만 인덱싱. 단수 `tag:` 는 무시됨. |
| 리스트는 flow (`[a, b]`) 또는 block (`- a\n- b`) 모두 허용 | Dataview 양쪽 다 파싱. |
| `cssclass` 선택 | Obsidian 편집/프리뷰 뷰에 CSS 적용. Calendar 의 note dot 색상 구분에도 활용 가능. |

---

## Calendar + Daily Note 연동 패턴 (핵심)

Calendar plugin 자체는 frontmatter `date` 를 읽지 않는다. **오직 파일명만** 본다. 그래서
우리는 "daily note 가 허브, wiki 페이지는 spoke" 패턴을 쓴다:

```
Calendar UI (월 뷰)
  └── 클릭 → docs/daily/2026-04-20.md (Daily Note, 파일명 = 날짜)
        └── Dataview 쿼리: WHERE date = this.file.day
              └── decisions/2026-04-20_xxx.md
              └── concepts/YYY.md  (date: 2026-04-20)
              └── postmortems/20260420_zzz.md
```

**Daily note 템플릿** (`docs/templates/daily-note.md`, TWK 글로벌 스킬 `templates/page-templates/daily-note.md` 복사):

```yaml
---
date: 2026-04-20
status: Active
aliases: []
tags: [daily-note]
cssclass: twk-daily
---

# 2026-04-20 — Daily Note

## 오늘의 wiki 페이지

```dataview
TABLE WITHOUT ID
  file.link AS Page,
  status AS Status,
  file.folder AS Section
FROM "docs/wiki"
WHERE date = this.file.day
SORT file.folder ASC
```

`this.file.day` 는 daily note 파일명(`YYYY-MM-DD.md`) 에서 Dataview 가 자동 추출.

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
| **Daily note** | `YYYY-MM-DD.md` | `2026-04-20.md` — Calendar 연동 전용 |

### Wikilink 건전성 원칙
- 새 페이지 생성 시 관련 기존 페이지에 역링크 추가 (양방향)
- `[[X]]` 작성 전 파일 존재 여부 확인 (lint.py 가 dangling link 탐지)
- 페이지 이름 변경 시 Obsidian "Rename" 기능 사용 (자동 링크 업데이트)

---

## Backlink 자동화

Obsidian 의 backlink 패널 (우측 사이드바) 에서 자동 표시.
"Backlinks in document" 옵션 활성화 시 페이지 하단에 자동 표시.

**활용 패턴:**
- Lint 의 "고아 페이지" 탐지를 Obsidian backlink 패널로 시각 확인
- `index.md` 에 없어도 backlink 있으면 연결된 페이지로 간주

---

## Graph View 활용

Obsidian Graph View (Ctrl+G) 로 wiki 구조 시각화.

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

## Dataview 쿼리 — 주요 패턴

### index.md 용: 전체 결정 테이블
```dataview
TABLE date, status, phase, scope
FROM "docs/wiki/decisions"
SORT date DESC
```

### Active 페이지 최근순
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

### 특정 날짜의 모든 페이지 (Calendar 연동 핵심)
```dataview
TABLE file.folder AS Section, status
FROM "docs/wiki"
WHERE date = date("2026-04-20")
```

### 태그 기반 크로스 섹션
```dataview
LIST
FROM #tems AND "docs/wiki"
SORT file.path
```

---

## cssclass 로 Calendar/노트 스타일 차별화

각 TWK 템플릿은 고유 `cssclass` 를 부여한다:

| 템플릿 | cssclass | 권장 색상 |
|--------|----------|----------|
| decision | `twk-decision` | blue |
| concept | `twk-concept` | green |
| principle | `twk-principle` | purple |
| postmortem | `twk-postmortem` | red |
| idea | `twk-idea` | yellow |
| entity | `twk-entity` | teal |
| daily-note | `twk-daily` | gray |

`.obsidian/snippets/twk.css` 예시:

```css
.twk-decision h1::before   { content: "🏛 "; }
.twk-concept h1::before    { content: "🧠 "; }
.twk-principle h1::before  { content: "📜 "; }
.twk-postmortem h1::before { content: "🔬 "; }
.twk-daily h1::before      { content: "📅 "; }
```

Calendar plugin 은 dot 에 frontmatter 값을 직접 매핑하지 않지만, Daily Note 진입 시
cssclass 가 적용되어 시각 구분 가능.

---

## QMD 연동

QMD (로컬 BM25/dense 검색) 와 Obsidian wiki 연동:

```bash
# wiki/ 디렉토리 QMD 컬렉션으로 인덱싱
qmd index --collection wiki --path docs/wiki/

# wiki 내 검색
qmd search --collection wiki "관련 키워드"
```

**QMD + wiki 분업:**
- QMD → L1 (JSONL) / L2 (session_archive) 전체 검색
- Obsidian 직접 탐색 → L3 (wiki) 구조적 탐색
- 두 경로 모두 제공; 에이전트는 wiki 를 우선, QMD 는 보강

---

## Obsidian Web Clipper 연동 (Mode A)

외부 웹 자료를 L1 raw/ 로 캡처:
1. Obsidian Web Clipper 브라우저 익스텐션 설치
2. 클립 대상 vault + 폴더를 `raw/web-clips/` 로 설정
3. 클립 후 Ingest Operation 실행 (`/wiki ingest raw/web-clips/<file>`)

---

## 진입점 북마크 권장

Obsidian 좌측 사이드바에 즐겨찾기 추가:
- `docs/wiki/index.md` — L3 Wiki 진입점
- `docs/wiki/log.md` — 최근 변경 타임라인
- `docs/daily/YYYY-MM-DD.md` — 오늘의 Daily Note (Calendar 와 동기)
- `docs/session_archive/` — L2 Archive 폴더 (Mode B)
