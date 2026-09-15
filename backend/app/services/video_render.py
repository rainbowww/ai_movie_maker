"""Assemble per-scene images + narration audio + Korean subtitles into a
single narrated video using the system `ffmpeg`/`ffprobe` binaries.

No AI calls and no network here — this stage only needs a scene's image,
its (optional) audio, and its caption text, so it is fully covered by
backend/tests/test_render.py using synthetic fixtures.

Layout: the artwork keeps its full 16:9 frame and the video is padded below
it into a dedicated subtitle band. Captions therefore never cover the
artwork or a red click-cue circle, however low in the frame that cue sits.

Sync: each scene clip is exactly as long as its narration audio, and its
captions tile that clip end to end, so voice and text cannot drift apart.
The sidecar .srt written next to the mp4 uses those same measured timings.

A scene without audio yet is held on screen for FALLBACK_SECONDS with
silence, so a project can still be previewed as a rough cut before every
voice line has been generated.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .subtitles import (
    SubtitleError,
    build_subtitles_filter,
    caption_cues,
    find_korean_font,
    font_family_name,
    write_ass,
    write_srt,
)

FALLBACK_SECONDS = 3.0
FPS = 30
CONTENT_W = 1280
CONTENT_H = 720
SUBTITLE_BAND_H = 96  # dedicated caption strip below the artwork
OUTPUT_H = CONTENT_H + SUBTITLE_BAND_H  # 816 — divisible by 16, H.264-friendly
BAND_COLOR = "0x12141C"


class RenderError(RuntimeError):
    pass


@dataclass
class SceneAsset:
    image_path: Path
    audio_path: Optional[Path] = None
    caption: str = ""


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RenderError(f"ffmpeg 실패 (exit {result.returncode}): {result.stderr[-4000:]}")


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError as e:
        raise RenderError(f"ffprobe로 길이를 읽을 수 없습니다: {path} ({result.stderr[-500:]})") from e


def _layout_filter(with_band: bool) -> str:
    """Fit the artwork into the content area, then pad out the caption band."""
    height = OUTPUT_H if with_band else CONTENT_H
    return (
        f"scale={CONTENT_W}:{CONTENT_H}:force_original_aspect_ratio=decrease,"
        f"pad={CONTENT_W}:{height}:(ow-iw)/2:0:color={BAND_COLOR}"
    )


def render_scene_clip(
    scene: SceneAsset,
    out_path: Path,
    burn_subtitles: bool = True,
    font_path: Optional[Path] = None,
) -> float:
    """Render one scene to an MP4 clip. Returns the clip's duration in seconds."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    has_audio = scene.audio_path is not None and scene.audio_path.exists()
    duration = probe_duration(scene.audio_path) if has_audio else FALLBACK_SECONDS

    captioned = burn_subtitles and bool(scene.caption.strip())
    filters = [_layout_filter(with_band=captioned)]
    if captioned:
        font = font_path or find_korean_font()
        ass_path = out_path.with_suffix(".ass")
        write_ass(
            caption_cues(scene.caption, duration),
            ass_path,
            font_name=font_family_name(font),
            play_res_x=CONTENT_W,
            play_res_y=OUTPUT_H,
        )
        filters.append(build_subtitles_filter(ass_path, font))

    vf = ",".join(filters)

    if has_audio:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(FPS), "-i", str(scene.image_path),
            "-i", str(scene.audio_path),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest",
            "-vf", vf,
            str(out_path),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(FPS), "-t", str(FALLBACK_SECONDS), "-i", str(scene.image_path),
            "-f", "lavfi", "-t", str(FALLBACK_SECONDS), "-i", "anullsrc=r=24000:cl=mono",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-vf", vf,
            str(out_path),
        ]
    _run(cmd)
    return duration


def concat_clips(clip_paths: list[Path], out_path: Path) -> None:
    if not clip_paths:
        raise RenderError("합칠 클립이 없습니다.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = out_path.parent / f"_{out_path.stem}_concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in clip_paths), encoding="utf-8"
    )
    try:
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out_path)])
    finally:
        list_file.unlink(missing_ok=True)


def render_project_video(
    scenes: list[SceneAsset],
    out_path: Path,
    work_dir: Path,
    burn_subtitles: bool = True,
) -> float:
    """Render every scene, concatenate them, and write a sidecar .srt.

    Returns the total duration in seconds.
    """
    work_dir.mkdir(parents=True, exist_ok=True)

    font_path: Optional[Path] = None
    if burn_subtitles:
        try:
            font_path = find_korean_font()
        except SubtitleError as e:
            raise RenderError(str(e)) from e

    clips: list[Path] = []
    all_cues: list[tuple[float, float, str]] = []
    elapsed = 0.0

    for i, scene in enumerate(scenes):
        clip_path = work_dir / f"clip_{i:03d}.mp4"
        duration = render_scene_clip(scene, clip_path, burn_subtitles, font_path)
        clips.append(clip_path)
        all_cues.extend(caption_cues(scene.caption, duration, start=elapsed))
        elapsed += duration

    concat_clips(clips, out_path)

    if all_cues:
        write_srt(all_cues, out_path.with_suffix(".srt"))

    return elapsed
