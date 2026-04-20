<!--
  템플릿: Daily Note (Obsidian Calendar + Dataview 연동 전용)

  복사 위치: <daily_notes_folder>/YYYY-MM-DD.md
  파일명은 반드시 Daily Notes 플러그인 format 과 일치해야 한다 (기본 YYYY-MM-DD).
  Calendar plugin(liamcain) 은 오직 **파일명** 으로 dot/dot-count 를 그린다.

  이 템플릿의 역할:
    - Calendar 에서 날짜를 클릭했을 때 열리는 진입점
    - Dataview 쿼리로 같은 date 를 가진 wiki 페이지들을 역참조 (`WHERE date = this.file.day`)
    - 에이전트 session log 요약을 append 하는 append-only journal

  이 파일 자체(템플릿)는 수정 금지.
-->
---
date: YYYY-MM-DD
status: Active
aliases: []
tags: [daily-note]
cssclass: twk-daily
---

# {{date:YYYY-MM-DD}} — Daily Note

<!--
  Obsidian Daily Notes plugin 의 {{date}} 변수가 파일 생성 시 치환.
  직접 복사해서 사용할 때는 YYYY-MM-DD 자리에 날짜를 수동 입력.
-->

## 오늘의 wiki 페이지 (Dataview)

```dataview
TABLE WITHOUT ID
  file.link AS Page,
  status AS Status,
  file.folder AS Section,
  tags AS Tags
FROM "docs/wiki"
WHERE date = this.file.day
  AND file.name != "index"
  AND file.name != "log"
SORT file.folder ASC, file.name ASC
```

<!--
  동작 원리:
    this.file.day  = 이 daily-note 파일명에서 추출된 날짜 (filename YYYY-MM-DD 규칙)
    date           = 각 wiki 페이지 frontmatter 의 date 필드 (Date 타입, 인용 금지)
    두 값이 일치하는 모든 wiki 페이지를 자동 집계.
-->

## 세션 로그

<!-- 에이전트 session-lifecycle 종료 훅에서 해당 날짜 recap 을 append. -->

## 메모

<!-- 자유 메모. -->
