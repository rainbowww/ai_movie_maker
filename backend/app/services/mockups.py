"""Draw every scene's artwork with Pillow — no API, no cost, no network.

The Gemini path produces richer images, but an image model cannot be told
"put the Generate button exactly here", and the red click-cue has to land
on a real control to mean anything. These mockups are drawn to a known
layout, so the cue coordinates in the scene library hit the button they
are pointing at, every time.

They are also the zero-cost path: a full narrated cut can be produced and
reviewed without spending anything.

Canvas is 1280x720 — the render pipeline's content area, before the
subtitle band is padded on.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720

# Palette shared with the frontend and the subtitle styling.
INK = (18, 20, 28)
SURFACE = (26, 29, 41)
SURFACE_2 = (35, 40, 56)
LINE = (52, 59, 82)
TEXT = (238, 240, 247)
TEXT_DIM = (152, 160, 184)
AMBER = (255, 180, 84)
CUE = (255, 71, 87)
BLUE = (90, 169, 255)
PINK = (255, 134, 176)
GREEN = (61, 220, 151)
SKIN = (232, 184, 155)
HAIR = (59, 44, 34)

FONT_DIR = Path("/usr/share/fonts/truetype/nanum")
FONT_REGULAR = FONT_DIR / "NanumBarunGothic.ttf"
FONT_BOLD = FONT_DIR / "NanumBarunGothicBold.ttf"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR
    if not path.exists():  # fall back to whatever PIL can find
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)


# --- primitives -------------------------------------------------------------

def _bg(color=INK) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), color)
    return img, ImageDraw.Draw(img)


def _window(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
            fill=SURFACE, title: str = "") -> None:
    """A browser/app window with a title bar and traffic lights."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=fill, outline=LINE, width=2)
    d.line([x, y + 44, x + w, y + 44], fill=LINE, width=2)
    for i, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([x + 20 + i * 22, y + 16, x + 32 + i * 22, y + 28], fill=c)
    if title:
        d.text((x + 100, y + 14), title, font=_font(15), fill=TEXT_DIM)


def _button(d: ImageDraw.ImageDraw, cx: int, cy: int, label: str,
            w: int = 190, h: int = 54, fill=AMBER, fg=INK) -> None:
    d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
                        radius=h // 2, fill=fill)
    f = _font(21, bold=True)
    tw = d.textlength(label, font=f)
    d.text((cx - tw / 2, cy - 14), label, font=f, fill=fg)


def _input(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
           lines: int = 3, placeholder: str = "") -> None:
    d.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=SURFACE_2,
                        outline=(58, 65, 90), width=2)
    if placeholder:
        d.text((x + 22, y + 20), placeholder, font=_font(19), fill=TEXT_DIM)
        start = y + 56
    else:
        start = y + 24
    widths = [0.72, 0.55, 0.38, 0.6]
    for i in range(lines):
        ly = start + i * 26
        if ly + 12 > y + h - 10:
            break
        d.rounded_rectangle([x + 22, ly, x + 22 + int((w - 44) * widths[i % 4]), ly + 11],
                            radius=5, fill=(75, 81, 101) if i == 0 else (58, 65, 90))


def _chip(d: ImageDraw.ImageDraw, x: int, y: int, label: str,
          active: bool = False) -> int:
    f = _font(17)
    tw = int(d.textlength(label, font=f))
    w = tw + 36
    d.rounded_rectangle([x, y, x + w, y + 38], radius=19,
                        fill=AMBER if active else (58, 65, 90))
    d.text((x + 18, y + 9), label, font=f, fill=INK if active else TEXT)
    return x + w + 12


def _slider(d: ImageDraw.ImageDraw, x: int, y: int, w: int, pct: float,
            label: str) -> None:
    d.text((x, y - 28), label, font=_font(17), fill=TEXT_DIM)
    d.rounded_rectangle([x, y, x + w, y + 10], radius=5, fill=LINE)
    d.rounded_rectangle([x, y, x + int(w * pct), y + 10], radius=5, fill=BLUE)
    knob = x + int(w * pct)
    d.ellipse([knob - 13, y - 8, knob + 13, y + 18], fill=TEXT)


def _bubble(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
            right: bool = False, lines: int = 2) -> None:
    fill = AMBER if right else SURFACE_2
    bar = (18, 20, 28) if right else TEXT_DIM
    d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=fill)
    for i in range(lines):
        ly = y + 22 + i * 24
        if ly + 11 > y + h - 12:
            break
        frac = [0.74, 0.9, 0.52][i % 3]
        d.rounded_rectangle([x + 24, ly, x + 24 + int((w - 48) * frac), ly + 11],
                            radius=5, fill=bar)


