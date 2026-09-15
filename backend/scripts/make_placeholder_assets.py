"""Fill a project with locally drawn placeholder images and silent audio —
no Gemini calls, no cost.

This exists so the whole pipeline (cue circles → subtitle burn-in → scene
clips → concatenated mp4 + .srt) can be exercised and reviewed for free
before spending anything on real generation. Once the result looks right,
swap in real assets with "전체 생성" and render again.

    cd backend
    python -m scripts.make_placeholder_assets demo-2host
    python -m scripts.make_placeholder_assets demo-solo --with-audio
"""
from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.deps import get_store  # noqa: E402
from app.services.mockups import render_mockup  # noqa: E402
from app.services.overlay import apply_cue_circle  # noqa: E402
from app.services.subtitles import find_korean_font  # noqa: E402

WIDTH, HEIGHT = 1280, 720
CHAPTER_COLORS = {
    "오프닝": (26, 29, 41),
    "Treblo로 작곡하기": (20, 30, 48),
    "Claude로 스토리 만들기": (44, 30, 20),
    "Google Flow로 장면 만들기": (20, 40, 44),
    "CapCut으로 완성하기": (40, 22, 40),
    "마무리": (32, 26, 52),
}
SECONDS_PER_PLACEHOLDER_LINE = 0.18  # rough read-aloud pace for silent stand-ins


def draw_placeholder(path: Path, index: int, chapter: str, caption: str) -> Path:
    bg = CHAPTER_COLORS.get(chapter, (26, 29, 41))
    img = Image.new("RGB", (WIDTH, HEIGHT), bg)
    draw = ImageDraw.Draw(img)

    font_path = find_korean_font()
    try:
        big = ImageFont.truetype(str(font_path), 54)
        small = ImageFont.truetype(str(font_path), 26)
    except OSError:  # .ttc collections need an index
        big = ImageFont.truetype(str(font_path), 54, index=0)
        small = ImageFont.truetype(str(font_path), 26, index=0)

    # mock browser window chrome so the frame reads as a screen mockup
    draw.rounded_rectangle([60, 70, WIDTH - 60, HEIGHT - 150], radius=18,
                           fill=(tuple(min(255, c + 12) for c in bg)), outline=(52, 59, 82), width=2)
    for i, dot in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        draw.ellipse([92 + i * 22, 96, 104 + i * 22, 108], fill=dot)

    draw.text((100, 150), f"#{index + 1}", font=big, fill=(255, 180, 84))
    draw.text((100, 225), chapter, font=small, fill=(152, 160, 184))
    draw.text((100, 275), "PLACEHOLDER — 실제 생성 전 미리보기용", font=small, fill=(152, 160, 184))

    preview = caption[:38] + ("…" if len(caption) > 38 else "")
    draw.text((100, 340), preview, font=small, fill=(238, 240, 247))

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")
    return path


def write_silent_wav(path: Path, seconds: float, rate: int = 24000) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * int(seconds * rate))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="프로젝트에 무료 플레이스홀더 자산을 채웁니다.")
    parser.add_argument("project_id")
    parser.add_argument("--with-audio", action="store_true",
                        help="대사 길이에 비례하는 무음 오디오도 만들어 자막 타이밍까지 확인")
    args = parser.parse_args()

    settings = get_settings()
    store = get_store()
    project = store.get(args.project_id)
    if not project:
        raise SystemExit(f"프로젝트를 찾을 수 없습니다: {args.project_id}")

    scenes_dir = project.scenes_dir(settings.storage_dir)

    for scene in sorted(project.scenes, key=lambda s: s.order):
        raw = scenes_dir / f"{scene.id}_placeholder_raw.png"
        final = scenes_dir / f"{scene.id}.png"
        if scene.visual_key:
            render_mockup(scene.visual_key, raw)
        else:
            draw_placeholder(raw, scene.order, scene.chapter, scene.caption)

        if scene.cue.enabled:
            apply_cue_circle(raw, final, scene.cue.x, scene.cue.y, scene.cue.r)
        else:
            final.write_bytes(raw.read_bytes())
        scene.image_path = str(final.relative_to(settings.storage_dir))

        if args.with_audio:
            seconds = max(2.0, len(scene.caption) * SECONDS_PER_PLACEHOLDER_LINE)
            wav = write_silent_wav(scenes_dir / f"{scene.id}.wav", seconds)
            scene.audio_path = str(wav.relative_to(settings.storage_dir))
            scene.audio_seconds = seconds

    store.save(project)
    print(f"[placeholder] {project.id}: 장면 {len(project.scenes)}개에 플레이스홀더 자산을 채웠습니다.")
    print("[placeholder] 이제 '영상 렌더링'을 눌러 전체 흐름을 비용 없이 확인하세요.")


if __name__ == "__main__":
    main()
