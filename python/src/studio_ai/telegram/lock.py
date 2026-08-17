import os
import sys
from pathlib import Path
from types import TracebackType

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class DuplicateInstanceError(RuntimeError):
    pass


def _lock_exclusive_nonblocking(lock_file: object) -> None:
    if sys.platform == "win32":
        # msvcrt.locking() refuses to lock a zero-byte region, so make sure
        # at least one byte exists before asking for the lock.
        lock_file.seek(0, 2)  # type: ignore[attr-defined]
        if lock_file.tell() == 0:  # type: ignore[attr-defined]
            lock_file.write(" ")  # type: ignore[attr-defined]
            lock_file.flush()  # type: ignore[attr-defined]
        lock_file.seek(0)  # type: ignore[attr-defined]
        try:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]
        except OSError as error:
            raise BlockingIOError from error
    else:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore[attr-defined]


def _unlock(lock_file: object) -> None:
    if sys.platform == "win32":
        lock_file.seek(0)  # type: ignore[attr-defined]
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
    else:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


class ProcessLock:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._file: object | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = self.path.open("a+", encoding="utf-8")
        try:
            _lock_exclusive_nonblocking(lock_file)
        except BlockingIOError as error:
            lock_file.seek(0)
            owner = lock_file.read().strip() or "unknown"
            lock_file.close()
            raise DuplicateInstanceError(
                f"another Telegram bot process already holds {self.path} "
                f"(PID {owner})"
            ) from error
        lock_file.seek(0)
        lock_file.truncate()
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        self._file = lock_file

    def release(self) -> None:
        if self._file is None:
            return
        lock_file = self._file
        _unlock(lock_file)
        lock_file.close()  # type: ignore[attr-defined]
        self._file = None

    def __enter__(self) -> "ProcessLock":
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc_type, exc_value, traceback
        self.release()
