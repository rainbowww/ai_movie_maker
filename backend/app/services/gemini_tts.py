"""Gemini text-to-speech.

Uses a Gemini TTS-capable model (default `gemini-2.5-flash-preview-tts`)
with a prebuilt voice. Gemini TTS returns raw 16-bit PCM audio (24kHz,
mono) which this module wraps in a standard WAV header so the result is a
directly playable .wav file.
Docs: https://ai.google.dev/gemini-api/docs/speech-generation

Requires GEMINI_API_KEY. Not covered by this repo's automated tests (no
network access in CI/sandbox) — see backend/scripts/smoke_test_gemini.py
to verify this against the live API once a key is configured. Prebuilt
voice names (e.g. "Puck", "Kore", "Zephyr", "Charon", "Fenrir", "Aoede", …)
are documented on that same page — preview them in Google AI Studio before
assigning voice_m / voice_f on a project, since their listed character
descriptions (upbeat / firm / bright / …) are a better guide than gender
labels.
"""
from __future__ import annotations

import base64
import wave
from pathlib import Path

from google import genai
from google.genai import types

from ..config import Settings

PCM_SAMPLE_RATE = 24000
PCM_SAMPLE_WIDTH = 2  # bytes (16-bit)
PCM_CHANNELS = 1


class GeminiTTSError(RuntimeError):
    pass


def _write_wav(pcm_bytes: bytes, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(PCM_CHANNELS)
        wf.setsampwidth(PCM_SAMPLE_WIDTH)
        wf.setframerate(PCM_SAMPLE_RATE)
        wf.writeframes(pcm_bytes)


def generate_speech(settings: Settings, text: str, voice_name: str, out_path: Path) -> Path:
    if not settings.has_gemini_key:
        raise GeminiTTSError("GEMINI_API_KEY가 설정되지 않았습니다.")
    if not text.strip():
        raise GeminiTTSError("대사 텍스트가 비어 있습니다.")

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_tts_model,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            ),
        ),
    )

    for candidate in response.candidates or []:
        parts = getattr(candidate.content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline and inline.data:
                data = inline.data
                if isinstance(data, str):
                    data = base64.b64decode(data)
                _write_wav(data, out_path)
                return out_path

    raise GeminiTTSError("Gemini 응답에 오디오 데이터가 없습니다.")
