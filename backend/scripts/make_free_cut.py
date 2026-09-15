"""Build a complete narrated cut for free, in one command.

Draws every scene, speaks every line with the offline engine, burns the
Korean subtitles in, and writes the mp4 — no API key, no credits, no
server, no network. The point is to see the whole thing before deciding
what is worth paying to improve.

    cd backend
    python -m scripts.make_free_cut demo-solo
    python -m scripts.make_free_cut demo-2host --open-dir

What it does NOT do is replace the paid path: the drawn mockups are
schematic and the voice is formant-synthesised. Once a GEMINI_API_KEY
exists, "전체 생성" swaps in real imagery and a neural voice, and the same
render step runs unchanged.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.deps import get_store  # noqa: E402
from app.services import edge_voice  # noqa: E402
from app.services.mockups import render_mockup  # noqa: E402
from app.services.overlay import apply_cue_circle  # noqa: E402
from app.services.video_render import (  # noqa: E402
    SceneAsset,
    parse_timecode_span,
    render_project_video,
)
from scripts.make_local_tts import (  # noqa: E402
    DEFAULT_AMPLITUDE,
    DEFAULT_SPEED,
    DEFAULT_WORD_GAP,
    PITCH_BY_SPEAKER,
    VOICE_BY_SPEAKER,
    synthesize,
)


def build_images(project, storage_root: Path) -> int:
    scenes_dir = project.scenes_dir(storage_root)
    made = 0
    for scene in sorted(project.scenes, key=lambda s: s.order):
        if not scene.visual_key:
            continue
        raw = scenes_dir / f"{scene.id}_raw.png"
        final = scenes_dir / f"{scene.id}.png"
        render_mockup(scene.visual_key, raw)
        if scene.cue.enabled:
            apply_cue_circle(raw, final, scene.cue.x, scene.cue.y, scene.cue.r)
        else:
            final.write_bytes(raw.read_bytes())
        raw.unlink(missing_ok=True)
        scene.image_path = str(final.relative_to(storage_root))
        made += 1
    return made


def resolve_engine(requested: str) -> str:
    """Pick the voice engine, and say why when the good one is unavailable.

    "auto" prefers the neural voices and drops to espeak-ng rather than
    failing — but it prints the reason, because a run that silently sounds
    worse than the last one is the kind of thing nobody notices until the
    video is already cut.
    """
    if requested == "espeak":
        if not shutil.which("espeak-ng"):
            raise SystemExit("espeak-ng이 없습니다: sudo apt install espeak-ng")
        return "espeak"

    ok, reason = edge_voice.probe()
    if requested == "edge":
        if not ok:
            raise SystemExit(
                f"신경망 음성(edge-tts)을 쓸 수 없습니다 — {reason}\n"
                "  · 이 컨테이너는 조직 네트워크 정책으로 막혀 있습니다.\n"
                "  · 로컬 PC나 정책이 허용된 환경에서 같은 명령을 실행하면 동작합니다.\n"
                "  · 지금 결과부터 보려면: --engine espeak"
            )
        return "edge"

    if ok:
        print(f"      신경망 음성 사용 (edge-tts · {reason})")
        return "edge"
    if not shutil.which("espeak-ng"):
        raise SystemExit(f"신경망 음성도 espeak-ng도 쓸 수 없습니다 — {reason}")
    print(f"      신경망 음성 불가 → espeak-ng으로 대체 ({reason})")
    return "espeak"


def build_voices(project, storage_root: Path, speed: int, engine: str) -> int:
    scenes_dir = project.scenes_dir(storage_root)
    made = 0
    for scene in sorted(project.scenes, key=lambda s: s.order):
        if not scene.caption.strip():
            scene.audio_path = None
            continue
        wav = scenes_dir / f"{scene.id}.wav"
        if engine == "edge":
            # A neural engine reads "AI" and "100%" correctly on its own;
            # the espeak rewrite would only make it read stiffly.
            edge_voice.synthesize(
                scene.spoken_text(normalize=False), wav,
                voice=edge_voice.VOICE_BY_SPEAKER.get(
                    scene.speaker, edge_voice.VOICE_BY_SPEAKER["m"]
                ),
            )
        else:
            synthesize(
                scene.spoken_text(), wav,
                voice=VOICE_BY_SPEAKER.get(scene.speaker, VOICE_BY_SPEAKER["m"]),
                speed=speed,
                pitch=PITCH_BY_SPEAKER.get(scene.speaker, PITCH_BY_SPEAKER["m"]),
                amplitude=DEFAULT_AMPLITUDE, word_gap=DEFAULT_WORD_GAP, master=True,
            )
        scene.audio_path = str(wav.relative_to(storage_root))
        made += 1
    return made


def main() -> None:
    parser = argparse.ArgumentParser(description="비용 0원으로 완성본 한 번에 만들기")
    parser.add_argument("project_id")
    parser.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser.add_argument(
        "--engine", choices=("auto", "edge", "espeak"), default="auto",
        help="auto: 신경망(edge-tts) 우선, 안 되면 espeak-ng",
    )
    parser.add_argument("--no-voice", action="store_true", help="음성 없이 화면만")
    parser.add_argument("--no-subtitles", action="store_true")
    parser.add_argument("--match-source-timing", action="store_true", default=True)
    args = parser.parse_args()

    settings = get_settings()
    store = get_store()
    project = store.get(args.project_id)
    if not project:
        raise SystemExit(
            f"프로젝트를 찾을 수 없습니다: {args.project_id}\n"
            "먼저 시드를 만드세요: python -m scripts.seed_solo_project"
        )

    started = time.time()
    print(f"[1/3] 화면 그리는 중… ({len(project.scenes)}장면)")
    images = build_images(project, settings.storage_dir)

    engine = ""
    if args.no_voice:
        voices = 0
        for scene in project.scenes:
            scene.audio_path = None
        print("[2/3] 음성 건너뜀 (--no-voice)")
    else:
        print("[2/3] 한국어 음성 생성 중…")
        engine = resolve_engine(args.engine)
        voices = build_voices(project, settings.storage_dir, args.speed, engine)

    store.save(project)

    print("[3/3] 영상 합성 중…")
    scenes = [
        SceneAsset(
            image_path=settings.storage_dir / scene.image_path,  # type: ignore[arg-type]
            audio_path=(settings.storage_dir / scene.audio_path) if scene.audio_path else None,
            caption=scene.caption,
            hold_seconds=scene.hold_seconds,
            target_seconds=(
                parse_timecode_span(scene.source_timecode) if args.match_source_timing else None
            ),
        )
        for scene in sorted(project.scenes, key=lambda s: s.order)
    ]
    out_path = project.project_dir(settings.storage_dir) / "final.mp4"
    duration = render_project_video(
        scenes, out_path,
        project.project_dir(settings.storage_dir) / "_render_work",
        burn_subtitles=not args.no_subtitles,
    )

    project.video_path = str(out_path.relative_to(settings.storage_dir))
    store.save(project)

    mins, secs = divmod(int(duration), 60)
    print()
    print(f"완성: {out_path}")
    engine_label = {"edge": "신경망 edge-tts", "espeak": "espeak-ng"}.get(engine, "없음")
    print(f"  길이 {mins}분 {secs}초 · 화면 {images}개 · 음성 {voices}개({engine_label}) · 자막 {'번인' if not args.no_subtitles else '없음'}")
    print(f"  자막 파일: {out_path.with_suffix('.srt')}")
    print(f"  걸린 시간 {time.time() - started:.0f}초 · 비용 0원")


if __name__ == "__main__":
    main()
