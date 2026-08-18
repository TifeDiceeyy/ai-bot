from pathlib import Path

from studio_ai.telegram.authorized_users import AuthorizedUserStore


def test_bootstraps_from_given_user_id_on_first_use(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", bootstrap_user_id=42)

    assert store.is_authorized(42)
    assert store.list_ids() == [42]


def test_bootstraps_empty_when_no_user_id_given(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", bootstrap_user_id=None)

    assert store.list_ids() == []
    assert not store.is_authorized(42)


def test_add_grants_access_and_persists_across_instances(tmp_path: Path) -> None:
    path = tmp_path / "users.json"
    AuthorizedUserStore(path).add(99)

    reloaded = AuthorizedUserStore(path)
    assert reloaded.is_authorized(99)


def test_remove_revokes_access_and_reports_whether_it_existed(tmp_path: Path) -> None:
    store = AuthorizedUserStore(tmp_path / "users.json", bootstrap_user_id=42)

    assert store.remove(42) is True
    assert not store.is_authorized(42)
    assert store.remove(42) is False


def test_existing_file_is_not_overwritten_by_a_later_bootstrap_id(
    tmp_path: Path,
) -> None:
    path = tmp_path / "users.json"
    AuthorizedUserStore(path, bootstrap_user_id=1)

    reopened = AuthorizedUserStore(path, bootstrap_user_id=2)
    assert reopened.list_ids() == [1]
