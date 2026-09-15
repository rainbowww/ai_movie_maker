"""edge-tts is unreachable from the build container, so these tests mock it.

What is worth asserting offline is not "does Microsoft answer" — it is that
a blocked network produces a message someone can act on instead of a stack
trace, and that `auto` degrades to espeak-ng loudly rather than quietly.
"""
from __future__ import annotations

import asyncio

import pytest

from app.models import Scene
from app.services import edge_voice


@pytest.fixture(autouse=True)
def _clear_probe_cache():
    edge_voice.probe.cache_clear()
    yield
    edge_voice.probe.cache_clear()


@pytest.mark.parametrize(
    "exc,expected_fragment",
    [
        (RuntimeError("SkewAdjustmentError: No server date in headers."), "프록시가 연결을 거부"),
        (RuntimeError("HTTP 403 Forbidden"), "403"),
        (RuntimeError("SSLError: CERTIFICATE_VERIFY_FAILED"), "SSL_CERT_FILE"),
        (asyncio.TimeoutError(), "타임아웃"),
    ],
)
def test_failures_are_explained_not_dumped(exc, expected_fragment):
    assert expected_fragment in edge_voice._explain(exc)


def test_unrecognised_failure_still_names_the_exception():
    # Better a raw type name than a message that hides what happened.
    assert "ValueError" in edge_voice._explain(ValueError("뭔가 새로운 실패"))


def test_probe_reports_why_it_cannot_be_used(monkeypatch):
    monkeypatch.setattr(edge_voice, "is_installed", lambda: False)
    ok, reason = edge_voice.probe()
    assert ok is False
    assert "pip install edge-tts" in reason


def test_synthesize_rejects_empty_text():
    with pytest.raises(edge_voice.EdgeVoiceError):
        edge_voice.synthesize("   ", edge_voice.Path("/tmp/x.wav"), voice="ko-KR-SunHiNeural")


def test_korean_voices_are_distinct_per_speaker():
    voices = edge_voice.VOICE_BY_SPEAKER
    assert voices["m"] != voices["f"]
    assert all(v.startswith("ko-KR-") for v in voices.values())


def test_neural_engine_gets_the_caption_unnormalised():
    # The espeak rewrite exists for espeak's defects; a neural voice reads
    # "AI" and "100%" correctly and 에이아이 only makes it stiff.
    scene = Scene(order=0, caption="AI로 100% 완성")
    assert scene.spoken_text(normalize=False) == "AI로 100% 완성"
    assert scene.spoken_text() != scene.spoken_text(normalize=False)


# --- engine selection -------------------------------------------------------

from scripts.make_free_cut import resolve_engine  # noqa: E402


def test_explicit_edge_fails_loudly_with_a_way_out(monkeypatch):
    monkeypatch.setattr(edge_voice, "probe", lambda: (False, "정책 차단"))
    with pytest.raises(SystemExit) as excinfo:
        resolve_engine("edge")
    message = str(excinfo.value)
    assert "정책 차단" in message
    assert "--engine espeak" in message  # tells the user what to do instead


def test_auto_prefers_the_neural_engine(monkeypatch):
    monkeypatch.setattr(edge_voice, "probe", lambda: (True, "사용 가능 (음성 500종)"))
    assert resolve_engine("auto") == "edge"


def test_auto_falls_back_to_espeak(monkeypatch, capsys):
    monkeypatch.setattr(edge_voice, "probe", lambda: (False, "정책 차단"))
    monkeypatch.setattr("scripts.make_free_cut.shutil.which", lambda _: "/usr/bin/espeak-ng")
    assert resolve_engine("auto") == "espeak"
    # Quietly sounding worse than the last run is the failure mode to avoid.
    assert "정책 차단" in capsys.readouterr().out


def test_auto_gives_up_when_neither_engine_exists(monkeypatch):
    monkeypatch.setattr(edge_voice, "probe", lambda: (False, "정책 차단"))
    monkeypatch.setattr("scripts.make_free_cut.shutil.which", lambda _: None)
    with pytest.raises(SystemExit):
        resolve_engine("auto")
