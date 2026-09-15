"""Turn on-screen caption text into text the TTS engine can actually read.

What a viewer should *read* and what an engine should *say* are not the
same string. Two espeak-ng defects make the difference audible, and both
are visible in its phoneme output (`espeak-ng -v ko+m3 -x -q`):

    "AI 영상"    -> (en),eI'aI(ko) j'@NsaN
    "에이아이 영상" -> 'ei;,ai j'@NsaN

The first switches to the *English* voice mid-sentence and switches back,
so the narrator's timbre changes for one word. The second stays in the
Korean voice.

    "90초"  -> g'u_! s'ip_! tSh'o
    "구십 초" -> gus'ip tSh'o

`_!` is a break. Digits get one inserted after every place, so "90초"
comes out as three chopped syllables instead of one word.

So the caption keeps "AI" and "100%" — that is what a Korean reader
expects to see — and only the string handed to the synthesiser is
rewritten. A scene can also set `speech_text` explicitly, which wins over
everything here.
"""
from __future__ import annotations

import re

# --- numbers ---------------------------------------------------------------

_SINO_DIGITS = "영일이삼사오육칠팔구"
_SMALL_UNITS = ("", "십", "백", "천")
_BIG_UNITS = ("", "만", "억", "조", "경")

# 고유어 수사. Above 99 Korean switches to Sino for every counter, so the
# table stops there. 20 has two forms: 스무 standing alone before a
# counter, 스물 as the head of a compound (스물한 개).
_NATIVE_ONES = ("", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉")
_NATIVE_TENS_ALONE = ("", "열", "스무", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔")
_NATIVE_TENS_PREFIX = ("", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔")

# Counters that take 고유어 수사. 분 is deliberately absent: in this domain
# it means minutes (삼십 분), not the honorific person counter (세 분).
_NATIVE_COUNTERS = (
    "개", "명", "번", "시", "살", "마리", "가지", "장", "권", "대", "잔",
    "벌", "켤레", "그루", "송이", "줄", "칸", "판", "조각", "군데", "차례",
)


def sino_number(n: int) -> str:
    """Read a whole number the 한자어 way: 0 -> 영, 100 -> 백, 10000 -> 만."""
    if n < 0:
        return "마이너스 " + sino_number(-n)
    if n == 0:
        return "영"

    groups: list[int] = []
    while n:
        groups.append(n % 10000)
        n //= 10000

    parts: list[str] = []
    for idx in range(len(groups) - 1, -1, -1):
        group = groups[idx]
        if group == 0:
            continue
        chunk = ""
        for pos in range(3, -1, -1):
            digit = (group // 10**pos) % 10
            if digit == 0:
                continue
            # 일십/일백/일천 are not how anyone says it — only the ones place
            # keeps its 일.
            chunk += ("" if digit == 1 and pos > 0 else _SINO_DIGITS[digit]) + _SMALL_UNITS[pos]
        if idx > 0 and chunk == "일":
            chunk = ""  # 만, not 일만
        parts.append(chunk + _BIG_UNITS[idx])
    return "".join(parts)


def native_number(n: int) -> str:
    """Read a whole number the 고유어 way. Falls back to 한자어 above 99."""
    if n <= 0 or n > 99:
        return sino_number(n)
    tens, ones = divmod(n, 10)
    if ones == 0:
        return _NATIVE_TENS_ALONE[tens]
    return _NATIVE_TENS_PREFIX[tens] + _NATIVE_ONES[ones]


def _read_number(digits: str, decimals: str, counter: str) -> str:
    whole = int(digits)
    use_native = bool(counter) and counter in _NATIVE_COUNTERS and not decimals
    spoken = native_number(whole) if use_native else sino_number(whole)
    if decimals:
        spoken += " 점 " + " ".join(_SINO_DIGITS[int(d)] for d in decimals)
    return spoken


# --- Latin ------------------------------------------------------------------

# Read letter by letter when an unknown acronym shows up, so at least it
# stays inside the Korean voice.
_LETTER_SOUNDS = {
    "a": "에이", "b": "비", "c": "씨", "d": "디", "e": "이", "f": "에프",
    "g": "지", "h": "에이치", "i": "아이", "j": "제이", "k": "케이", "l": "엘",
    "m": "엠", "n": "엔", "o": "오", "p": "피", "q": "큐", "r": "알",
    "s": "에스", "t": "티", "u": "유", "v": "브이", "w": "더블유", "x": "엑스",
    "y": "와이", "z": "지",
}

# Words this project actually says, plus the tools next to them. Keys are
# lowercase; lookup is case-insensitive.
_LATIN_WORDS = {
    # general
    "ai": "에이아이", "ui": "유아이", "ux": "유엑스", "url": "유알엘",
    "pc": "피씨", "tts": "티티에스", "api": "에이피아이", "cpu": "씨피유",
    "gpu": "지피유", "hd": "에이치디", "fhd": "에프에이치디", "4k": "사케이",
    "mp3": "엠피쓰리", "mp4": "엠피포", "png": "피엔지", "jpg": "제이페그",
    "gif": "지프", "srt": "에스알티", "ok": "오케이", "qr": "큐알",
    # tools and services
    "youtube": "유튜브", "shorts": "쇼츠", "google": "구글", "gemini": "제미나이",
    "chatgpt": "챗지피티", "openai": "오픈에이아이", "capcut": "캡컷",
    "treblo": "트레블로", "suno": "수노", "udio": "유디오", "canva": "캔바",
    "midjourney": "미드저니", "runway": "런웨이", "sora": "소라", "veo": "베오",
    "pika": "피카", "kling": "클링", "luma": "루마", "leonardo": "레오나르도",
    "photoshop": "포토샵", "premiere": "프리미어", "instagram": "인스타그램",
    "tiktok": "틱톡", "facebook": "페이스북", "spotify": "스포티파이",
    "figma": "피그마", "notion": "노션", "discord": "디스코드",
    # verbs and nouns that show up on buttons
    "prompt": "프롬프트", "download": "다운로드", "upload": "업로드",
    "export": "익스포트", "import": "임포트", "enter": "엔터", "login": "로그인",
    "logout": "로그아웃", "click": "클릭", "generate": "제너레이트",
    "preview": "프리뷰", "render": "렌더", "save": "세이브", "start": "스타트",
    "free": "프리", "pro": "프로", "plus": "플러스", "beta": "베타",
}

_SYMBOLS = {"%": " 퍼센트", "$": "달러 ", "&": " 앤드 ", "@": " 골뱅이 ", "+": " 플러스 "}

_UNKNOWN_LATIN: set[str] = set()

# A number, an optional decimal part, and whatever Hangul immediately
# follows it — that trailing text is what decides 고유어 vs 한자어.
_NUMBER_RE = re.compile(r"(\d[\d,]*)(?:\.(\d+))?\s*([가-힣]{1,3})?")
_LATIN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def _latin_to_hangul(token: str) -> str:
    known = _LATIN_WORDS.get(token.lower())
    if known:
        return known
    # An acronym stays in the Korean voice if it is spelled out.
    if token.isupper() and len(token) <= 5:
        return "".join(
            _LETTER_SOUNDS.get(ch.lower(), ch) if ch.isalpha() else sino_number(int(ch))
            for ch in token
        )
    _UNKNOWN_LATIN.add(token)
    return token


def unknown_latin_tokens() -> list[str]:
    """Latin words no mapping covered — they still switch the voice.

    Reported rather than silently accepted, so the dictionary above can be
    filled in as the script grows.
    """
    return sorted(_UNKNOWN_LATIN)


def to_speech_text(caption: str) -> str:
    """Rewrite a caption into something espeak-ng reads in one Korean voice."""
    if not caption.strip():
        return caption

    text = _LATIN_RE.sub(lambda m: _latin_to_hangul(m.group(0)), caption)

    def replace_number(match: re.Match[str]) -> str:
        digits = match.group(1).replace(",", "")
        decimals = match.group(2) or ""
        trailing = match.group(3) or ""
        # The counter is the first syllable of what follows; the rest is
        # ordinary text and has to survive untouched.
        counter = ""
        for length in (2, 1):
            if trailing[:length] in _NATIVE_COUNTERS:
                counter = trailing[:length]
                break
        spoken = _read_number(digits, decimals, counter)
        return f"{spoken} {trailing}" if trailing else spoken

    text = _NUMBER_RE.sub(replace_number, text)

    for symbol, spoken in _SYMBOLS.items():
        text = text.replace(symbol, spoken)

    return re.sub(r"\s{2,}", " ", text).strip()
