import base64
import binascii
import os
from typing import cast

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from studio_ai.config import get_settings
from studio_ai.core.types import EditInput, EditQuality
from studio_ai.runtime import Runtime, create_runtime

MAX_IMAGE_BYTES = 18 * 1024 * 1024


class EditRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    imageBase64: str
    instruction: str
    quality: str = "natural"
    editor: str


class EditResponse(BaseModel):
    imageBase64: str
    width: int
    height: int


def parse_quality(value: str) -> EditQuality:
    return cast(EditQuality, value) if value in ("natural", "upscale") else "natural"


def decode_image(value: str) -> bytes:
    raw = value.split(",", maxsplit=1)[-1]
    try:
        image = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as error:
        raise HTTPException(status_code=400, detail="Invalid base64 image.") from error
    if len(image) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large.")
    return image


def create_app(runtime: Runtime | None = None) -> FastAPI:
    app = FastAPI(title="Studio AI", version="0.1.0")
    app.state.runtime = runtime or create_runtime()

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error: HTTPException) -> JSONResponse:
        del request
        return JSONResponse(
            status_code=error.status_code,
            content={"error": error.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        del request, error
        return JSONResponse(
            status_code=400,
            content={
                "error": "Body must include imageBase64 and instruction (both strings)."
            },
        )

    @app.get("/api/quality-costs")
    async def quality_costs() -> dict[str, dict[EditQuality, float]]:
        selected_runtime: Runtime = app.state.runtime
        return selected_runtime.quality_costs()

    @app.post("/api/edit", response_model=EditResponse)
    async def edit(body: EditRequest) -> EditResponse:
        selected_runtime: Runtime = app.state.runtime
        editor = selected_runtime.editors.get(body.editor)
        if editor is None:
            available = ", ".join(selected_runtime.editors)
            raise HTTPException(
                status_code=400, detail=f"Unknown editor. Available: {available}"
            )
        if not editor.is_available():
            raise HTTPException(
                status_code=400,
                detail="Image editor is not available (missing FAL_KEY?).",
            )
        engineer = selected_runtime.engineers["natural-passthrough"]
        image = decode_image(body.imageBase64)
        try:
            instruction = await engineer.engineer(image, body.instruction)
            result = await editor.edit(
                EditInput(image, instruction, parse_quality(body.quality))
            )
        except HTTPException:
            raise
        except Exception as error:
            raise HTTPException(status_code=502, detail=str(error)) from error
        encoded = base64.b64encode(result.image).decode("ascii")
        return EditResponse(
            imageBase64=f"data:image/png;base64,{encoded}",
            width=result.width,
            height=result.height,
        )

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "studio_ai.api.app:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=settings.port,
    )
