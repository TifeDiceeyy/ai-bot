from __future__ import annotations

from builtins import list as list_type

from studio_ai.core.types import ImageEditor


class EditorRegistry:
    def __init__(self) -> None:
        self._editors: dict[str, ImageEditor] = {}

    def register(self, editor: ImageEditor) -> None:
        self._editors[editor.id] = editor

    def list(self) -> list_type[ImageEditor]:
        return list_type(self._editors.values())

    def select(self, editor_id: str) -> ImageEditor:
        try:
            return self._editors[editor_id]
        except KeyError as error:
            available = ", ".join(self._editors)
            raise ValueError(
                f"Unknown editor id: {editor_id}. Available: {available}"
            ) from error

    def filter_by_available(self) -> list_type[ImageEditor]:
        return [editor for editor in self.list() if editor.is_available()]
