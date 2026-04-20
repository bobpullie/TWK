# session-lifecycle Wiki 통합 스니펫

> 이 파일을 프로젝트의 `session-lifecycle.md` 세션 종료(Shutdown) 섹션에 복사 삽입.
> Mode A / Mode B 중 해당 모드의 스니펫만 사용. [N]은 기존 Step 번호에 맞게 조정.

---

## Mode B (Session-Extract) 스니펫

### Step [N]: Session Archive (L2 생성)

```bash
python ~/.claude/skills/TWK/scripts/extract_session_raw.py \
  --config ./wiki.config.json
```

- 출력: `{session_archive_root}/YYYYMMDD_session{N}_raw.md`
- 내용: 이번 세션의 user/assistant Q&A 전부 (tool_use, thinking 제외)
- 토큰 비용: 0 (기계적 추출)
- 이미 추출된 세션은 자동 skip (`already_extracted()` 헤더 검사)

### Step [N+1]: Wiki Curation (L3 갱신)

이번 세션에 새로운 **결정 / 아키텍처 이해 / 원리**가 있었나?

**YES** → 해당 섹션 `wiki/` 업데이트:
1. 해당 섹션 템플릿 복사: `~/.claude/skills/TWK/templates/page-templates/<type>.md`
2. 내용 채우기 (원본 대화 붙여넣기 금지 — 압축·요약만)
3. `[[../../session_archive/YYYYMMDD_sN_raw]]`로 L2 원본 wikilink
4. `index.md` 해당 섹션에 `[[page_name]] — 1줄 설명` 추가
5. `log.md`에 1행 append: `## YYYY-MM-DD — [Ingest] <요약> | <페이지 경로>`

**NO** → skip (억지로 쓰지 말 것 — Karpathy 원칙)

---

## Mode A (Karpathy Pure) 스니펫

### Step [N]: Wiki Ingest (외부 자료 / 결과 처리)

이번 세션에 새로운 **자료 / 실험 결과 / 핸드오버**가 도입됐나?

**YES** → Ingest 실행:
```
Task: [Wiki Ingest] <source 1줄 요약>
Source: <L1 raw/ 경로>
관련 섹션: <예상 섹션 목록>
```
→ Sonnet 서브에이전트에 위임 (직접 수행 가능하나 위임 권장)

**NO** → skip

### Step [N+1]: Wiki Curation (L3 원리·개념 갱신)

새 원리·개념이 도출됐나?

**YES** → `wiki/concepts/` 또는 `wiki/principles/` 페이지 생성·갱신
→ 인간 디렉터 방향 확인 후 작성 (원리 승격은 승인 필수)

**NO** → skip

---

## 공통: Lint 주기 확인

```
세션 카운터 += 1
IF 세션 카운터 % lint_cadence.every_sessions == 0:
    → python ~/.claude/skills/TWK/scripts/lint.py --config ./wiki.config.json
    → 보고서 log.md append, 수정 이슈 검토
```

---

## 빠른 참조

| 파일 | 경로 |
|------|------|
| extract_session_raw.py | `~/.claude/skills/TWK/scripts/extract_session_raw.py` |
| lint.py | `~/.claude/skills/TWK/scripts/lint.py` |
| 페이지 템플릿 | `~/.claude/skills/TWK/templates/page-templates/` |
| 전체 스킬 | `~/.claude/skills/TWK/SKILL.md` |
