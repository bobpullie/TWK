# TWK Vault Aggregator (v0.4+)

여러 TWK 프로젝트의 위키를 단일 통합 Obsidian Vault 로 묶는 모듈.

## 명령어 요약

| 명령 | 용도 |
|------|------|
| `twk vault init` | 메타 vault 초기화 |
| `twk vault join` | 프로젝트 합류 (junction 생성) |
| `twk vault leave` | 프로젝트 제거 (원본 무영향) |
| `twk vault sync` | Junction → mirror 복사 + git push |
| `twk vault status` | 등록된 프로젝트 상태 점검 |
| `twk vault discover` | 미가입 TWK 프로젝트 탐색 |

## 빠른 시작

1. 메타 vault 초기화:
   ```bash
   python ~/.claude/skills/TWK/scripts/vault_init.py \
     --vault-id kji-knowledge-vault \
     --vault-root E:/TWK_Vault \
     --mirror-root E:/KJI_WIKI \
     --mirror-remote https://github.com/bobpullie/KJI_WIKI.git \
     --allowed-email blueitems7@gmail.com
   ```

2. 프로젝트 합류:
   ```bash
   cd E:/MyProject  # wiki.config.json 있는 폴더
   python ~/.claude/skills/TWK/scripts/vault_join.py
   ```

3. 수동 sync:
   ```bash
   python ~/.claude/skills/TWK/scripts/vault_sync.py
   ```

## 디렉토리 모델

(spec 의 Section 1.5 참조)

## Edge Cases

(구현 시 채움 — Task 21 에서 보강)
