"""Build the finished cut with Gemini imagery and voice, in one command.

The paid twin of make_free_cut: same project, same render step, but the
screens and narration come from Gemini instead of Pillow and espeak-ng.

    cd backend
    python -m scripts.make_gemini_cut demo-solo --dry-run   # 호출 수와 비용만
    python -m scripts.make_gemini_cut demo-solo             # 실제 생성 + 렌더
    python -m scripts.make_gemini_cut demo-solo --voice-only # 화면은 그대로 두고 음성만

Needs GEMINI_API_KEY in backend/.env. Every scene is saved the moment it
succeeds, so an interrupted run resumes where it stopped and never pays
twice for the same scene — re-run the same command.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.deps import get_store  # noqa: E402
from app.services.gemini_image import GeminiImageError, generate_image  # noqa: E402
from app.services.gemini_tts import GeminiTTSError, generate_speech  # noqa: E402
from app.services.overlay import apply_cue_circle  # noqa: E402
from app.services.video_render import (  # noqa: E402
    SceneAsset,
    parse_timecode_span,
    render_project_video,
)

# Rough published rates, for an estimate only — verify current pricing at
# https://ai.google.dev/pricing before relying on these numbers.
EST_USD_PER_IMAGE = 0.04
EST_USD_PER_1K_CHARS = 0.016


def estimate(project, do_images: bool, do_voice: bool) -> tuple[int, int, float]:
    images = sum(1 for s in project.scenes if do_images and s.image_prompt.strip())
    chars = sum(len(s.caption) for s in project.scenes if do_voice and s.caption.strip())
    usd = images * EST_USD_PER_IMAGE + (chars / 1000) * EST_USD_PER_1K_CHARS
    return images, chars, usd


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini로 완성본을 한 번에 만들기")
    parser.add_argument("project_id")
    parser.add_argument("--dry-run", action="store_true", help="호출 수와 예상 비용만 출력")
    parser.add_argument("--voice-only", action="store_true", help="이미지는 건드리지 않고 음성만")
    parser.add_argument("--images-only", action="store_true", help="음성은 건드리지 않고 이미지만")
    parser.add_argument("--force", action="store_true", help="이미 있는 자산도 다시 생성")
    parser.add_argument("--no-render", action="store_true", help="생성만 하고 렌더는 건너뜀")
    args = parser.parse_args()

    settings = get_settings()
    store = get_store()
    project = store.get(args.project_id)
    if not project:
        raise SystemExit(f"프로젝트를 찾을 수 없습니다: {args.project_id}")

    do_images = not args.voice_only
    do_voice = not args.images_only
    images, chars, usd = estimate(project, do_images, do_voice)

    print(f"프로젝트: {project.title}")
    print(f"  이미지 {images}장 · 음성 {chars:,}자 · 예상 비용 약 ${usd:.2f}")
    print("  (추정치입니다. 최신 단가는 https://ai.google.dev/pricing 에서 확인하세요)")

    if args.dry_run:
        print("\n--dry-run 이므로 아무것도 호출하지 않았습니다.")
        return

    if not settings.has_gemini_key:
        raise SystemExit(
            "\nGEMINI_API_KEY가 없습니다.\n"
            "  1) https://aistudio.google.com/apikey 에서 발급\n"
            "  2) backend/.env 에 GEMINI_API_KEY=... 입력\n"
            "  3) 다시 실행\n"
            "키 없이 결과를 먼저 보려면: python -m scripts.make_free_cut " + args.project_id
        )

    scenes_dir = project.scenes_dir(settings.storage_dir)
    started = time.time()
    made_images = made_voice = 0
    failures: list[str] = []

    total = len(project.scenes)
    for scene in sorted(project.scenes, key=lambda s: s.order):
        label = f"[{scene.order + 1:2d}/{total}]"

        if do_images and scene.image_prompt.strip() and (args.force or not scene.image_path):
            raw = scenes_dir / f"{scene.id}_raw.png"
            final = scenes_dir / f"{scene.id}.png"
            try:
                generate_image(settings, scene.image_prompt, raw)
                if scene.cue.enabled:
                    apply_cue_circle(raw, final, scene.cue.x, scene.cue.y, scene.cue.r)
                else:
                    final.write_bytes(raw.read_bytes())
                raw.unlink(missing_ok=True)
                scene.image_path = str(final.relative_to(settings.storage_dir))
                made_images += 1
                print(f"{label} 이미지 완료")
            except GeminiImageError as e:
                failures.append(f"장면 {scene.order + 1} 이미지: {e}")
                print(f"{label} 이미지 실패 — {e}")

        if do_voice and scene.caption.strip() and (args.force or not scene.audio_path):
            wav = scenes_dir / f"{scene.id}.wav"
            voice = project.voice_m if scene.speaker == "m" else project.voice_f
            try:
                generate_speech(settings, scene.spoken_text(normalize=False), voice, wav)
                scene.audio_path = str(wav.relative_to(settings.storage_dir))
                made_voice += 1
                print(f"{label} 음성 완료 ({voice})")
            except GeminiTTSError as e:
                failures.append(f"장면 {scene.order + 1} 음성: {e}")
                print(f"{label} 음성 실패 — {e}")

        # Save after every scene: an interrupted run resumes instead of
        # paying for the same scenes again.
        store.save(project)

    print(f"\n생성 완료: 이미지 {made_images}장 · 음성 {made_voice}개 · {time.time() - started:.0f}초")
    if failures:
        print(f"실패 {len(failures)}건:")
        for f in failures[:10]:
            print(f"  - {f}")
        print("같은 명령을 다시 실행하면 실패한 장면만 이어서 시도합니다.")

    if args.no_render:
        return

    missing = [s.order + 1 for s in project.scenes if not s.image_path]
    if missing:
        print(f"\n이미지가 없는 장면이 있어 렌더를 건너뜁니다: {missing}")
        return

    print("\n영상 합성 중…")
    scenes = [
        SceneAsset(
            image_path=settings.storage_dir / s.image_path,  # type: ignore[arg-type]
            audio_path=(settings.storage_dir / s.audio_path) if s.audio_path else None,
            caption=s.caption,
            hold_seconds=s.hold_seconds,
            target_seconds=parse_timecode_span(s.source_timecode),
        )
        for s in sorted(project.scenes, key=lambda s: s.order)
    ]
    out_path = project.project_dir(settings.storage_dir) / "final.mp4"
    duration = render_project_video(
        scenes, out_path, project.project_dir(settings.storage_dir) / "_render_work"
    )
    project.video_path = str(out_path.relative_to(settings.storage_dir))
    store.save(project)

    mins, secs = divmod(int(duration), 60)
    print(f"\n완성: {out_path}")
    print(f"  길이 {mins}분 {secs}초 · 자막 파일 {out_path.with_suffix('.srt')}")


if __name__ == "__main__":
    main()
