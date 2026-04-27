# TWK — TriadWiKi

**Claude Code Skill Plugin** — Karpathy LLM Wiki 방법론의 Triad Chord Studio 전용 구현체 (구 `llm-wiki`).

3-Layer (Raw / Wiki / Schema) + 3 Operations (Ingest / Query / Lint) + **Compilation > RAG** 원칙.

## Install

글로벌 Claude Code 스킬로 설치 (**clone 권장** — pull-based 업데이트 지원):

```bash
# Unix/macOS
git clone https://github.com/bobpullie/TWK.git "$HOME/.claude/skills/TWK"

# Windows (Git Bash)
git clone https://github.com/bobpullie/TWK.git "$USERPROFILE/.claude/skills/TWK"
```

설치 후 Claude Code에서 `Skill` 도구로 `TWK` 호출 가능.

## Updating

설치 디렉토리가 clone일 경우:

```bash
git -C "$HOME/.claude/skills/TWK" pull origin main
```

위상군 또는 다른 에이전트가 upstream repo에 push 하면, 모든 에이전트가 위 명령으로 기능 업데이트 수신 가능.

**검증:** `head -5 "$HOME/.claude/skills/TWK/SKILL.md"` 에 `upstream: https://github.com/bobpullie/TWK` 표시.

## Structure

```
TWK/
├── SKILL.md              # Skill 진입점 (name: TWK)
├── scripts/
│   ├── extract_session_raw.py   # L2 세션 raw 추출 (Mode B)
│   ├── init_wiki.py             # 프로젝트별 wiki.config.json + 섹션 생성
│   └── lint.py                  # orphan/dangling/stale/frontmatter 검사
├── templates/
│   ├── page-templates/          # decision/concept/principle/postmortem/entity
│   ├── rule-snippets/
│   ├── schema/
│   └── wiki.config.json.template
└── references/
    ├── 3-layer-architecture.md
    └── operations.md
```

## 프로젝트 적용

각 에이전트 프로젝트 루트에 `wiki.config.json` 작성 (템플릿 참조):

```bash
cd <AGENT_PROJECT>
python ~/.claude/skills/TWK/scripts/init_wiki.py --mode B  # Mode A=Pure, B=Session-Extract
```

출력: `docs/wiki/{decisions,patterns,concepts,postmortems,principles}/` + `index.md` + `log.md`.

## Dependencies

- Python ≥ 3.10
- (Optional) `qmd` CLI — wiki BM25/dense 검색 시. 미설치 시 lint/extract는 정상 동작, 검색만 제한.

## Naming History

- v0: `llm-wiki` — 2026-04-20 S34 위상군 자체 제작 (범용 Karpathy 구현)
- v1: **TWK (TriadWiKi)** — 2026-04-20 S35 fork 브랜드 공식화, 본 레포 분리

## Related Plugins

| 플러그인 | 역할 | 레포 |
|---------|------|------|
| **TEMS** | Topological Evolving Memory System (hook) | https://github.com/bobpullie/TEMS |
| **SDC** | Subagent Delegation Contract (skill) | https://github.com/bobpullie/SDC |
| **DVC** | Deterministic Verification Checklist (skill) | https://github.com/bobpullie/DVC |
| **TWK** (this) | LLM Wiki 3-Layer 방법론 (skill) | https://github.com/bobpullie/TWK |

## Vault Aggregator (v0.4+)

여러 프로젝트의 TWK 위키를 단일 통합 Obsidian Vault 로 묶고 GitHub mirror (`bobpullie/KJI_WIKI`) 에 자동 동기화.

- `vault_init.py` — 메타 vault 초기화
- `vault_join.py` — 프로젝트 합류 (junction 자동 생성)
- `vault_leave.py` — 프로젝트 제거 (원본 무영향)
- `vault_sync.py` — junction → mirror 복사 + git push
- `vault_status.py` — 상태 점검
- `vault_discover.py` — 미가입 프로젝트 탐색
- `session_end_hook.py` — 세션 종료 통합 (normalize + sync)

상세 매뉴얼: `references/vault-aggregation.md`

## License

MIT — see [LICENSE](LICENSE).
