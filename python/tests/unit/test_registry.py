from dataclasses import dataclass

import pytest

from studio_ai.core.registry import EditorRegistry
from studio_ai.core.types import EditInput, EditQuality, EditResult


@dataclass
class StubEditor:
    id: str
    available: bool = True
    license: str = "commercial-ok"

    def is_available(self) -> bool:
        return self.available

    def cost_for_quality(self, quality: EditQuality) -> float | None:
        del quality
        return None

    async def edit(self, edit_input: EditInput) -> EditResult:
        del edit_input
        return EditResult(b"image", 1, 1)


def test_registry_selects_and_filters() -> None:
    registry = EditorRegistry()
    registry.register(StubEditor("ready"))  # type: ignore[arg-type]
    registry.register(StubEditor("offline", available=False))  # type: ignore[arg-type]

    assert registry.select("ready").id == "ready"
    assert [editor.id for editor in registry.filter_by_available()] == ["ready"]


def test_registry_reports_unknown_editor() -> None:
    registry = EditorRegistry()
    registry.register(StubEditor("known"))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Unknown editor id: missing"):
        registry.select("missing")
