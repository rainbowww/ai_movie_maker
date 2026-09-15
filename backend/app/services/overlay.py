"""Draw the red 'click here' cue circle on top of a generated scene image.

Deliberately done with Pillow in a separate pass, rather than asked for in
the Gemini image prompt itself: an image model cannot reliably place a
circle at an exact normalized coordinate, but Pillow can, every time.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

CUE_COLOR = (255, 71, 87, 255)  # #ff4757 — same accent used across this project
CUE_WIDTH_RATIO = 0.012  # stroke width relative to image width
CUE_MARGIN_RATIO = 0.006  # keep the ring this far off the edge
CUE_MIN_RADIUS_RATIO = 0.05  # below this a circle stops reading as a pointer


def fit_circle(cx: float, cy: float, radius: float, w: int, h: int) -> tuple[float, float, float]:
    """Shrink (and only if it must, move) a circle so the whole ring is visible.

    A cue circle that runs off the canvas is drawn as an arc, and an arc
    does not read as "click here" — it reads as a stray line. Targets near
    an edge are exactly the ones this happens to: a 생성 button sitting at
    y=600 of 720 with a 166px radius loses its bottom.

    The centre is what carries the meaning, so the radius gives way first
    and the centre only moves when shrinking alone would leave the circle
    too small to notice.
    """
    margin = w * CUE_MARGIN_RATIO
    stroke = max(3, int(w * CUE_WIDTH_RATIO))
    # The ring is stroked centred on the path, so half of it sits outside.
    inset = margin + stroke / 2

    room = min(cx, cy, w - cx, h - cy) - inset
    minimum = w * CUE_MIN_RADIUS_RATIO

    if radius <= room:
        return cx, cy, radius
    if room >= minimum:
        return cx, cy, room

    # Too close to an edge to fit even a small circle — nudge inward by the
    # least amount that fits `minimum`, so the ring stays whole and still
    # sits over the target.
    radius = min(minimum, (min(w, h) / 2) - inset)
    cx = min(max(cx, radius + inset), w - radius - inset)
    cy = min(max(cy, radius + inset), h - radius - inset)
    return cx, cy, radius


def apply_cue_circle(src_path: Path, out_path: Path, x: float, y: float, r: float) -> Path:
    """x, y, r are normalized 0-1 values relative to the image's width."""
    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy, radius = fit_circle(x * w, y * h, r * w, w, h)
    stroke = max(3, int(w * CUE_WIDTH_RATIO))
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=CUE_COLOR,
        width=stroke,
    )

    combined = Image.alpha_composite(img, overlay).convert("RGB")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(out_path, "PNG")
    return out_path
