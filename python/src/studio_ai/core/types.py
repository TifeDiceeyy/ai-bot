from dataclasses import dataclass
from typing import Literal, Protocol

EditQuality = Literal["natural", "upscale"]
License = Literal["commercial-ok", "non-commercial"]


@dataclass(frozen=True, slots=True)
class EditInput:
    image: bytes
    instruction: str
    quality: EditQuality = "natural"


@dataclass(frozen=True, slots=True)
class EditResult:
    image: bytes
    width: int
    height: int
    cost_usd: float | None = None


class ImageEditor(Protocol):
    id: str
    license: License

    def is_available(self) -> bool: ...

    def cost_for_quality(self, quality: EditQuality) -> float | None: ...

    async def edit(self, edit_input: EditInput) -> EditResult: ...


class PromptEngineer(Protocol):
    id: str

    async def engineer(self, image: bytes, user_prompt: str) -> str: ...
