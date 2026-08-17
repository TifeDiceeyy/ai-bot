from pathlib import Path

import pytest

from studio_ai.telegram.lock import DuplicateInstanceError, ProcessLock


def test_second_instance_is_rejected_and_release_allows_restart(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bot.lock"
    first = ProcessLock(path)
    second = ProcessLock(path)

    first.acquire()
    with pytest.raises(DuplicateInstanceError, match="already holds"):
        second.acquire()
    first.release()

    second.acquire()
    second.release()
