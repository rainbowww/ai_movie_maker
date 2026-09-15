"""A cue circle that runs off the canvas is an arc, and an arc points at nothing.

Targets near an edge are exactly the ones this happens to — a 생성 button at
y=600 of 720 with a 166px radius loses its bottom — so the fit is asserted
for every cue the two seeded projects actually use, not just in the abstract.
"""
from __future__ import annotations

import pytest
from PIL import Image

from app.services.overlay import (
    CUE_MARGIN_RATIO,
    CUE_MIN_RADIUS_RATIO,
    CUE_WIDTH_RATIO,
    apply_cue_circle,
    fit_circle,
)

W, H = 1280, 720


def _inset(w: int) -> float:
    return w * CUE_MARGIN_RATIO + max(3, int(w * CUE_WIDTH_RATIO)) / 2


def _assert_inside(cx: float, cy: float, radius: float, w: int = W, h: int = H) -> None:
    inset = _inset(w)
    assert cx - radius >= -0.01 and cy - radius >= -0.01
    assert cx + radius <= w + 0.01 and cy + radius <= h + 0.01
    # And not merely touching — the stroke has width.
    assert cx - radius >= inset - 0.01
    assert cy - radius >= inset - 0.01


def test_a_circle_that_already_fits_is_untouched():
    assert fit_circle(640, 360, 200, W, H) == (640, 360, 200)


def test_radius_shrinks_before_the_centre_moves():
    # The centre carries the meaning: it is what sits over the target.
    cx, cy, radius = fit_circle(640, 600, 166, W, H)
    assert (cx, cy) == (640, 600)
    assert radius < 166
    _assert_inside(cx, cy, radius)


def test_a_corner_target_still_gets_a_whole_circle():
    cx, cy, radius = fit_circle(8, 8, 200, W, H)
    assert radius >= W * CUE_MIN_RADIUS_RATIO * 0.99
    _assert_inside(cx, cy, radius)


def test_the_centre_moves_only_as_far_as_it_must():
    # Shrinking alone would leave it unreadably small, so it slides inward —
    # but no further than needed to fit the minimum radius.
    _, _, minimum = fit_circle(8, 8, 200, W, H)
    cx, cy, radius = fit_circle(8, 8, 200, W, H)
    assert cx <= minimum + _inset(W) + 0.01
    assert cy <= minimum + _inset(W) + 0.01


@pytest.mark.parametrize(
    "name,x,y,r",
    [
        ("treblo_prompt_box", 0.500, 0.389, 0.19),
        ("treblo_generate", 0.500, 0.761, 0.13),
        ("treblo_advanced_tab", 0.199, 0.153, 0.075),
        ("treblo_style_tags", 0.260, 0.374, 0.145),
        ("treblo_sliders", 0.648, 0.563, 0.10),
        ("claude_input", 0.461, 0.847, 0.20),
        ("flow_generate", 0.500, 0.833, 0.13),
        ("flow_reference", 0.137, 0.292, 0.095),
        ("flow_video_generate", 0.500, 0.847, 0.13),
        ("capcut_timeline", 0.500, 0.706, 0.14),
        ("capcut_export", 0.830, 0.122, 0.105),
    ],
)
def test_every_real_cue_fits_after_clamping(name, x, y, r):
    _assert_inside(*fit_circle(x * W, y * H, r * W, W, H))


def test_no_cue_is_large_enough_to_stop_pointing():
    """Past ~0.2 a circle encloses half the screen instead of indicating one thing."""
    from scripts._scene_library import CUES

    oversized = {k: c.r for k, c in CUES.items() if c.r > 0.2}
    assert not oversized, f"이 큐들은 가리키는 게 아니라 화면을 덮습니다: {oversized}"


def test_drawn_output_keeps_the_ring_on_canvas(tmp_path):
    src = tmp_path / "src.png"
    Image.new("RGB", (W, H), (0, 0, 0)).save(src)
    out = tmp_path / "out.png"

    # A button near the bottom edge: the case that was being clipped.
    apply_cue_circle(src, out, 0.5, 0.847, 0.13)

    pixels = Image.open(out).convert("RGB").load()
    red_rows = [yy for yy in range(H) if any(pixels[xx, yy][0] > 150 for xx in range(W))]
    assert red_rows, "빨간 원이 그려지지 않았습니다"
    # The ring closes above the bottom edge instead of being cut by it.
    assert max(red_rows) < H - 1
