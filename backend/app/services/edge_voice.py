"""Free neural Korean narration through Microsoft Edge's read-aloud voices.

espeak-ng is a formant synthesiser and always sounds like one. `edge-tts`
talks to the same neural voices Edge uses for Read Aloud — ko-KR-InJoonNeural
and ko-KR-SunHiNeural are real Korean voices, they cost nothing, and they
need no API key.

What they do need is network access to Microsoft's speech host. The
container this repo was built in denies it at the egress proxy (403 on
CONNECT to speech.platform.bing.com), so this module cannot be exercised
end to end from there — `probe()` says so plainly instead of pretending.
Run it anywhere without that policy (a laptop, an environment whose
network policy allows the host) and it just works.

    python -m scripts.make_free_cut demo-solo --engine edge
    python -m scripts.make_free_cut demo-solo              # auto: edge, 안 되면 espeak

Unlike espeak this is a neural engine, so it reads "AI" and "100%"
correctly on its own — the caption goes in unnormalised
(`Scene.spoken_text(normalize=False)`).
"""
from __future__ import annotations

import asyncio
import subprocess
from functools import lru_cache
from pathlib import Path

# 한국어 신경망 음성. `edge-tts --list-voices | grep ko-KR` 로 최신 목록 확인.
VOICE_BY_SPEAKER = {"m": "ko-KR-InJoonNeural", "f": "ko-KR-SunHiNeural"}

# A narration read is a touch slower than the default; the neural voices
# need no pitch shaping to tell two speakers apart, they already differ.
DEFAULT_RATE = "-8%"
DEFAULT_VOLUME = "+0%"

OUTPUT_RATE = 24000

# Neural output does not get the espeak mastering chain. That chain exists
# to hide formant fizz — the 3.4kHz notch and the echo would only muddy a
# voice that is already clean. Level-matching is all that is wanted, and
# it matches make_local_tts so the two engines cut together.
MASTER_FILTER = "loudnorm=I=-16:TP=-1.5:LRA=11"


class EdgeVoiceError(RuntimeError):
    """edge-tts could not produce audio (usually the network policy)."""


def is_installed() -> bool:
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        return False
    return True


@lru_cache(maxsize=1)
def probe() -> tuple[bool, str]:
    """Can this machine actually reach the voices? Returns (ok, reason)."""
    if not is_installed():
        return False, "edge-tts가 설치되어 있지 않습니다: pip install edge-tts"
    try:
        import edge_tts

        async def _list() -> int:
            return len(await edge_tts.list_voices())

        count = asyncio.run(asyncio.wait_for(_list(), timeout=20))
    except Exception as exc:  # noqa: BLE001 - every failure means "not here"
        return False, _explain(exc)
    return True, f"사용 가능 (음성 {count}종)"


def _explain(exc: BaseException) -> str:
    text = f"{type(exc).__name__}: {exc}"
    if "CERTIFICATE_VERIFY_FAILED" in text or "SSLError" in text:
        return "TLS 검증 실패 — 프록시 CA를 신뢰하도록 SSL_CERT_FILE을 지정하세요."
    if "403" in text or "Forbidden" in text:
        return "네트워크 정책이 speech.platform.bing.com 접속을 막고 있습니다 (403)."
    if "SkewAdjustment" in text or "No server date" in text:
        # edge-tts syncs its clock off the response's Date header. A proxy
        # that refuses the CONNECT answers without one, so this is what a
        # policy block looks like from inside the library.
        return "응답에 Date 헤더가 없습니다 — 프록시가 연결을 거부한 것으로 보입니다 (정책 차단)."
    if isinstance(exc, asyncio.TimeoutError) or "Timeout" in text:
        return "Microsoft 음성 호스트 응답 없음 (타임아웃)."
    return text


def synthesize(
    text: str,
    out_path: Path,
    *,
    voice: str,
    rate: str = DEFAULT_RATE,
    volume: str = DEFAULT_VOLUME,
    master: bool = True,
) -> Path:
    """Speak `text` in a neural Korean voice and write a 24kHz mono wav."""
    if not text.strip():
        raise EdgeVoiceError("빈 문장은 합성할 수 없습니다.")
    if not is_installed():
        raise EdgeVoiceError("edge-tts가 설치되어 있지 않습니다: pip install edge-tts")

    import edge_tts

    out_path.parent.mkdir(parents=True, exist_ok=True)
    mp3_path = out_path.with_suffix(".edge.mp3")

    async def _run() -> None:
        await edge_tts.Communicate(text, voice, rate=rate, volume=volume).save(str(mp3_path))

    try:
        asyncio.run(_run())
    except Exception as exc:  # noqa: BLE001
        mp3_path.unlink(missing_ok=True)
        raise EdgeVoiceError(_explain(exc)) from exc

    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        mp3_path.unlink(missing_ok=True)
        raise EdgeVoiceError("edge-tts가 빈 파일을 남겼습니다 — 음성 이름을 확인하세요.")

    command = ["ffmpeg", "-y", "-i", str(mp3_path)]
    if master:
        command += ["-af", MASTER_FILTER]
    command += ["-ar", str(OUTPUT_RATE), "-ac", "1", str(out_path)]

    result = subprocess.run(command, capture_output=True, text=True)
    mp3_path.unlink(missing_ok=True)
    if result.returncode != 0 or not out_path.exists():
        raise EdgeVoiceError(f"ffmpeg 변환 실패: {result.stderr[-500:]}")
    return out_path
