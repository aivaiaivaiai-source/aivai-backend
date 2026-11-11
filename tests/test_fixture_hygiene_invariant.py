"""Fixture hygiene: Package B write tests must tear down listings."""
from __future__ import annotations

from pathlib import Path

TESTS = Path(__file__).resolve().parent

# Known shared-DB write tests that historically leaked PKG-B listings.
_MUST_TEARDOWN = (
    "test_food_agri_v2_package_b.py",
    "test_electronics_v2_package_b_search.py",
)


def _has_listing_write(src: str) -> bool:
    return "Listing(" in src and "session.add(listing)" in src


def _has_teardown(src: str) -> bool:
    return (
        "finally:" in src
        and ("Listing.__table__.delete" in src or "session.delete" in src)
        and ("created_ids" in src or "created:" in src or "created =" in src)
    )


def test_known_package_b_write_tests_have_teardown() -> None:
    for name in _MUST_TEARDOWN:
        path = TESTS / name
        assert path.is_file(), name
        src = path.read_text(encoding="utf-8")
        assert _has_listing_write(src), f"{name} expected Listing writes"
        assert _has_teardown(src), f"{name} must finally-delete tracked fixtures"


def test_package_b_search_write_files_are_fixture_safe_or_readonly() -> None:
    """Scan *package_b* tests: if they write Listing rows, require teardown."""
    leaks: list[str] = []
    for path in sorted(TESTS.glob("test_*package_b*.py")):
        src = path.read_text(encoding="utf-8")
        if not _has_listing_write(src):
            continue
        if not _has_teardown(src):
            leaks.append(path.name)
    assert leaks == [], f"Package B write tests missing teardown: {leaks}"
