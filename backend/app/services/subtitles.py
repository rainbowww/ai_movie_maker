"""Korean subtitle generation + font discovery for burned-in captions.

Sync model: a scene clip is exactly as long as its narration audio. A long
line is split into several cues whose durations are proportional to their
character counts, so the text on screen tracks the voice through the line
instead of sitting there as one wall of text. Splits prefer sentence
endings, then clause commas, then spaces — so a cue break lands where a
speaker would pause.

Korean text needs a CJK-capable font. Rather than vendoring a multi-megabyte
font binary into git, this module discovers one from the system and lets an
operator override the choice with SUBTITLE_FONT_PATH.
"""
from __future__ import annotations

import os
import platform
import re
from pathlib import Path

# Common Korean-capable fonts per platform, in preference order.
FONT_CANDIDATES = {
    "Linux": [
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ],
    "Darwin": [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleGothic.ttf",
    ],
    "Windows": [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/NanumGothic.ttf",
    ],
}

MAX_CHARS_PER_LINE = 32
MAX_LINES_PER_CUE = 2
MAX_CHARS_PER_CUE = MAX_CHARS_PER_LINE * MAX_LINES_PER_CUE
MIN_CUE_SECONDS = 1.0

# Prefer breaking after a sentence ending, then after a comma, then a space.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


class SubtitleError(RuntimeError):
    pass


def find_korean_font() -> Path:
    """Return a path to a Korean-capable font file, or raise with a fix hint."""
    override = os.environ.get("SUBTITLE_FONT_PATH", "").strip()
    if override:
        p = Path(override)
        if not p.exists():
            raise SubtitleError(f"SUBTITLE_FONT_PATH가 가리키는 폰트가 없습니다: {p}")
        return p

    for candidate in FONT_CANDIDATES.get(platform.system(), []):
        p = Path(candidate)
        if p.exists():
            return p

    raise SubtitleError(
        "한글 자막용 폰트를 찾지 못했습니다. 다음 중 하나로 해결하세요:\n"
        "  - Ubuntu/Debian: sudo apt install fonts-nanum fonts-noto-cjk\n"
        "  - 또는 SUBTITLE_FONT_PATH 환경변수에 .ttf/.ttc 경로를 직접 지정"
    )


def srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _split_long_chunk(chunk: str, limit: int) -> list[str]:
    """Break a chunk that is still too long, preferring commas then spaces."""
    out: list[str] = []
    remaining = chunk
    while len(remaining) > limit:
        window = remaining[: limit + 1]
        cut = max(window.rfind(", "), window.rfind(" "))
        if cut <= 0:
            cut = limit
        out.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()
    if remaining:
        out.append(remaining)
    return out


def split_caption(caption: str, limit: int = MAX_CHARS_PER_CUE) -> list[str]:
    """Split one narration line into subtitle-sized chunks."""
    text = " ".join(caption.split())
    if not text:
        return []

    chunks: list[str] = []
    for sentence in _SENTENCE_END.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        if chunks and len(chunks[-1]) + 1 + len(sentence) <= limit:
            chunks[-1] = f"{chunks[-1]} {sentence}"
        elif len(sentence) <= limit:
            chunks.append(sentence)
        else:
            chunks.extend(_split_long_chunk(sentence, limit))
    return chunks


def wrap_caption(text: str, max_chars: int = MAX_CHARS_PER_LINE,
                 max_lines: int = MAX_LINES_PER_CUE) -> str:
    """Wrap one cue's text onto at most `max_lines` lines."""
    text = " ".join(text.split())
    if not text:
        return ""

    lines: list[str] = []
    remaining = text
    while remaining and len(lines) < max_lines:
        if len(remaining) <= max_chars:
            lines.append(remaining)
            remaining = ""
            break
        window = remaining[: max_chars + 1]
        cut = window.rfind(" ")
        if cut <= 0:
            cut = max_chars
        lines.append(remaining[:cut].strip())
        remaining = remaining[cut:].strip()

    if remaining:  # shouldn't happen after split_caption, but never drop text
        lines[-1] = f"{lines[-1]} {remaining}".strip()
    return "\n".join(lines)


