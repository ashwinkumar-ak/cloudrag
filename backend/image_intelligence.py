import base64
import io
import json
from typing import Any
from pathlib import Path

from PIL import Image
import requests

from backend.config import settings
from backend.llm import LLMGenerationError
from backend.model_registry import validate_model


SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def is_supported_image(filename: str, content_type: str | None = None) -> bool:
    if content_type and content_type.lower() in SUPPORTED_IMAGE_TYPES:
        return True
    return Path(filename).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def normalized_image_mime_type(filename: str, content_type: str | None) -> str:
    if content_type and content_type.lower() in SUPPORTED_IMAGE_TYPES:
        return content_type.lower()
    mapping = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime_type = mapping.get(Path(filename).suffix.lower())
    if not mime_type:
        raise LLMGenerationError("Unsupported image type.")
    return mime_type


def image_dimensions(content: bytes) -> tuple[int | None, int | None]:
    try:
        with Image.open(io.BytesIO(content)) as image:
            return image.width, image.height
    except Exception:
        return None, None


def _parts_for_image(prompt: str, image_bytes: bytes, mime_type: str) -> list[dict[str, Any]]:
    return [
        {
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }
        },
        {"text": prompt},
    ]


def describe_image(
    image_bytes: bytes,
    mime_type: str,
    model: str | None = None,
) -> str:
    if not settings.gemini_api_key:
        raise LLMGenerationError("GEMINI_API_KEY is not configured.")

    if mime_type not in SUPPORTED_IMAGE_TYPES:
        raise LLMGenerationError("Unsupported image type.")

    selected_model = validate_model(model or settings.gemini_model)

    prompt = (
        "Analyze this image for a document intelligence system. "
        "Produce a factual, detailed description that can be searched later. "
        "Capture visible text when legible, tables, charts, diagrams, labels, "
        "relationships, objects, and important visual facts. Do not invent "
        "information. Return plain text only."
    )

    response = requests.post(
        f"{settings.gemini_api_base_url}/models/{selected_model}:generateContent",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        },
        json={
            "contents": [{"parts": _parts_for_image(prompt, image_bytes, mime_type)}],
            "generationConfig": {
                "thinkingConfig": {"thinkingLevel": "minimal"},
                "maxOutputTokens": 1200,
            },
        },
        timeout=120,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        try:
            detail = response.json().get("error", {}).get("message", "Unknown Gemini API error.")
        except ValueError:
            detail = "Unknown Gemini API error."
        raise LLMGenerationError(f"Gemini image analysis failed: {detail}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise LLMGenerationError("Gemini returned invalid image-analysis data.") from exc

    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise LLMGenerationError("Gemini returned no image-analysis candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and part.get("text") and part.get("thought") is not True
    ]
    description = "\n".join(texts).strip()

    if not description:
        raise LLMGenerationError("Gemini returned an empty image description.")

    return description
