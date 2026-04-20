<!--
  템플릿: 실험·결과 사후 분석 (코드군 패턴)
  복사 위치: wiki/postmortems/YYYYMMDD_<name>.md
  확정판: YYYYMMDD_<name>.md / 최종판: YYYYMMDD_<name>_final.md
  이 파일 자체는 수정 금지.
-->

# Postmortem — [실험/결과 제목]

## 원본 링크

<!-- L1/L2 원본 경로 또는 wikilink -->
<!-- Mode B: [[../../session_archive/YYYYMMDD_sN_raw]] -->
<!-- Mode A: [[../../raw/backtest_logs/YYYYMMDD_<name>]] -->
<!-- 관련 아이디어·가설 페이지 -->
<!-- [[../ideas/YYYYMMDD_<idea_name>]] [[../hypotheses/YYYYMMDD_<hyp_name>]] -->

## Taxonomy 태그

<!--
실패 분류:
  T1 Theory      — 이론 자체가 틀림
  T2 Specification — 이론은 맞으나 구체화 오류
  T3 Implementation — 구현 버그
  T4 Parameter   — 파라미터 과적합
  T5 Data        — 데이터 오류 (생존편향, lookahead 등)
  T6 Regime      — 레짐 의존성 미반영

성공 분류:
  S1 Robust       — 다양한 조건에서 검증된 강건한 성공
  S2 Regime-Lucky — 특정 레짐에서만 작동
  S3 Parameter-Lucky — 파라미터 민감도 높음

복합 가능: 예: T2 + T6
-->
**분류:** <!-- 예: T2 Specification + T6 Regime -->
**상태:** <!-- Tentative | Confirmed | Disputed -->

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

<!-- config에 auditor가 정의된 경우 해당 섹션 사용.
     PASS / FAIL / NEEDS REVISION + 확증편향 탐지 결과 + 대안 설명 -->

_판정일: YYYY-MM-DD_
_판정자: <!-- Auditor 이름 또는 N/A -->_
