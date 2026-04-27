"""TWK vault aggregator 공통 유틸 — config 로드/저장, 경로 탐색."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VAULT_CONFIG_NAME = "vault.config.json"
WIKI_CONFIG_NAME = "wiki.config.json"


class VaultConfigError(Exception):
    """vault.config.json / wiki.config.json 로드/파싱 오류."""


def load_vault_config(vault_root: Path) -> dict[str, Any]:
    path = vault_root / VAULT_CONFIG_NAME
    if not path.exists():
        raise VaultConfigError(f"vault.config.json not found at {vault_root}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VaultConfigError(f"vault.config.json malformed at {path}: {exc}") from exc


def save_vault_config(vault_root: Path, cfg: dict[str, Any]) -> None:
    path = vault_root / VAULT_CONFIG_NAME
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_wiki_config(project_root: Path) -> dict[str, Any]:
    path = project_root / WIKI_CONFIG_NAME
    if not path.exists():
        raise VaultConfigError(f"wiki.config.json not found at {project_root}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VaultConfigError(f"wiki.config.json malformed at {path}: {exc}") from exc


def save_wiki_config(project_root: Path, cfg: dict[str, Any]) -> None:
    path = project_root / WIKI_CONFIG_NAME
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def find_vault_config(start: Path) -> Path | None:
    """start 부터 부모 디렉토리로 올라가며 vault.config.json 탐색."""
    current = start.resolve()
    while True:
        if (current / VAULT_CONFIG_NAME).exists():
            return current
        if current.parent == current:
            return None
        current = current.parent
