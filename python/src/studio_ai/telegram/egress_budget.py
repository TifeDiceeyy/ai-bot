import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

# GCP's Always Free tier gives 1 GB/month of network egress. Deliberately
# use the smaller decimal-GB reading (not GiB) so this errs on the side of
# blocking earlier rather than risking an actual bill.
FREE_TIER_EGRESS_BYTES = 1_000_000_000

# Worst-case per-edit egress (upload to fal.ai + send the edited PNG to
# Telegram) to assume until real data accumulates this month — lossless PNG
# output commonly runs 2-5MB, so 5MB is a conservative starting estimate.
DEFAULT_ESTIMATE_BYTES = 5_000_000

# How many average-sized edits of headroom must remain before the free tier
# threshold to keep allowing edits. This is the safety margin, not a literal
# "5 edits left" counter — it's recomputed from the real running average.
SAFETY_MARGIN_EDITS = 5


@dataclass(slots=True)
class _MonthState:
    month: str
    total_bytes: int = 0
    edit_count: int = 0


class MonthlyEgressBudget:
    """Blocks new edits once remaining free-tier egress headroom is thin.

    Tracks real, measured egress bytes per edit (upload to the image editor
    + the final image sent to Telegram) rather than guessing, so the
    estimate gets more accurate as the month goes on. Resets automatically
    when the calendar month changes. Persisted to a JSON file so it
    survives restarts.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _month_key(self) -> str:
        return date.today().strftime("%Y-%m")

    def _load(self) -> _MonthState:
        month = self._month_key()
        if not self._path.exists():
            return _MonthState(month=month)
        raw = self._path.read_text(encoding="utf-8").strip()
        data = json.loads(raw) if raw else {}
        if data.get("month") != month:
            return _MonthState(month=month)
        return _MonthState(
            month=month,
            total_bytes=int(data.get("total_bytes", 0)),
            edit_count=int(data.get("edit_count", 0)),
        )

    def _write(self, state: _MonthState) -> None:
        self._path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")

    def can_edit(self) -> bool:
        state = self._load()
        average = (
            state.total_bytes / state.edit_count
            if state.edit_count
            else DEFAULT_ESTIMATE_BYTES
        )
        remaining = FREE_TIER_EGRESS_BYTES - state.total_bytes
        return remaining > SAFETY_MARGIN_EDITS * average

    def record(self, egress_bytes: int) -> None:
        state = self._load()
        state.total_bytes += egress_bytes
        state.edit_count += 1
        self._write(state)

    def status(self) -> str:
        state = self._load()
        used_mb = state.total_bytes / 1_000_000
        cap_mb = FREE_TIER_EGRESS_BYTES / 1_000_000
        return (
            f"This month ({state.month}): {state.edit_count} edits, "
            f"{used_mb:.1f}MB / {cap_mb:.0f}MB egress used."
        )
