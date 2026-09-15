"""Generate Korean narration for every scene with the offline espeak-ng engine.

This is the zero-cost, zero-network path: no API key, no internet, so a
full narrated cut can be produced and reviewed immediately.

espeak-ng is a formant synthesiser, so it will never sound human. What it
can do is sound *listenable*, and two things get it most of the way:

1. Voice settings tuned for narration rather than screen-reading — a lower
   pitch, a slower rate, and a small word gap so Korean particles do not
   run together.
2. A mastering pass in ffmpeg: roll off the rumble and the harsh top end,
   lift the chest frequencies, notch the 3-4kHz band where formant
   synthesis sounds most artificial, even out the level, and add a touch
   of room so the voice is not bone dry.

Replace it with a neural voice (전체 생성, Gemini TTS) when a key exists.

    cd backend
    sudo apt install espeak-ng          # 한 번만
    python -m scripts.make_local_tts demo-solo
    python -m scripts.make_local_tts demo-solo --raw      # 후처리 없이
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.deps import get_store  # noqa: E402

# Narration-tuned espeak settings. The stock voice sits too high and too
# fast to follow for ten minutes, so each speaker gets a variant and a
# pitch of its own — otherwise the two-host concept comes out in one voice.
VOICE_BY_SPEAKER = {"m": "ko+m3", "f": "ko+f3"}
PITCH_BY_SPEAKER = {"m": 30, "f": 62}
DEFAULT_SPEED = 142  # words per minute
DEFAULT_AMPLITUDE = 190
DEFAULT_WORD_GAP = 2  # 10ms units, inserted between words

# Mastering chain applied to espeak's raw output.
MASTER_FILTER = (
    "highpass=f=85,"  # drop rumble below the voice
    "lowpass=f=7200,"  # tame the synthetic fizz up top
    "equalizer=f=250:t=q:w=1.2:g=4,"  # add chest/body
    "equalizer=f=3400:t=q:w=2:g=-5,"  # notch the harshest formant band
    "acompressor=threshold=-18dB:ratio=3:attack=8:release=180,"
    "aecho=0.85:0.75:28:0.12,"  # a small room, not a hall
    "loudnorm=I=-16:TP=-1.5:LRA=11"
)
OUTPUT_RATE = 24000


def synthesize(text: str, out_path: Path, *, voice: str, speed: int, pitch: int,
               amplitude: int, word_gap: int, master: bool) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path = out_path.with_name(f"{out_path.stem}_raw.wav") if master else out_path

    result = subprocess.run(
        [
            "espeak-ng", "-v", voice,
            "-s", str(speed), "-p", str(pitch), "-a", str(amplitude), "-g", str(word_gap),
            "-w", str(raw_path), text,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not raw_path.exists():
        raise RuntimeError(f"espeak-ng 실패: {result.stderr[-500:]}")

    if not master:
        return out_path

    mastered = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_path),
            "-af", MASTER_FILTER,
            "-ar", str(OUTPUT_RATE), "-ac", "1",
            str(out_path),
        ],
        capture_output=True, text=True,
    )
    if mastered.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"ffmpeg 후처리 실패: {mastered.stderr[-800:]}")
    raw_path.unlink(missing_ok=True)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="espeak-ng으로 장면별 한국어 내레이션 생성")
    parser.add_argument("project_id")
    parser.add_argument("--voice-m", default=VOICE_BY_SPEAKER["m"])
    parser.add_argument("--voice-f", default=VOICE_BY_SPEAKER["f"])
    parser.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser.add_argument("--amplitude", type=int, default=DEFAULT_AMPLITUDE)
    parser.add_argument("--word-gap", type=int, default=DEFAULT_WORD_GAP)
    parser.add_argument("--raw", action="store_true", help="ffmpeg 마스터링 없이 원본 그대로")
    args = parser.parse_args()

    if not shutil.which("espeak-ng"):
        raise SystemExit("espeak-ng이 설치되어 있지 않습니다. `sudo apt install espeak-ng`")

    settings = get_settings()
    store = get_store()
    project = store.get(args.project_id)
    if not project:
        raise SystemExit(f"프로젝트를 찾을 수 없습니다: {args.project_id}")

    scenes_dir = project.scenes_dir(settings.storage_dir)
    made = 0

    for scene in sorted(project.scenes, key=lambda s: s.order):
        if not scene.caption.strip():
            scene.audio_path = None  # 무대사 장면은 hold_seconds로 유지
            scene.audio_seconds = None
            continue
        voice = args.voice_m if scene.speaker == "m" else args.voice_f
        pitch = PITCH_BY_SPEAKER.get(scene.speaker, PITCH_BY_SPEAKER["m"])
        wav = synthesize(
            scene.spoken_text(), scenes_dir / f"{scene.id}.wav",
            voice=voice, speed=args.speed, pitch=pitch,
            amplitude=args.amplitude, word_gap=args.word_gap, master=not args.raw,
        )
        scene.audio_path = str(wav.relative_to(settings.storage_dir))
        made += 1
        print(f"  [{scene.order + 1:2d}/{len(project.scenes)}] {scene.caption[:32]}…")

    store.save(project)
    mode = "원본" if args.raw else "마스터링 적용"
    voices = f"남 {args.voice_m} / 여 {args.voice_f}"
    print(f"[local-tts] {project.id}: 대사 {made}개 음성 생성 완료 ({voices}, {args.speed}wpm, {mode})")
    print("[local-tts] 이제 '영상 렌더링'을 실행하면 음성이 들어간 완성본이 나옵니다.")


if __name__ == "__main__":
    main()
