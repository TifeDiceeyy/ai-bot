import base64
from dataclasses import dataclass

from fastapi.testclient import TestClient

from studio_ai.api.app import create_app
from studio_ai.core.types import EditInput, EditQuality, EditResult
from studio_ai.engineers import NaturalPassthrough
from studio_ai.runtime import Runtime


@dataclass
class StubEditor:
    id: str = "stub"
    license: str = "commercial-ok"

    def is_available(self) -> bool:
        return True

    def cost_for_quality(self, quality: EditQuality) -> float | None:
        return {"natural": 0.10, "upscale": 0.20}[quality]

    async def edit(self, edit_input: EditInput) -> EditResult:
        assert edit_input.instruction.startswith("make it blue")
        return EditResult(b"png-result", 1024, 768)


def create_test_client() -> TestClient:
    runtime = Runtime(
        editors={"banana": StubEditor()},  # type: ignore[dict-item]
        engineers={"natural-passthrough": NaturalPassthrough()},
    )
    return TestClient(create_app(runtime))


def test_quality_cost_contract() -> None:
    response = create_test_client().get("/api/quality-costs")
    assert response.status_code == 200
    assert response.json() == {"banana": {"natural": 0.10, "upscale": 0.20}}


def test_edit_contract() -> None:
    encoded = base64.b64encode(b"input-image").decode("ascii")
    response = create_test_client().post(
        "/api/edit",
        json={
            "imageBase64": f"data:image/png;base64,{encoded}",
            "instruction": "make it blue",
            "quality": "upscale",
            "editor": "banana",
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "imageBase64": "data:image/png;base64,cG5nLXJlc3VsdA==",
        "width": 1024,
        "height": 768,
    }


def test_invalid_base64_is_rejected() -> None:
    response = create_test_client().post(
        "/api/edit",
        json={
            "imageBase64": "not-base64!",
            "instruction": "make it blue",
            "editor": "banana",
        },
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid base64 image."}


def test_missing_fields_keep_existing_error_contract() -> None:
    response = create_test_client().post("/api/edit", json={"editor": "banana"})
    assert response.status_code == 400
    assert response.json() == {
        "error": "Body must include imageBase64 and instruction (both strings)."
    }
