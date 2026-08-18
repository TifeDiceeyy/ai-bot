import json
from pathlib import Path


class AuthorizedUserStore:
    """Persistent set of Telegram user ids allowed to use the bot.

    Backed by a small JSON file so access granted via /promote survives a
    restart. Seeded from `bootstrap_user_id` (ALLOWED_TELEGRAM_USER_ID) the
    first time the file doesn't exist yet, so existing single-user setups
    keep working without manual migration.
    """

    def __init__(self, path: str | Path, bootstrap_user_id: int | None = None) -> None:
        self._path = Path(path)
        if not self._path.exists():
            self._path.parent.mkdir(parents=True, exist_ok=True)
            initial = [bootstrap_user_id] if bootstrap_user_id is not None else []
            self._write(initial)

    def _read(self) -> list[int]:
        raw = self._path.read_text(encoding="utf-8").strip()
        return json.loads(raw) if raw else []

    def _write(self, user_ids: list[int]) -> None:
        self._path.write_text(json.dumps(user_ids, indent=2), encoding="utf-8")

    def is_authorized(self, user_id: int) -> bool:
        return user_id in self._read()

    def add(self, user_id: int) -> None:
        user_ids = self._read()
        if user_id not in user_ids:
            user_ids.append(user_id)
            self._write(user_ids)

    def remove(self, user_id: int) -> bool:
        user_ids = self._read()
        if user_id not in user_ids:
            return False
        user_ids.remove(user_id)
        self._write(user_ids)
        return True

    def list_ids(self) -> list[int]:
        return self._read()
