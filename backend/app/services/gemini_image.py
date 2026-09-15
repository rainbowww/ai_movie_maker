"""Gemini image generation.

Uses the `google-genai` SDK's image-capable model (default
`gemini-2.5-flash-image`) to turn a text prompt into a PNG.
Docs: https://ai.google.dev/gemini-api/docs/image-generation

Requires GEMINI_API_KEY. Not covered by this repo's automated tests (no
network access in CI/sandbox) — see backend/scripts/smoke_test_gemini.py
to verify this against the live API once a key is configured.
"""
from __future__ import annotations

import base64
from pathlib import Path

from google import genai

from ..config import Settings


class GeminiImageError(RuntimeError):
    pass


def generate_image(settings: Settings, prompt: str, out_path: Path) -> Path:
    if not settings.has_gemini_key:
        raise GeminiImageError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_image_model,
        contents=[prompt],
    )

    for candidate in response.candidates or []:
        parts = getattr(candidate.content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                data = inline.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_bytes(data)
                return out_path

    raise GeminiImageError(
        "Gemini 응답에 이미지 데이터가 없습니다 (안전 필터에 걸렸거나 텍스트만 반환됨). "
        "프롬프트를 조정해 다시 시도하세요."
    )
