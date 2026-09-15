"""The caption is what you read; spoken_text is what the engine says.

Every case here exists because espeak-ng gets the raw form wrong — the
defects are reproducible with `espeak-ng -v ko+m3 -x -q`, and
test_no_english_voice_switch / test_no_digit_breaks assert against that
phoneme output directly rather than trusting the table below.
"""
from __future__ import annotations

import shutil
import subprocess

import pytest

from app.models import Scene
from app.services.speech_text import (
    native_number,
    sino_number,
    to_speech_text,
    unknown_latin_tokens,
)


@pytest.mark.parametrize(
    "number,expected",
    [
        (0, "영"), (1, "일"), (10, "십"), (11, "십일"), (20, "이십"),
        (90, "구십"), (100, "백"), (101, "백일"), (1000, "천"),
        (1234, "천이백삼십사"), (10000, "만"), (10001, "만일"),
        (110000, "십일만"), (100000000, "억"),
    ],
)
def test_sino_number(number, expected):
    assert sino_number(number) == expected


@pytest.mark.parametrize(
    "number,expected",
    [(1, "한"), (3, "세"), (10, "열"), (11, "열한"), (20, "스무"), (21, "스물한"), (99, "아흔아홉")],
)
def test_native_number(number, expected):
    assert native_number(number) == expected


def test_native_number_falls_back_to_sino_above_99():
    # 고유어 수사 stops being idiomatic past 99 whatever the counter.
    assert native_number(100) == sino_number(100)


@pytest.mark.parametrize(
    "caption,expected",
    [
        ("AI 영상", "에이아이 영상"),
        ("100퍼센트 한국어", "백 퍼센트 한국어"),
        ("90초 안에", "구십 초 안에"),
        ("0원으로", "영 원으로"),
        # 개 takes 고유어, 분 (minutes) takes 한자어.
        ("3개만 고르세요", "세 개만 고르세요"),
        ("30분 걸립니다", "삼십 분 걸립니다"),
        ("1.5배 빠르게", "일 점 오 배 빠르게"),
        ("CapCut에서 Export를 누르세요", "캡컷에서 익스포트를 누르세요"),
        ("2025년 9월 15일", "이천이십오 년 구 월 십오 일"),
    ],
)
def test_to_speech_text(caption, expected):
    assert to_speech_text(caption) == expected


def test_unknown_acronym_is_spelled_out_in_hangul():
    # Not in the dictionary, but spelling it out keeps the Korean voice.
    assert to_speech_text("MZ 세대") == "엠지 세대"


def test_unknown_word_is_reported_not_silently_accepted():
    to_speech_text("Zyxwquux 툴")
    assert "Zyxwquux" in unknown_latin_tokens()


def test_empty_caption_is_left_alone():
    assert to_speech_text("") == ""
    assert to_speech_text("   ") == "   "


def test_trailing_text_after_a_counter_survives():
    assert to_speech_text("5개입니다") == "다섯 개입니다"


def test_scene_override_wins():
    scene = Scene(order=0, caption="AI 영상", speech_text="에이 아이 영상")
    assert scene.spoken_text() == "에이 아이 영상"


def test_scene_normalizes_by_default():
    assert Scene(order=0, caption="AI 영상").spoken_text() == "에이아이 영상"


def test_scene_skips_normalization_for_a_neural_engine():
    # Gemini has neither defect, and 에이아이 only makes it read stiffly.
    assert Scene(order=0, caption="AI 영상").spoken_text(normalize=False) == "AI 영상"


def _phonemes(text: str) -> str:
    return subprocess.run(
        ["espeak-ng", "-v", "ko+m3", "-x", "-q", text],
        capture_output=True, text=True, check=True,
    ).stdout


needs_espeak = pytest.mark.skipif(
    not shutil.which("espeak-ng"), reason="espeak-ng이 없는 환경"
)


@needs_espeak
def test_no_english_voice_switch():
    """"(en)" in the phoneme stream means the narrator's voice changed."""
    caption = "AI 영상에서 CapCut을 씁니다"
    assert "(en)" in _phonemes(caption)  # the defect is real
    assert "(en)" not in _phonemes(to_speech_text(caption))


@needs_espeak
def test_no_digit_breaks():
    """"_!" is a break; espeak inserts one after every digit place."""
    caption = "90초 만에 100퍼센트"
    assert "_!" in _phonemes(caption)  # the defect is real
    assert "_!" not in _phonemes(to_speech_text(caption))
