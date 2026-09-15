"""The 27 drawn screens are all Korean labels, so the font has to be Hangul-capable.

This module used to hardcode /usr/share/fonts/truetype/nanum. It worked on
the Linux box it was written on and drew blank labels everywhere else,
because PIL's default bitmap font has no Hangul — and nothing failed, so
the only symptom was 27 screens of empty buttons.
"""
from __future__ import annotations

import pytest
from PIL import Image

from app.services import mockups
from app.services.subtitles import find_korean_font


def test_font_comes_from_the_shared_discovery():
    """Not a hardcoded directory — the same lookup the subtitles use."""
    regular, _ = mockups._font_paths()
    if regular is None:
        pytest.skip("이 환경에 한국어 폰트가 없습니다")
    assert regular == find_korean_font()


def test_the_drawing_font_can_render_hangul():
    font = mockups._font(24)
    left, _, right, _ = font.getbbox("한글")
    assert right - left > 0, "한글이 0폭으로 그려집니다 (한국어 폰트를 못 찾음)"


def test_bold_is_a_real_face_or_falls_back_cleanly():
    regular, bold = mockups._font_paths()
    if regular is None:
        pytest.skip("이 환경에 한국어 폰트가 없습니다")
    assert regular.exists()
    if bold is not None:
        assert bold.exists()
        assert bold != regular


@pytest.mark.parametrize("visual_key", sorted(mockups.RENDERERS))
def test_every_screen_draws_at_the_expected_size(visual_key, tmp_path):
    out = tmp_path / f"{visual_key}.png"
    mockups.render_mockup(visual_key, out)
    with Image.open(out) as img:
        assert img.size == (mockups.W, mockups.H)


def test_unknown_screen_name_draws_a_placeholder_instead_of_crashing(tmp_path):
    """A missing renderer must not stop a 38-scene render mid-way.

    The placeholder carries the key that was asked for, so the gap is
    obvious on screen rather than silently blank.
    """
    out = tmp_path / "unknown.png"
    mockups.render_mockup("존재하지_않는_화면", out)
    with Image.open(out) as img:
        assert img.size == (mockups.W, mockups.H)
