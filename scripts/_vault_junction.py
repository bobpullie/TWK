"""Win32 junction (mklink /J) 생성/삭제/판별."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class JunctionError(Exception):
    """Junction 조작 오류."""


def create_junction(link: Path, target: Path) -> None:
    """link 위치에 target 을 가리키는 junction 생성."""
    if link.exists():
        raise JunctionError(f"link path already exists: {link}")
    if not target.exists():
        raise JunctionError(f"target does not exist: {target}")
    if not target.is_dir():
        raise JunctionError(f"target is not a directory: {target}")

    link.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        # mklink /J 는 cmd.exe 내장 명령
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target.resolve())],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise JunctionError(f"mklink failed: {result.stderr.strip()}")
    else:
        # POSIX fallback: symlink
        link.symlink_to(target.resolve(), target_is_directory=True)


def remove_junction(link: Path) -> None:
    """Junction 제거 — 원본 폴더는 건드리지 않음."""
    if not link.exists():
        return
    if sys.platform == "win32":
        # rmdir 은 junction 만 제거 (원본 무영향)
        result = subprocess.run(
            ["cmd", "/c", "rmdir", str(link)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise JunctionError(f"rmdir failed: {result.stderr.strip()}")
    else:
        link.unlink()


def is_junction(path: Path) -> bool:
    """경로가 junction 인지 판별."""
    if not path.exists():
        return False
    if sys.platform == "win32":
        # Win32 reparse point 검사
        try:
            attrs = os.stat(path, follow_symlinks=False).st_file_attributes
            FILE_ATTRIBUTE_REPARSE_POINT = 0x400
            return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
        except (AttributeError, OSError):
            return False
    return path.is_symlink()


def resolve_junction_target(link: Path) -> Path:
    """Junction 의 실제 target 경로 반환."""
    if not is_junction(link):
        raise JunctionError(f"not a junction: {link}")
    return link.resolve()
