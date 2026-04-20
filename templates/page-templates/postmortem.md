<!--
  템플릿: 실험·결과 사후 분석 (코드군 패턴)
  복사 위치: wiki/postmortems/YYYYMMDD_<name>.md
  확정판: YYYYMMDD_<name>.md / 최종판: YYYYMMDD_<name>_final.md
  이 파일 자체는 수정 금지.

  Frontmatter 규약 (Dataview + Calendar 호환):
    - date: YYYY-MM-DD  (인용 금지 — 사후분석 작성일)
    - taxonomy: T1~T6 / S1~S3 복합 가능
-->
---
date: YYYY-MM-DD
status: Tentative
aliases: []
tags: [postmortem]
taxonomy: []
phase: "P5"
scope: ""
auditor: ""
auditor_verdict: ""
cssclass: twk-postmortem
---
<!--
  status 옵션: Tentative | Confirmed | Disputed
  taxonomy 코드:
    실패: T1 Theory / T2 Specification / T3 Implementation / T4 Parameter / T5 Data / T6 Regime
    성공: S1 Robust / S2 Regime-Lucky / S3 Parameter-Lucky
  복합 가능: [T2, T6] 처럼 배열
  auditor_verdict: PASS | FAIL | NEEDS_REVISION
-->

# Postmortem — [실험/결과 제목]

## 원본 링크

<!-- L1/L2 원본 경로 또는 wikilink -->
<!-- Mode B: [[../../session_archive/YYYYMMDD_sN_raw]] -->
<!-- Mode A: [[../../raw/backtest_logs/YYYYMMDD_<name>]] -->
<!-- 관련 아이디어·가설 페이지 -->
<!-- [[../ideas/YYYYMMDD_<idea_name>]] [[../hypotheses/YYYYMMDD_<hyp_name>]] -->

## 결과가 실제 보여준 것

<!-- 아이디어·가설이 현실에서 어떻게 행동했는가.
     수치·패턴·조건별 분해 등 구체적으로. 해석 없이 사실만. -->

## 초기 해석 vs 최종 해석

| | 내용 |
|---|---|
| **초기 해석** | <!-- 결과 직후 1차 해석 --> |
| **최종 해석** | <!-- 추가 분석 후 수정된 해석 --> |
| **해석 괴리 원인** | <!-- 있다면 기술 --> |

## 축적 교훈

<!-- 재사용 가능한 교훈. 유사 상황에 일반화 가능한 내용.
     구체적이고 falsifiable하게 기술. -->

- <!-- 교훈 1 -->
- <!-- 교훈 2 -->

## 원리 승격 후보

<!-- Y / N + 이유. Y이면 wiki/principles/ 페이지 생성 계획 또는 링크 -->

## Auditor 판정

<!-- frontmatter auditor + auditor_verdict 사용. 본문에는 상세 서술. -->
<!-- 확증편향 탐지 결과 + 대안 설명 -->
