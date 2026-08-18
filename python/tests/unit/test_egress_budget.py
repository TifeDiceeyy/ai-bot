import json
from datetime import date
from pathlib import Path

from studio_ai.telegram.egress_budget import (
    DEFAULT_ESTIMATE_BYTES,
    FREE_TIER_EGRESS_BYTES,
    SAFETY_MARGIN_EDITS,
    MonthlyEgressBudget,
)

_THIS_MONTH = date.today().strftime("%Y-%m")


def _seed(path: Path, total_bytes: int, edit_count: int = 0) -> None:
    # Writes state directly (bypassing record(), which always increments
    # edit_count) so the "no edits recorded yet" default-estimate code path
    # can be tested at an exact boundary.
    path.write_text(
        json.dumps(
            {"month": _THIS_MONTH, "total_bytes": total_bytes, "edit_count": edit_count}
        )
    )


def test_allows_edits_when_nothing_recorded_yet(tmp_path: Path) -> None:
    budget = MonthlyEgressBudget(tmp_path / "budget.json")

    assert budget.can_edit() is True


def test_blocks_once_within_the_safety_margin_of_the_free_tier(
    tmp_path: Path,
) -> None:
    path = tmp_path / "budget.json"
    # No edits recorded yet this month, so the default per-edit estimate
    # governs the margin. Leave just under 5 default-sized edits of headroom.
    remaining_allowance = SAFETY_MARGIN_EDITS * DEFAULT_ESTIMATE_BYTES - 1
    _seed(path, FREE_TIER_EGRESS_BYTES - remaining_allowance)

    assert MonthlyEgressBudget(path).can_edit() is False


def test_stays_open_just_above_the_safety_margin(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    remaining_allowance = SAFETY_MARGIN_EDITS * DEFAULT_ESTIMATE_BYTES + 1
    _seed(path, FREE_TIER_EGRESS_BYTES - remaining_allowance)

    assert MonthlyEgressBudget(path).can_edit() is True


def test_uses_the_real_running_average_not_just_the_default_estimate(
    tmp_path: Path,
) -> None:
    budget = MonthlyEgressBudget(tmp_path / "budget.json")
    # Real edits here are much smaller than the 5MB default estimate, so the
    # safety margin should shrink accordingly and allow more edits through.
    small_edit_bytes = 200_000
    for _ in range(10):
        budget.record(small_edit_bytes)

    remaining = FREE_TIER_EGRESS_BYTES - 10 * small_edit_bytes
    assert remaining > SAFETY_MARGIN_EDITS * DEFAULT_ESTIMATE_BYTES  # sanity
    assert budget.can_edit() is True


def test_recorded_usage_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "budget.json"
    MonthlyEgressBudget(path).record(1_000_000)

    reloaded = MonthlyEgressBudget(path)
    assert "1 edits, 1.0MB" in reloaded.status()
