from studio_ai.telegram.pending_store import InMemoryPendingStore, PendingEdit


async def test_set_then_get_round_trips() -> None:
    store = InMemoryPendingStore()
    await store.set(1, PendingEdit("file-1", "make it blue"))

    job = await store.get(1)

    assert job == PendingEdit("file-1", "make it blue")


async def test_get_missing_chat_returns_none() -> None:
    store = InMemoryPendingStore()

    assert await store.get(404) is None


async def test_delete_removes_entry() -> None:
    store = InMemoryPendingStore()
    await store.set(1, PendingEdit("file-1"))

    await store.delete(1)

    assert await store.get(1) is None


async def test_delete_missing_chat_is_a_no_op() -> None:
    store = InMemoryPendingStore()

    await store.delete(404)
