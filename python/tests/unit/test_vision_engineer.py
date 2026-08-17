from typing import Any

import pytest

from studio_ai.engineers.vision_engineer import SYSTEM_INSTRUCTION, VisionEngineer


def _engineer() -> VisionEngineer:
    return VisionEngineer(id="claude-opus-5", model="anthropic/claude-opus-5")


async def test_builds_expected_request_and_returns_stripped_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, Any] = {}

    async def fake_upload_image(image: bytes) -> str:
        calls["uploaded_image"] = image
        return "https://cdn.example/image.png"

    async def fake_subscribe(
        endpoint: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        calls["endpoint"] = endpoint
        calls["arguments"] = arguments
        return {
            "output": "  Change the background to a beach. Preserve the "
            "subject's pose, framing, and identity.  "
        }

    monkeypatch.setattr(
        "studio_ai.engineers.vision_engineer.upload_image", fake_upload_image
    )
    monkeypatch.setattr(
        "studio_ai.engineers.vision_engineer.subscribe", fake_subscribe
    )

    instruction = await _engineer().engineer(b"image-bytes", "put me at the beach")

    assert calls["uploaded_image"] == b"image-bytes"
    assert calls["endpoint"] == "openrouter/router/vision"
    assert calls["arguments"]["image_urls"] == ["https://cdn.example/image.png"]
    assert calls["arguments"]["model"] == "anthropic/claude-opus-5"
    assert (
        calls["arguments"]["prompt"]
        == f"{SYSTEM_INSTRUCTION}\n\nUser's request: put me at the beach"
    )
    assert instruction == (
        "Change the background to a beach. Preserve the subject's pose, "
        "framing, and identity."
    )


async def test_raises_when_no_output_text(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_upload_image(image: bytes) -> str:
        del image
        return "https://cdn.example/image.png"

    async def fake_subscribe(
        endpoint: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        del endpoint, arguments
        return {}

    monkeypatch.setattr(
        "studio_ai.engineers.vision_engineer.upload_image", fake_upload_image
    )
    monkeypatch.setattr(
        "studio_ai.engineers.vision_engineer.subscribe", fake_subscribe
    )

    with pytest.raises(RuntimeError, match="returned no output text"):
        await _engineer().engineer(b"image-bytes", "put me at the beach")


def test_system_instruction_no_longer_tells_the_model_to_invent_content() -> None:
    # Regression guard for the documented over-invention bug (an unrequested
    # mirror-selfie stance and gold jewelry) — see
    # .claude/project/prompt-quality-reference.md. The old instruction said
    # "missing an implied action is as wrong as ignoring a stated one",
    # which is what caused it.
    assert (
        "missing an implied action is as wrong as ignoring a stated one"
        not in SYSTEM_INSTRUCTION
    )
    assert "do not invent" in SYSTEM_INSTRUCTION.lower()
