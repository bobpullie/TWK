import sys
from pathlib import Path

import pytest

from scripts._vault_junction import (
    create_junction, remove_junction, is_junction, resolve_junction_target,
    JunctionError,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Win32 junction only")


def test_create_and_resolve_junction(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "marker.txt").write_text("hello")

    link = tmp_path / "link"
    create_junction(link, target)

    assert is_junction(link)
    assert resolve_junction_target(link) == target.resolve()
    assert (link / "marker.txt").read_text() == "hello"


def test_create_junction_duplicate_raises(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    create_junction(link, target)
    with pytest.raises(JunctionError, match="already exists"):
        create_junction(link, target)


def test_remove_junction(tmp_path: Path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "marker.txt").write_text("hello")
    link = tmp_path / "link"
    create_junction(link, target)

    remove_junction(link)
    assert not link.exists()
    # 원본은 보존
    assert (target / "marker.txt").exists()


def test_is_junction_false_for_normal_dir(tmp_path: Path):
    normal = tmp_path / "normal"
    normal.mkdir()
    assert not is_junction(normal)
