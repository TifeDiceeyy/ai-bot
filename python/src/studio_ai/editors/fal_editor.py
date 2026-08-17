from dataclasses import dataclass, field
from typing import Any, Literal

from studio_ai.core.types import EditInput, EditQuality, EditResult, License
from studio_ai.fal_client import (
    download_as_png,
    fal_key_available,
    subscribe,
    upload_image,
)


@dataclass(frozen=True, slots=True)
class QualityTier:
    params: dict[str, Any]
    cost_usd: float


@dataclass(slots=True)
class FalEditor:
    id: str
    endpoint: str
    license: License = "commercial-ok"
    image_input_mode: Literal["url", "urls"] = "urls"
    quality: dict[EditQuality, QualityTier] = field(default_factory=dict)

    def is_available(self) -> bool:
        return fal_key_available()

    def cost_for_quality(self, quality: EditQuality) -> float | None:
        tier = self.quality.get(quality)
        return tier.cost_usd if tier else None

    async def edit(self, edit_input: EditInput) -> EditResult:
        image_url = await upload_image(edit_input.image)
        image_field: dict[str, Any]
        if self.image_input_mode == "url":
            image_field = {"image_url": image_url}
        else:
            image_field = {"image_urls": [image_url]}

        tier = self.quality.get(edit_input.quality)
        response = await subscribe(
            self.endpoint,
            {
                "prompt": edit_input.instruction,
                **image_field,
                **(tier.params if tier else {}),
            },
        )
        images = response.get("images")
        if not isinstance(images, list) or not images:
            raise RuntimeError(f"{self.endpoint} returned no images.")
        first = images[0]
        if not isinstance(first, dict) or not isinstance(first.get("url"), str):
            raise RuntimeError(f"{self.endpoint} returned an invalid image.")

        png, width, height = await download_as_png(first["url"])
        return EditResult(
            image=png,
            width=width,
            height=height,
            cost_usd=tier.cost_usd if tier else None,
        )