def _thumb(d: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int,
           tone: tuple[int, int, int], face: bool = False) -> None:
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=tone)
    if face:
        cx, cy = x + w // 2, y + h // 2 - 4
        d.ellipse([cx - 16, cy - 20, cx + 16, cy + 12], fill=SKIN)
        d.rounded_rectangle([cx - 24, cy + 14, cx + 24, y + h - 6], radius=10, fill=PINK)
    else:
        d.rectangle([x + 10, y + h - 26, x + w - 10, y + h - 10], fill=(0, 0, 0, 40))


def _skyline(d: ImageDraw.ImageDraw, baseline: int, tone=(35, 40, 56)) -> None:
    towers = [(0, 190), (78, 250), (140, 160), (196, 300), (270, 210),
              (900, 230), (968, 300), (1040, 170), (1104, 260), (1180, 200)]
    for x, h in towers:
        d.rectangle([x, baseline - h, x + 62, baseline], fill=tone)
        for row in range(3):
            for col in range(2):
                wx = x + 12 + col * 26
                wy = baseline - h + 24 + row * 44
                if wy < baseline - 20:
                    d.rectangle([wx, wy, wx + 12, wy + 14], fill=AMBER)


def _presenter(d: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0,
               female: bool = False, glasses: bool = True) -> None:
    s = scale
    body = PINK if female else (75, 81, 101)
    d.polygon([
        (cx - int(96 * s), cy + int(250 * s)),
        (cx - int(74 * s), cy + int(70 * s)),
        (cx + int(74 * s), cy + int(70 * s)),
        (cx + int(96 * s), cy + int(250 * s)),
    ], fill=body)
    d.rectangle([cx - int(18 * s), cy + int(30 * s), cx + int(18 * s), cy + int(80 * s)], fill=SKIN)
    d.ellipse([cx - int(62 * s), cy - int(62 * s), cx + int(62 * s), cy + int(62 * s)], fill=SKIN)
    if female:
        d.pieslice([cx - int(70 * s), cy - int(78 * s), cx + int(70 * s), cy + int(70 * s)],
                   start=180, end=360, fill=HAIR)
        d.ellipse([cx - int(72 * s), cy - int(30 * s), cx - int(44 * s), cy + int(60 * s)], fill=HAIR)
        d.ellipse([cx + int(44 * s), cy - int(30 * s), cx + int(72 * s), cy + int(60 * s)], fill=HAIR)
    else:
        d.pieslice([cx - int(66 * s), cy - int(74 * s), cx + int(66 * s), cy + int(40 * s)],
                   start=180, end=360, fill=HAIR)
        d.chord([cx - int(44 * s), cy + int(14 * s), cx + int(44 * s), cy + int(62 * s)],
                start=0, end=180, fill=HAIR)
    eye = int(6 * s)
    d.ellipse([cx - int(26 * s) - eye, cy - eye, cx - int(26 * s) + eye, cy + eye], fill=INK)
    d.ellipse([cx + int(26 * s) - eye, cy - eye, cx + int(26 * s) + eye, cy + eye], fill=INK)
    if glasses and not female:
        for side in (-1, 1):
            gx = cx + side * int(26 * s)
            d.rounded_rectangle([gx - int(22 * s), cy - int(16 * s), gx + int(22 * s), cy + int(14 * s)],
                                radius=int(6 * s), outline=INK, width=max(2, int(3 * s)))
        d.line([cx - int(4 * s), cy, cx + int(4 * s), cy], fill=INK, width=max(2, int(3 * s)))


def _glow(img: Image.Image, cx: int, cy: int, radius: int, color, alpha: int = 46) -> Image.Image:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                                  fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(70))
    return Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")


def _studio(tint) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img, d = _bg(SURFACE)
    for i in range(0, W, 4):
        shade = int(18 + 14 * (i / W))
        d.line([(i, 0), (i, H)], fill=(shade, shade + 2, shade + 10))
    img = _glow(img, W // 2, 300, 420, tint, 52)
    return img, ImageDraw.Draw(img)


# --- scenes -----------------------------------------------------------------

def hook_rooftop() -> Image.Image:
    img, d = _bg((27, 32, 64))
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(27 - 12 * t), int(32 - 15 * t), int(64 - 40 * t)))
    for sx, sy, r in [(120, 70, 2), (300, 44, 2), (520, 90, 2), (760, 50, 2), (1020, 78, 2), (1180, 40, 2)]:
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=TEXT)
    _skyline(d, 560)
    d.rectangle([0, 560, W, H], fill=(16, 18, 26))
    d.ellipse([560, 470, 720, 560], fill=(22, 25, 36))
    _presenter(d, 640, 430, 0.62, female=True, glasses=False)
    return _glow(img, 640, 480, 300, AMBER, 30)


