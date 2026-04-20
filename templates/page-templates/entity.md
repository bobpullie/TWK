<!--
  템플릿: 재사용 엔티티 (지표·전략·컴포넌트 등 도메인 특화 엔티티)
  복사 위치: wiki/<section>/<name>.md
  파일명: 엔티티명 그대로 (예: wiki/indicators/VIX.md, wiki/strategies/COMPASS_v3.md)
  이 파일 자체는 수정 금지.

  Frontmatter 규약 (Dataview + Calendar 호환):
    - date: YYYY-MM-DD  (인용 금지 — 마지막 갱신일)
    - entity_type: Indicator | Strategy | Component | Module | System | Pattern
-->
---
date: YYYY-MM-DD
status: Active
aliases: []
tags: [entity]
id: ""
entity_type: ""
scope: ""
cssclass: twk-entity
---
<!--
  status: Active | Stub | Deprecated | Frozen
  id 형식: <TYPE>-<NAME>. 예: IND-VIX, STRAT-COMPASS_v3
-->

# [엔티티 유형] — [엔티티 이름]

## 정의

<!-- 엔티티의 명확한 정의.
     수식·알고리즘 포함 시 코드블록 또는 LaTeX. -->

## 데이터 소스 / 의존성

<!-- 이 엔티티가 의존하는 외부 데이터, 라이브러리, 서비스. -->
<!-- 예: FRED BAMLH0A0HYM2, CBOE ^VIX, internal module: src/core/xxx.py -->

## 관련 실험·결과

<!-- 이 엔티티가 사용된 결정·postmortem·실험 wikilink 목록 -->
<!-- [[../decisions/YYYY-MM-DD_xxx]] -->
<!-- [[../postmortems/YYYYMMDD_xxx]] -->

## 주의점

<!-- 알려진 한계, 오용 패턴, 전제 조건. -->

## 관련 엔티티

<!-- [[related_entity_1]] [[related_entity_2]] -->
