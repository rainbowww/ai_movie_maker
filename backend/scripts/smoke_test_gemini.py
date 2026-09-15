"""Manual smoke test for the Gemini integration — NOT part of the automated
test suite (it needs a real GEMINI_API_KEY and network access, neither of
which the sandbox that built this repo had). Run this yourself once you've
set GEMINI_API_KEY in backend/.env, to confirm both calls actually work
end-to-end before generating a whole project:

    cd backend
    pip install -r requirements.txt
    cp .env.example .env   # then edit .env and paste your key
    python -m scripts.smoke_test_gemini
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.services.gemini_image import generate_image  # noqa: E402
from app.services.gemini_tts import generate_speech  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.has_gemini_key:
        print("[smoke] GEMINI_API_KEY가 설정되지 않았습니다. backend/.env를 확인하세요.")
        raise SystemExit(1)

    out_dir = Path("storage/_smoke_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[smoke] 이미지 생성 시도 중 (gemini_image_model=%s)…" % settings.gemini_image_model)
    img_path = generate_image(
        settings,
        "Flat vector illustration of a friendly presenter character waving, "
        "warm gradient background, 16:9.",
        out_dir / "test_image.png",
    )
    print(f"[smoke] 이미지 생성 성공 -> {img_path} ({img_path.stat().st_size} bytes)")

    print("[smoke] TTS 생성 시도 중 (gemini_tts_model=%s, voice=Kore)…" % settings.gemini_tts_model)
    audio_path = generate_speech(
        settings,
        "안녕하세요, 이것은 음성 생성 테스트입니다.",
        "Kore",
        out_dir / "test_audio.wav",
    )
    print(f"[smoke] 오디오 생성 성공 -> {audio_path} ({audio_path.stat().st_size} bytes)")
    print("[smoke] 완료. 두 파일을 재생해 실제 품질을 직접 확인하세요.")


if __name__ == "__main__":
    main()