def hook_fireflies() -> Image.Image:
    img, d = _bg((20, 24, 40))
    d.ellipse([360, 300, 920, 640], fill=(32, 26, 24))
    d.ellipse([420, 330, 860, 600], fill=SKIN)
    for fx, fy, r in [(520, 360, 9), (640, 300, 12), (760, 380, 8), (700, 430, 6), (560, 450, 7)]:
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=AMBER)
    return _glow(img, 640, 380, 260, AMBER, 60)


def hook_skyline_gaze() -> Image.Image:
    img, d = _bg((24, 28, 52))
    _skyline(d, 600, (30, 35, 52))
    d.rectangle([0, 600, W, H], fill=(16, 18, 26))
    _presenter(d, 360, 380, 0.78, female=True, glasses=False)
    return _glow(img, 880, 420, 340, AMBER, 44)


def hook_street_run() -> Image.Image:
    img, d = _bg((30, 24, 20))
    d.polygon([(0, H), (480, 300), (800, 300), (W, H)], fill=(38, 30, 26))
    for x in (120, 300, 980, 1160):
        d.rectangle([x - 90, 120, x + 90, 520], fill=(46, 34, 30))
    for i in range(10):
        lx = 200 + i * 96
        d.ellipse([lx - 8, 150 - (i % 3) * 14, lx + 8, 166 - (i % 3) * 14], fill=AMBER)
    _presenter(d, 640, 400, 0.72, female=True, glasses=False)
    return _glow(img, 640, 260, 380, AMBER, 50)


def hook_light_particles() -> Image.Image:
    img, d = _bg((34, 26, 44))
    _presenter(d, 640, 380, 0.8, female=True, glasses=False)
    for i in range(48):
        ang = i * 7.5
        import math
        rad = 210 + (i % 5) * 34
        px = 640 + int(rad * math.cos(math.radians(ang)))
        py = 400 + int(rad * 0.55 * math.sin(math.radians(ang)))
        r = 3 + (i % 3) * 2
        d.ellipse([px - r, py - r, px + r, py + r], fill=AMBER)
    return _glow(img, 640, 400, 420, AMBER, 56)


def logo_sting() -> Image.Image:
    img, d = _bg(INK)
    d.rounded_rectangle([520, 240, 760, 470], radius=40, fill=SURFACE_2, outline=BLUE, width=4)
    d.ellipse([566, 300, 616, 350], fill=BLUE)
    d.ellipse([664, 300, 714, 350], fill=BLUE)
    d.rounded_rectangle([576, 390, 704, 418], radius=14, fill=AMBER)
    d.line([640, 200, 640, 240], fill=BLUE, width=6)
    d.ellipse([624, 176, 656, 208], fill=AMBER)
    for x in (430, 850):
        for i in range(4):
            d.rectangle([x - 12, 250 + i * 54, x + 12, 280 + i * 54], fill=(40, 46, 66))
    return _glow(img, 640, 350, 360, BLUE, 44)


def _host(female: bool, prop: str = "") -> Image.Image:
    img, d = _studio(PINK if female else BLUE)
    _presenter(d, 640, 300, 1.0, female=female)
    if prop == "laptop":
        d.polygon([(500, 640), (780, 640), (820, 700), (460, 700)], fill=(60, 66, 88))
        d.rounded_rectangle([520, 510, 760, 645], radius=10, fill=SURFACE_2, outline=LINE, width=3)
        d.rounded_rectangle([540, 530, 740, 626], radius=6, fill=(20, 24, 36))
    elif prop == "point":
        d.ellipse([880, 470, 940, 530], fill=SKIN)
        d.rounded_rectangle([900, 420, 922, 500], radius=11, fill=SKIN)
    elif prop == "card":
        d.rounded_rectangle([860, 250, 1160, 470], radius=18, fill=SURFACE_2, outline=AMBER, width=3)
        d.text((890, 280), "MASTER PROMPT", font=_font(20, bold=True), fill=AMBER)
        for i in range(4):
            d.rounded_rectangle([890, 330 + i * 30, 1130 - i * 40, 342 + i * 30], radius=6, fill=(58, 65, 90))
    elif prop == "flow":
        d.rounded_rectangle([880, 280, 1150, 420], radius=18, fill=SURFACE_2, outline=BLUE, width=3)
        d.ellipse([930, 320, 990, 380], fill=BLUE)
        d.polygon([(950, 335), (978, 350), (950, 365)], fill=INK)
        d.text((1010, 340), "FLOW", font=_font(24, bold=True), fill=TEXT)
    return img


