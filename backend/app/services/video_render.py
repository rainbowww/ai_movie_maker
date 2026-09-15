"""Assemble per-scene images + narration audio into a single narrated video
using the system `ffmpeg`/`ffprobe` binaries via subprocess.

No AI calls and no network here — this stage only needs a scene's
image_path and (optionally) audio_path, so it is fully covered by
backend/tests/test_render.py using synthetic fixtures.

A scene without audio yet is held on screen for FALLBACK_SECONDS with
silence, so a project can still be previewed as a rough-cut video before
every voice line has been generated.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

FALLBACK_SECONDS = 3.0
FPS = 30
OUTPUT_SIZE = "1280:720"


class RenderError(RuntimeError):
    pass


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


def _scale_pad_filter() -> str:
    return f"scale={OUTPUT_SIZE}:force_original_aspect_ratio=decrease,pad={OUTPUT_SIZE}:(ow-iw)/2:(oh-ih)/2"


def render_scene_clip(image_path: Path, audio_path: Path | None, out_path: Path) -> float:
    """Render one scene to an MP4 clip. Returns the clip's duration in seconds."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if audio_path and audio_path.exists():
        duration = probe_duration(audio_path)
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(FPS), "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest",
            "-vf", _scale_pad_filter(),
            str(out_path),
        ]
    else:
        duration = FALLBACK_SECONDS
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(FPS), "-t", str(FALLBACK_SECONDS), "-i", str(image_path),
            "-f", "lavfi", "-t", str(FALLBACK_SECONDS), "-i", "anullsrc=r=24000:cl=mono",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-vf", _scale_pad_filter(),
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
    scene_assets: list[tuple[Path, Path | None]],
    out_path: Path,
    work_dir: Path,
) -> float:
    """scene_assets: ordered list of (image_path, audio_path_or_None).
    Renders each scene, concatenates them, and returns the total duration
    in seconds."""
    work_dir.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    total = 0.0
    for i, (image_path, audio_path) in enumerate(scene_assets):
        clip_path = work_dir / f"clip_{i:03d}.mp4"
        total += render_scene_clip(image_path, audio_path, clip_path)
        clips.append(clip_path)
    concat_clips(clips, out_path)
    return total
