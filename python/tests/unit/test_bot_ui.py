from studio_ai.editors.fal_editor import FalEditor, QualityTier
from studio_ai.telegram.bot import CONFLICT_EXIT_CODE, quality_keyboard


def test_conflict_exit_code_is_dedicated() -> None:
    assert CONFLICT_EXIT_CODE == 78


def test_quality_keyboard_uses_editor_costs() -> None:
    editor = FalEditor(
        id="test",
        endpoint="test/endpoint",
        quality={
            "natural": QualityTier({}, 0.15),
            "upscale": QualityTier({}, 0.30),
        },
    )
    keyboard = quality_keyboard(editor)
    buttons = keyboard.inline_keyboard[0]
    assert [button.text for button in buttons] == [
        "Natural — $0.15",
        "Upscale — $0.30",
    ]
