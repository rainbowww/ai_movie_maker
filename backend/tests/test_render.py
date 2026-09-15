"""Proves the ffmpeg render pipeline actually works, using synthetic
fixtures (a solid-color PNG, a short silent WAV) instead of real Gemini
output — no network or API key required, so this runs in any CI.
"""
from __future__ import annotations

import wave
from pathlib import Path

import pytest
from PIL import Image

from app.services.video_render import probe_duration, render_project_video


def _make_test_image(path: Path, color=(30, 30, 60)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 450), color).save(path, "PNG")
    return path


def _make_test_wav(path: Path, seconds: float = 1.5, rate: int = 24000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames = int(seconds * rate)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * n_frames)  # silence
    return path


def test_render_project_video_with_and_without_audio(tmp_path: Path):
    img1 = _make_test_image(tmp_path / "scene1.png", (30, 30, 60))
    img2 = _make_test_image(tmp_path / "scene2.png", (60, 30, 30))
    wav1 = _make_test_wav(tmp_path / "scene1.wav", seconds=1.5)

    out_path = tmp_path / "final.mp4"
    work_dir = tmp_path / "_work"

    total = render_project_video(
        scene_assets=[(img1, wav1), (img2, None)],
        out_path=out_path,
        work_dir=work_dir,
    )

    assert out_path.exists(), "최종 mp4가 생성되지 않았습니다"
    assert out_path.stat().st_size > 0

    # scene1 duration comes from its audio (~1.5s), scene2 falls back to 3.0s
    assert total == pytest.approx(1.5 + 3.0, abs=0.05)

    actual_duration = probe_duration(out_path)
    assert actual_duration == pytest.approx(total, abs=0.2)