def caption_cues(caption: str, duration: float, start: float = 0.0) -> list[tuple[float, float, str]]:
    """Time a narration line's chunks across `duration`, proportional to length.

    Returns (start, end, text) tuples. Without word-level timings from the
    TTS engine, character share is the closest proxy for how long each chunk
    takes to speak; the cues always tile the full clip with no gaps, so the
    last cue ends exactly when the audio does.
    """
    chunks = split_caption(caption)
    if not chunks:
        return []

    total_chars = sum(len(c) for c in chunks)
    cues: list[tuple[float, float, str]] = []
    cursor = start
    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            end = start + duration  # absorb rounding into the final cue
        else:
            share = (len(chunk) / total_chars) * duration
            end = cursor + max(MIN_CUE_SECONDS, share)
            end = min(end, start + duration)
        cues.append((cursor, end, chunk))
        cursor = end
    return cues


def write_srt(cues: list[tuple[float, float, str]], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        f"{i}\n{srt_timestamp(start)} --> {srt_timestamp(end)}\n{wrap_caption(text)}\n"
        for i, (start, end, text) in enumerate(cues, start=1)
    ]
    out_path.write_text("\n".join(blocks), encoding="utf-8")
    return out_path


def write_scene_srt(caption: str, duration: float, out_path: Path) -> Path:
    """SRT for a single scene clip, timed from 0."""
    return write_srt(caption_cues(caption, duration), out_path)


def ass_timestamp(seconds: float) -> str:
    """ASS uses H:MM:SS.cc (centiseconds, single-digit hours)."""
    if seconds < 0:
        seconds = 0.0
    centis = int(round(seconds * 100))
    hours, centis = divmod(centis, 360_000)
    minutes, centis = divmod(centis, 6_000)
    secs, centis = divmod(centis, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"


def write_ass(
    cues: list[tuple[float, float, str]],
    out_path: Path,
    font_name: str,
    play_res_x: int,
    play_res_y: int,
    font_size: int = 34,
    margin_v: int = 14,
) -> Path:
    """Write burn-in subtitles as ASS.

    SRT is written too (for distribution), but burning uses ASS because it
    carries the script resolution: libass sizes SRT text against a default
    384x288 canvas and scales it up, which silently inflates the font and
    re-wraps lines. With PlayResX/Y pinned to the real frame, Fontsize and
    MarginV are exact pixels, and WrapStyle 2 keeps the line breaks we chose.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {play_res_x}\n"
        f"PlayResY: {play_res_y}\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: KR,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00101014,&H00000000,"
        f"1,0,0,0,100,100,0,0,1,3,0,2,40,40,{margin_v},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = []
    for start, end, text in cues:
        body = wrap_caption(text).replace("\n", r"\N")
        lines.append(
            f"Dialogue: 0,{ass_timestamp(start)},{ass_timestamp(end)},KR,,0,0,0,,{body}"
        )
    out_path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def escape_for_filter(path: Path) -> str:
    """Escape a path for use inside an ffmpeg filtergraph argument."""
    s = str(path)
    s = s.replace("\\", "/")
    s = s.replace(":", r"\:")
    s = s.replace("'", r"\'")
    return s


def build_subtitles_filter(ass_path: Path, font_path: Path) -> str:
    """ffmpeg -vf fragment that burns an ASS subtitle file in.

    Styling lives in the ASS file itself (see write_ass), so nothing is
    overridden here; fontsdir points libass at the discovered font so it
    resolves even when the system font cache does not know it.
    """
    return (
        f"subtitles={escape_for_filter(ass_path)}"
        f":fontsdir={escape_for_filter(font_path.parent)}"
    )


def font_family_name(font_path: Path) -> str:
    """Best-effort family name for a font file, for the ASS Style line."""
    try:
        from PIL import ImageFont

        font = ImageFont.truetype(str(font_path), 20)
        family, _style = font.getname()
        return family
    except Exception:
        return font_path.stem
