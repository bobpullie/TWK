from datetime import date
from pathlib import Path

from scripts.vault_status import collect_status, format_report
from scripts.vault_join import apply_join


def test_collect_status_healthy(initialized_vault: Path, fake_project: Path):
    apply_join(
        vault_root=initialized_vault, project_root=fake_project,
        project_id="fake", name="Fake", description="x",
        wiki_path="docs/wiki", handover_path="handover_doc",
        session_archive_path=None, recap_path=None,
        status="Active", tags=[], joined_at=date(2026, 4, 27),
    )
    status = collect_status(initialized_vault)
    assert status["projects"]["fake"]["health"] == "healthy"
    assert status["projects"]["fake"]["page_count"] == 1


def test_collect_status_broken_junction(initialized_vault: Path, fake_project: Path):
    apply_join(
        vault_root=initialized_vault, project_root=fake_project,
        project_id="fake", name="Fake", description="x",
        wiki_path="docs/wiki", handover_path="handover_doc",
        session_archive_path=None, recap_path=None,
        status="Active", tags=[], joined_at=date(2026, 4, 27),
    )
    # 원본 wiki 삭제 → junction 깨짐
    import shutil
    shutil.rmtree(fake_project / "docs" / "wiki")

    status = collect_status(initialized_vault)
    assert status["projects"]["fake"]["health"] == "broken"


def test_format_report_contains_table(initialized_vault: Path):
    status = {
        "vault_id": "test",
        "vault_root": str(initialized_vault),
        "mirror": "https://github.com/x/y.git",
        "last_sync": "N/A",
        "projects": {},
    }
    report = format_report(status)
    assert "vault_id" in report or "test" in report
