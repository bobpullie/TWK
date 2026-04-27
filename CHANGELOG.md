# TWK Changelog

## v0.4.0 (2026-04-27) — Vault Aggregator

### Added
- `scripts/vault_init.py` — 메타 vault 초기화
- `scripts/vault_join.py` — 프로젝트 합류 (junction 생성)
- `scripts/vault_leave.py` — 프로젝트 제거 (원본 무영향)
- `scripts/vault_sync.py` — junction → mirror 복사 + git push (orphan cleanup 포함)
- `scripts/vault_status.py` — 상태 점검
- `scripts/vault_discover.py` — 미가입 프로젝트 탐색
- `scripts/session_end_hook.py` — 세션 종료 통합
- `scripts/_vault_common.py`, `scripts/_vault_junction.py` — 공통 유틸
- `templates/vault.config.json.template`
- `templates/vault_index.md.template`
- `templates/page-templates/project_index.md.template`
- `references/vault-aggregation.md` — 운영 매뉴얼
- `tests/` — pytest 스위트 (44 테스트, Win32 integration 포함)

### Changed
- `wiki.config.json` schema: `vault_membership` 옵션 필드 추가 (v1.2)

### Backward Compatibility
- 기존 wiki.config.json (v1.1) 무수정 호환
- 기존 init_wiki/lint/extract_session_raw/normalize_session_frontmatter 동작 변경 없음

### Notes
- `vault_sync` orphan cleanup 은 destructive: `mirror_root/{projects,handovers,session_archive}/<id>` 디렉토리가 `cfg.projects` 에 없으면 자동 삭제. 수동으로 mirror 에 추가한 폴더는 다음 sync 시 사라지므로, mirror 직접 편집은 권장하지 않음.
- Win32-only integration test (`test_full_lifecycle`) — Linux/macOS 환경에서는 skip. Win32 가 v0.4 의 1차 deployment target.
- Lessons learned (T7-T19): Path → JSON serialization 은 `Path.as_posix()` 사용 (T8 lesson, codified in vault_join + vault_init). External library exceptions wrap to domain exceptions (T3 lesson, applied throughout).
