"""Proves the ffmpeg render pipeline actually works, using synthetic
fixtures (a solid-color PNG, a short silent WAV) instead of real Gemini
output — no network or API key required, so this runs in any CI.
"""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import pytest
from PIL import Image

from app.services.subtitles import (
    MAX_CHARS_PER_CUE,
    caption_cues,
    find_korean_font,
    split_caption,
    srt_timestamp,
    wrap_caption,
)
from app.services.video_render import (
    OUTPUT_H,
    SceneAsset,
    probe_duration,
    render_project_video,
)


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


def _extract_frame(video: Path, out_png: Path, at_seconds: float = 0.5) -> Path:
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(at_seconds), "-i", str(video), "-frames:v", "1", str(out_png)],
        capture_output=True,
        check=True,
    )
    return out_png


def test_render_project_video_with_and_without_audio(tmp_path: Path):
    img1 = _make_test_image(tmp_path / "scene1.png", (30, 30, 60))
    img2 = _make_test_image(tmp_path / "scene2.png", (60, 30, 30))
    wav1 = _make_test_wav(tmp_path / "scene1.wav", seconds=1.5)

    out_path = tmp_path / "final.mp4"
    total = render_project_video(
        scenes=[
            SceneAsset(img1, wav1, "첫 번째 장면 자막입니다."),
            SceneAsset(img2, None, "두 번째 장면 자막입니다."),
        ],
        out_path=out_path,
        work_dir=tmp_path / "_work",
    )

    assert out_path.exists(), "최종 mp4가 생성되지 않았습니다"
    assert out_path.stat().st_size > 0

    # scene1 duration comes from its audio (~1.5s), scene2 falls back to 3.0s
    assert total == pytest.approx(1.5 + 3.0, abs=0.05)
    assert probe_duration(out_path) == pytest.approx(total, abs=0.2)


def test_project_srt_is_written_with_matching_timings(tmp_path: Path):
    img = _make_test_image(tmp_path / "scene.png")
    wav = _make_test_wav(tmp_path / "scene.wav", seconds=2.0)

    out_path = tmp_path / "final.mp4"
    render_project_video(
        scenes=[SceneAsset(img, wav, "자막 동기화 확인용 문장입니다.")],
        out_path=out_path,
        work_dir=tmp_path / "_work",
    )

    srt_path = out_path.with_suffix(".srt")
    assert srt_path.exists(), "프로젝트 .srt 파일이 생성되지 않았습니다"
    body = srt_path.read_text(encoding="utf-8")
    assert "자막 동기화 확인용 문장입니다." in body
    assert "00:00:00,000 --> 00:00:02,0" in body  # start at 0, end ≈ audio length


def test_cues_tile_the_clip_without_gaps_or_overrun():
    """자막은 클립을 빈틈없이 덮고, 오디오 길이를 넘지 않아야 한다 (싱크 100%)."""
    long_line = (
        "마스터 프롬프트를 붙여넣고 가사를 입력해서 전송하면, 스토리를 만들어 줍니다. "
        "마음에 들면 확인이라고 입력하세요. 그러면 등장인물과 장소, 장면별 이미지 "
        "프롬프트까지 한 번에 정리해 줍니다."
    )
    duration = 14.0
    cues = caption_cues(long_line, duration)

    assert len(cues) > 1, "긴 대사는 여러 자막으로 나뉘어야 합니다"
    assert cues[0][0] == pytest.approx(0.0)
    assert cues[-1][1] == pytest.approx(duration)
    for (_, prev_end, _), (next_start, _, _) in zip(cues, cues[1:]):
        assert next_start == pytest.approx(prev_end), "자막 사이에 빈틈이 있습니다"
    for _, _, text in cues:
        assert len(text) <= MAX_CHARS_PER_CUE


def test_video_has_a_subtitle_band_below_the_artwork(tmp_path: Path):
    """자막이 그림/빨간 원을 가리지 않도록 아래쪽 전용 영역이 있어야 한다."""
    img = _make_test_image(tmp_path / "scene.png")
    wav = _make_test_wav(tmp_path / "scene.wav", seconds=1.0)

    out_path = tmp_path / "final.mp4"
    render_project_video(
        scenes=[SceneAsset(img, wav, "자막 전용 영역 확인용 문장입니다.")],
        out_path=out_path,
        work_dir=tmp_path / "_work",
    )

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0:s=x", str(out_path)],
        capture_output=True, text=True, check=True,
    )
    assert probe.stdout.strip() == f"1280x{OUTPUT_H}"


def test_split_caption_keeps_every_word():
    line = "첫 번째 문장입니다. 두 번째 문장은 조금 더 길게 이어집니다. 세 번째 문장으로 마무리합니다."
    chunks = split_caption(line)
    rejoined = " ".join(chunks).replace("  ", " ")
    for word in line.replace(".", "").split():
        assert word in rejoined


def test_subtitles_are_actually_burned_into_the_frames(tmp_path: Path):
    """A frame rendered with a caption must differ from one rendered without."""
    img = _make_test_image(tmp_path / "scene.png", (20, 20, 40))
    wav = _make_test_wav(tmp_path / "scene.wav", seconds=1.0)

    with_subs = tmp_path / "with_subs.mp4"
    render_project_video(
        scenes=[SceneAsset(img, wav, "한글 자막이 실제로 그려졌는지 확인합니다.")],
        out_path=with_subs,
        work_dir=tmp_path / "_work_subs",
        burn_subtitles=True,
    )

    without_subs = tmp_path / "without_subs.mp4"
    render_project_video(
        scenes=[SceneAsset(img, wav, "한글 자막이 실제로 그려졌는지 확인합니다.")],
        out_path=without_subs,
        work_dir=tmp_path / "_work_plain",
        burn_subtitles=False,
    )

    frame_a = _extract_frame(with_subs, tmp_path / "a.png")
    frame_b = _extract_frame(without_subs, tmp_path / "b.png")

    assert frame_a.read_bytes() != frame_b.read_bytes(), "자막이 프레임에 그려지지 않았습니다"


def test_find_korean_font_returns_an_existing_file():
    font = find_korean_font()
    assert font.exists()


def test_wrap_caption_breaks_long_korean_lines():
    long_text = "이 문장은 자막 한 줄에 담기에는 지나치게 길기 때문에 두 줄로 나뉘어야 정상입니다"
    wrapped = wrap_caption(long_text)
    assert "\n" in wrapped
    assert all(len(line) <= 45 for line in wrapped.split("\n"))


def test_srt_timestamp_format():
    assert srt_timestamp(0) == "00:00:00,000"
    assert srt_timestamp(61.5) == "00:01:01,500"
    assert srt_timestamp(3661.25) == "01:01:01,250"
