from dataclasses import dataclass

from studio_ai.core.registry import EditorRegistry
from studio_ai.core.types import EditQuality, ImageEditor, PromptEngineer
from studio_ai.editors import create_editors
from studio_ai.engineers import NaturalPassthrough, Passthrough, VisionEngineer


@dataclass(frozen=True, slots=True)
class Runtime:
    editors: dict[str, ImageEditor]
    engineers: dict[str, PromptEngineer]

    def quality_costs(self) -> dict[str, dict[EditQuality, float]]:
        costs: dict[str, dict[EditQuality, float]] = {}
        for codename, editor in self.editors.items():
            editor_costs: dict[EditQuality, float] = {}
            for quality in ("natural", "upscale"):
                cost = editor.cost_for_quality(quality)
                if cost is not None:
                    editor_costs[quality] = cost
            costs[codename] = editor_costs
        return costs


def create_runtime() -> Runtime:
    registry = EditorRegistry()
    for editor in create_editors():
        registry.register(editor)

    return Runtime(
        editors={
            "banana": registry.select("nano-banana-pro"),
            "dream": registry.select("seedream-5-pro"),
        },
        engineers={
            "passthrough": Passthrough(),
            "natural-passthrough": NaturalPassthrough(),
            # Not yet the active engineer anywhere (still natural-passthrough,
            # see prompt-quality-reference.md) — available for A/B testing
            # per CLAUDE.md's Phase 4 gate.
            "claude-opus-5": VisionEngineer(
                id="claude-opus-5", model="anthropic/claude-opus-5"
            ),
        },
    )