def host_m() -> Image.Image:
    return _host(False)


def host_m_laptop() -> Image.Image:
    return _host(False, "laptop")


def host_m_pointing() -> Image.Image:
    return _host(False, "point")


def host_m_flow() -> Image.Image:
    return _host(False, "flow")


def master_prompt_card() -> Image.Image:
    return _host(False, "card")


def host_f() -> Image.Image:
    return _host(True)


def host_f_gesturing() -> Image.Image:
    return _host(True, "point")


def treblo_home() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="treblo — AI Music Generator")
    d.rounded_rectangle([100, 120, 1180, 330], radius=16, fill=(30, 34, 50))
    d.text((140, 160), "무료 AI 작곡", font=_font(40, bold=True), fill=TEXT)
    d.text((140, 220), "프롬프트 한 줄로 완성곡을 만듭니다", font=_font(22), fill=TEXT_DIM)
    _button(d, 250, 290, "시작하기", w=180, h=48)
    for i in range(3):
        x = 100 + i * 370
        d.rounded_rectangle([x, 370, x + 340, 560], radius=14, fill=SURFACE_2)
        d.ellipse([x + 28, 398, x + 76, 446], fill=[AMBER, BLUE, PINK][i])
        d.rounded_rectangle([x + 28, 470, x + 250, 484], radius=7, fill=(75, 81, 101))
        d.rounded_rectangle([x + 28, 500, x + 190, 512], radius=6, fill=(58, 65, 90))
    return img


def treblo_simple() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="treblo — Simple")
    d.text((110, 100), "Simple", font=_font(20, bold=True), fill=AMBER)
    d.text((210, 100), "Advanced", font=_font(20), fill=TEXT_DIM)
    _input(d, 110, 160, 1060, 240, lines=3,
           placeholder="만들고 싶은 곡을 설명해 주세요")
    _button(d, 640, 548, "생성", w=200, h=58)
    return img


def treblo_advanced() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="treblo — Advanced")
    d.text((110, 100), "Simple", font=_font(20), fill=TEXT_DIM)
    d.text((210, 100), "Advanced", font=_font(20, bold=True), fill=AMBER)
    _input(d, 110, 150, 1060, 60, lines=1)
    x = 110
    for label, active in [("Pop", False), ("Indie", False), ("Electronic", True),
                          ("90s", False), ("Lo-fi", False)]:
        x = _chip(d, x, 250, label, active)
    _slider(d, 110, 400, 1060, 0.68, "Style Strength")
    _slider(d, 110, 500, 1060, 0.42, "Duration")
    _button(d, 640, 600, "생성", w=180, h=50)
    return img


def treblo_results() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="treblo — Results")
    for i in range(2):
        y = 130 + i * 230
        color = AMBER if i == 0 else PINK
        d.rounded_rectangle([110, y, 1170, y + 190], radius=16, fill=SURFACE_2)
        d.ellipse([150, y + 60, 220, y + 130], fill=color)
        d.polygon([(174, y + 76), (206, y + 95), (174, y + 114)], fill=INK)
        d.rounded_rectangle([260, y + 58, 620, y + 76], radius=8, fill=TEXT)
        d.rounded_rectangle([260, y + 100, 500, y + 114], radius=7, fill=TEXT_DIM)
        for b in range(26):
            bh = 20 + (b * 37 % 70)
            bx = 700 + b * 17
            d.rounded_rectangle([bx, y + 120 - bh, bx + 9, y + 130], radius=4, fill=color)
    return img


def claude_chat() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, fill=(250, 249, 245), title="")
    d.rounded_rectangle([60, 50, 1220, 94], radius=16, fill=(240, 237, 230))
    d.text((160, 62), "Claude", font=_font(17, bold=True), fill=(120, 80, 40))
    _bubble(d, 110, 130, 520, 110, right=False, lines=2)
    _bubble(d, 560, 270, 610, 130, right=True, lines=3)
    _bubble(d, 110, 430, 560, 110, right=False, lines=2)
    d.rounded_rectangle([110, 580, 1070, 640], radius=30, fill=(238, 235, 228),
                        outline=(214, 208, 196), width=2)
    d.text((140, 598), "메시지를 입력하세요", font=_font(19), fill=(150, 145, 135))
    d.ellipse([1100, 580, 1160, 640], fill=AMBER)
    d.polygon([(1120, 598), (1146, 610), (1120, 622)], fill=(250, 249, 245))
    return img


