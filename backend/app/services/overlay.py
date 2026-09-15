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


def apply_cue_circle(src_path: Path, out_path: Path, x: float, y: float, r: float) -> Path:
    """x, y, r are normalized 0-1 values relative to the image's width."""
    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    cx, cy = x * w, y * h
    radius = r * w
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
