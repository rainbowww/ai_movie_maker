"""Generate Korean narration for every scene with the offline espeak-ng engine.

This is the zero-cost, zero-network path: it needs no API key and no
internet, so a full narrated cut can be produced and reviewed immediately.
The voice is formant-synthesised and sounds robotic — it is for checking
pacing, subtitle sync and structure, not for publishing. Replace it with
Gemini TTS (전체 생성) once a key is configured.

    cd backend
    sudo apt install espeak-ng          # 한 번만
    python -m scripts.make_local_tts demo-solo
    python -m scripts.make_local_tts demo-solo --speed 140
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

DEFAULT_SPEED = 150  # words per minute; Korean reads better a little slower


def synthesize(text: str, out_path: Path, speed: int, voice: str = "ko") -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["espeak-ng", "-v", voice, "-s", str(speed), "-w", str(out_path), text],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"espeak-ng 실패: {result.stderr[-500:]}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="espeak-ng으로 장면별 한국어 내레이션 생성")
    parser.add_argument("project_id")
    parser.add_argument("--speed", type=int, default=DEFAULT_SPEED)
    parser.add_argument("--voice", default="ko")
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
        wav = synthesize(scene.caption, scenes_dir / f"{scene.id}.wav", args.speed, args.voice)
        scene.audio_path = str(wav.relative_to(settings.storage_dir))
        made += 1

    store.save(project)
    print(f"[local-tts] {project.id}: 대사 {made}개 음성 생성 완료 (espeak-ng, {args.speed}wpm)")
    print("[local-tts] 이제 '영상 렌더링'을 실행하면 음성이 들어간 완성본이 나옵니다.")


if __name__ == "__main__":
    main()
