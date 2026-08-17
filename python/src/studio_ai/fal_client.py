import asyncio
import hashlib
import io
import os
from collections.abc import Mapping
from typing import Any

import fal_client
import httpx
from PIL import Image

_upload_cache: dict[str, str] = {}
_upload_locks: dict[str, asyncio.Lock] = {}


def fal_key_available() -> bool:
    return bool(os.environ.get("FAL_KEY"))


def _require_key() -> None:
    if not fal_key_available():
        raise RuntimeError(
            "FAL_KEY is not set. Copy .env.example to .env and fill it in."
        )


async def upload_image(image: bytes) -> str:
    _require_key()
    digest = hashlib.sha256(image).hexdigest()
    if cached := _upload_cache.get(digest):
        return cached

    lock = _upload_locks.setdefault(digest, asyncio.Lock())
    async with lock:
        if cached := _upload_cache.get(digest):
            return cached
        url = await asyncio.to_thread(fal_client.upload, image, "image/png")
        _upload_cache[digest] = url
        return url


async def subscribe(endpoint: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
    _require_key()
    result = await asyncio.to_thread(
        fal_client.subscribe,
        endpoint,
        arguments=dict(arguments),
        with_logs=False,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"{endpoint} returned an invalid response.")
    return result


async def download_as_png(url: str) -> tuple[bytes, int, int]:
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(url)
        response.raise_for_status()

    with Image.open(io.BytesIO(response.content)) as source:
        width, height = source.size
        output = io.BytesIO()
        source.save(output, format="PNG")
    return output.getvalue(), width, height
