from studio_ai.engineers.passthrough import Passthrough

REALISM_SUFFIX = (
    "Photorealistic, unedited-photo look — not an AI-generated aesthetic: "
    "visible skin pore texture, no airbrushing, no added sharpness or clarity "
    "boost, natural (not artificially crisp) focus, no HDR glow or "
    "oversaturated color."
)


class NaturalPassthrough:
    id = "natural-passthrough"

    def __init__(self) -> None:
        self._passthrough = Passthrough()

    async def engineer(self, image: bytes, user_prompt: str) -> str:
        base = await self._passthrough.engineer(image, user_prompt)
        return f"{base} {REALISM_SUFFIX}"