def claude_storyplan() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, fill=(250, 249, 245))
    d.text((110, 110), "STORY PLAN", font=_font(24, bold=True), fill=(120, 80, 40))
    _thumb(d, 110, 170, 190, 210, (238, 226, 210), face=True)
    for i in range(3):
        _thumb(d, 330 + i * 200, 170, 180, 210, [(206, 214, 226), (226, 210, 206), (210, 222, 214)][i])
    for i in range(3):
        y = 420 + i * 62
        d.rounded_rectangle([110, y, 1170, y + 48], radius=10, fill=(240, 237, 230))
        d.rounded_rectangle([132, y + 18, 132 + 420 - i * 90, y + 30], radius=6, fill=(186, 180, 170))
    return img


def flow_image() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="Flow — Image")
    d.rounded_rectangle([100, 110, 330, 640], radius=14, fill=SURFACE_2)
    for i, label in enumerate(["Image", "Video", "16:9"]):
        y = 150 + i * 62
        on = i == 0
        d.rounded_rectangle([130, y, 300, y + 44], radius=22, fill=(58, 65, 90))
        d.ellipse([138, y + 8, 166, y + 36], fill=BLUE if on else (75, 81, 101))
        d.text((180, y + 12), label, font=_font(17), fill=TEXT)
    d.rounded_rectangle([370, 110, 1180, 520], radius=14, fill=(16, 18, 26), outline=LINE, width=2)
    _thumb(d, 640, 170, 280, 300, (46, 36, 58), face=True)
    _button(d, 640, 600, "생성", w=180, h=50)
    return img


def flow_gallery() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="Flow — Library")
    tones = [(46, 36, 58), (30, 38, 60), (34, 48, 54), (52, 38, 40),
             (38, 34, 56), (28, 44, 48), (50, 44, 34), (36, 40, 62)]
    for i, tone in enumerate(tones):
        x = 110 + (i % 4) * 275
        y = 130 + (i // 4) * 260
        _thumb(d, x, y, 250, 220, tone, face=(i == 0))
    return img


def flow_rename() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="Flow — Library")
    for i in range(4):
        y = 130 + i * 130
        d.rounded_rectangle([110, y, 1170, y + 108], radius=12, fill=SURFACE_2)
        _thumb(d, 130, y + 12, 130, 84, [(46, 36, 58), (30, 38, 60), (34, 48, 54), (52, 38, 40)][i],
               face=(i == 0))
        if i == 1:
            d.rounded_rectangle([290, y + 32, 700, y + 76], radius=8, fill=(16, 18, 26),
                                outline=AMBER, width=2)
            d.text((312, y + 42), "LOC-01", font=_font(20), fill=TEXT)
            d.line([690, y + 40, 690, y + 68], fill=AMBER, width=3)
        else:
            d.text((300, y + 42), ["CHAR-01", "LOC-01", "LOC-02", "LOC-03"][i],
                   font=_font(20), fill=TEXT_DIM)
    return img


def flow_video() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="Flow — Video")
    d.text((110, 110), "Ingredients", font=_font(17), fill=TEXT_DIM)
    for i in range(3):
        x = 110 + i * 150
        _thumb(d, x, 145, 130, 130, [(46, 36, 58), (30, 38, 60), (34, 48, 54)][i], face=(i == 0))
        if i == 0:
            d.rounded_rectangle([x - 4, 141, x + 134, 279], radius=12, outline=BLUE, width=4)
    d.rounded_rectangle([600, 130, 1180, 500], radius=14, fill=(16, 18, 26), outline=LINE, width=2)
    d.ellipse([850, 270, 930, 350], fill=TEXT)
    d.polygon([(876, 288), (914, 310), (876, 332)], fill=INK)
    _button(d, 640, 610, "생성", w=180, h=50)
    return img


