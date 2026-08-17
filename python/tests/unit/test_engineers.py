import pytest

from studio_ai.engineers.natural_passthrough import (
    REALISM_SUFFIX,
    NaturalPassthrough,
)
from studio_ai.engineers.passthrough import Passthrough


@pytest.mark.asyncio
async def test_passthrough_does_not_change_prompt() -> None:
    assert await Passthrough().engineer(b"image", "make it blue") == "make it blue"


@pytest.mark.asyncio
async def test_natural_passthrough_appends_exact_suffix() -> None:
    instruction = await NaturalPassthrough().engineer(b"image", "make it blue")
    assert instruction == f"make it blue {REALISM_SUFFIX}"