def capcut() -> Image.Image:
    img, d = _bg(INK)
    _window(d, 60, 50, 1160, 620, title="편집기")
    d.rounded_rectangle([100, 110, 860, 430], radius=12, fill=(14, 16, 24))
    d.ellipse([440, 230, 520, 310], fill=(46, 52, 74))
    d.polygon([(466, 248), (504, 270), (466, 292)], fill=TEXT)
    d.rounded_rectangle([890, 110, 1180, 430], radius=12, fill=SURFACE_2)
    for i in range(4):
        d.rounded_rectangle([910, 140 + i * 70, 1160, 195 + i * 70], radius=8, fill=(48, 55, 78))
    clips = [(100, 300, (58, 40, 70)), (410, 230, (32, 52, 62)), (650, 180, (60, 48, 36)),
             (840, 210, (40, 46, 70)), (1060, 120, (52, 38, 44))]
    for x, w, c in clips:
        d.rounded_rectangle([x, 470, x + w - 10, 546], radius=8, fill=c)
    d.rounded_rectangle([100, 560, 1180, 630], radius=8, fill=(14, 16, 24))
    for b in range(64):
        bh = 8 + (b * 53 % 46)
        bx = 116 + b * 17
        d.rounded_rectangle([bx, 595 - bh // 2, bx + 8, 595 + bh // 2], radius=3, fill=AMBER)
    _button(d, 1063, 88, "내보내기", w=196, h=50)
    return img


def final_montage() -> Image.Image:
    img, d = _bg(INK)
    panels = [hook_rooftop, hook_street_run, hook_skyline_gaze, hook_light_particles]
    for i, fn in enumerate(panels):
        sub = fn().resize((632, 352))
        img.paste(sub, (8 + (i % 2) * 640, 8 + (i // 2) * 360))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=INK)
    return img


def outro_solo() -> Image.Image:
    img, d = _studio(BLUE)
    _presenter(d, 640, 300, 1.0, female=False)
    d.ellipse([200, 160, 320, 280], fill=CUE)
    d.polygon([(196, 220), (260, 150), (324, 220), (260, 300)], fill=CUE)
    d.rounded_rectangle([960, 170, 1080, 270], radius=20, fill=AMBER)
    d.pieslice([960, 150, 1080, 270], start=180, end=360, fill=AMBER)
    d.ellipse([1004, 274, 1036, 300], fill=AMBER)
    d.text((880, 560), "좋아요 · 구독", font=_font(34, bold=True), fill=TEXT)
    return img


def outro_two_hosts() -> Image.Image:
    img, d = _studio(PINK)
    _presenter(d, 470, 320, 0.88, female=True, glasses=False)
    _presenter(d, 810, 320, 0.88, female=False)
    d.ellipse([170, 150, 270, 250], fill=CUE)
    d.polygon([(166, 202), (220, 142), (274, 202), (220, 262)], fill=CUE)
    d.rounded_rectangle([1010, 160, 1120, 250], radius=18, fill=AMBER)
    d.pieslice([1010, 142, 1120, 250], start=180, end=360, fill=AMBER)
    d.ellipse([1050, 254, 1080, 278], fill=AMBER)
    return img


RENDERERS: dict[str, Callable[[], Image.Image]] = {
    "hook_rooftop": hook_rooftop,
    "hook_fireflies": hook_fireflies,
    "hook_skyline_gaze": hook_skyline_gaze,
    "hook_street_run": hook_street_run,
    "hook_light_particles": hook_light_particles,
    "logo_sting": logo_sting,
    "host_m": host_m,
    "host_m_laptop": host_m_laptop,
    "host_m_pointing": host_m_pointing,
    "host_m_flow": host_m_flow,
    "host_f": host_f,
    "host_f_gesturing": host_f_gesturing,
    "master_prompt_card": master_prompt_card,
    "treblo_home": treblo_home,
    "treblo_simple": treblo_simple,
    "treblo_advanced": treblo_advanced,
    "treblo_results": treblo_results,
    "claude_chat": claude_chat,
    "claude_storyplan": claude_storyplan,
    "flow_image": flow_image,
    "flow_gallery": flow_gallery,
    "flow_rename": flow_rename,
    "flow_video": flow_video,
    "capcut": capcut,
    "final_montage": final_montage,
    "outro_solo": outro_solo,
    "outro_two_hosts": outro_two_hosts,
}


def render_mockup(visual_key: str, out_path: Path) -> Path:
    """Draw `visual_key` to out_path. Unknown keys get a neutral card."""
    fn = RENDERERS.get(visual_key)
    if fn is None:
        img, d = _bg(SURFACE)
        d.text((80, 320), visual_key, font=_font(34, bold=True), fill=TEXT_DIM)
    else:
        img = fn()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
