"""Shared visual vocabulary for the seed projects.

Both concepts (two-host dialogue, solo first-person narration) walk through
the same tool screens, so the image prompts and click-cue positions live
here once instead of being duplicated per script.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.models import CueCircle  # noqa: E402

STYLE = (
    "Modern flat vector illustration, clean lines, soft gradient background, "
    "cohesive indigo-purple-teal palette, tutorial explainer video aesthetic, "
    "no photorealism, no readable long paragraphs of text, 16:9."
)

# Reusable screen / character illustrations, keyed by a short name.
VISUALS: dict[str, str] = {
    "hook_rooftop": (
        f"{STYLE} A young woman lies on a gravel rooftop at night, city lights "
        "and a starry sky behind her, soft bokeh, dreamy cinematic mood."
    ),
    "hook_fireflies": (
        f"{STYLE} Close-up of an open palm with glowing fireflies landing on it, "
        "dim cool-toned light, gravel background."
    ),
    "hook_skyline_gaze": (
        f"{STYLE} Profile view of a young woman looking out over a city skyline "
        "at night, warm yellow bokeh lights, dark sky."
    ),
    "hook_street_run": (
        f"{STYLE} A young woman runs down a European-style street lined with "
        "brick buildings and warm string lights, laughing, cinematic warm light."
    ),
    "hook_light_particles": (
        f"{STYLE} A young woman stands still in a street with her arms wide open, "
        "swirling golden light particles around her, warm glow."
    ),
    "logo_sting": (
        f"{STYLE} Fast-paced abstract composition of mechanical and digital shapes "
        "assembling into a simple robot-head logo, dark background, vibrant accents."
    ),
    "host_m_laptop": (
        f"{STYLE} Friendly young male presenter with hands resting on an open "
        "laptop, blue background with vertical light bars, facing camera."
    ),
    "host_m_flow": (
        f"{STYLE} Friendly young male presenter speaking to camera with a floating "
        "graphic card beside him, blue neon gradient studio."
    ),
    "treblo_home": (
        f"{STYLE} Mockup of a dark-themed AI music generator homepage: hero banner, "
        "feature highlight cards and a pricing row, minimal browser window chrome."
    ),
    "master_prompt_card": (
        f"{STYLE} A floating document card labelled with a prompt icon hovering "
        "beside a presenter's hand, dark background with soft glow."
    ),
    "flow_rename": (
        f"{STYLE} Mockup of an asset list where thumbnails are being renamed to "
        "short labels, an inline text field active, dark theme browser chrome."
    ),
    "host_f": (
        f"{STYLE} Friendly young female presenter character, warm smile, casual "
        "smart outfit, standing in a soft pink-teal gradient studio, facing camera."
    ),
    "host_f_gesturing": (
        f"{STYLE} The same friendly female presenter, gesturing enthusiastically "
        "while presenting, pink-teal gradient studio background."
    ),
    "host_m": (
        f"{STYLE} Friendly young male presenter character, short hair, glasses, "
        "light beard, grey t-shirt, standing in a blue neon gradient studio, facing camera."
    ),
    "host_m_pointing": (
        f"{STYLE} The same male presenter, pointing toward an off-screen laptop, "
        "blue gradient studio background."
    ),
    "treblo_simple": (
        f"{STYLE} Mockup of a dark-themed AI music generator web app: a large "
        "text prompt input box and a rounded 'Generate' button below it, minimal "
        "browser window chrome."
    ),
    "treblo_advanced": (
        f"{STYLE} Mockup of a dark-themed music app 'advanced mode': a row of "
        "genre style tag chips and two labeled horizontal sliders (Style Strength, "
        "Duration), minimal browser window chrome."
    ),
    "treblo_results": (
        f"{STYLE} Mockup of a music app results screen: two song result cards, "
        "each with a play button icon and waveform bars, minimal browser window chrome."
    ),
    "claude_chat": (
        f"{STYLE} Mockup of a minimalist AI chat assistant interface: chat bubble "
        "conversation on the left, a text input bar with a send icon at the bottom, "
        "warm orange accent color, minimal browser window chrome."
    ),
    "claude_storyplan": (
        f"{STYLE} Mockup of an AI chat assistant output panel: a small character "
        "portrait thumbnail, a few location thumbnail icons, and a short list of "
        "prompt cards, warm orange accent color."
    ),
    "flow_image": (
        f"{STYLE} Mockup of an AI image-generation studio interface: left settings "
        "sidebar with toggle switches, large central canvas with a generated portrait "
        "thumbnail, a prominent 'Generate' button, minimal browser window chrome."
    ),
    "flow_gallery": (
        f"{STYLE} Mockup of an image gallery grid with eight generated thumbnails "
        "of a character and city locations, dark theme, minimal browser window chrome."
    ),
    "flow_video": (
        f"{STYLE} Mockup of an AI video-generation studio interface: a row of small "
        "reference thumbnail icons on the side, a large central video preview frame "
        "with a play icon, a prominent 'Generate' button, minimal browser window chrome."
    ),
    "capcut": (
        f"{STYLE} Mockup of a desktop video editor interface: a horizontal timeline "
        "at the bottom with colored clip blocks and a waveform track, a highlighted "
        "'Export' button in the top-right corner, minimal window chrome."
    ),
    "final_montage": (
        f"{STYLE} A four-panel montage of finished music video frames: a rooftop at "
        "night, a rain-slicked city street, warm string lights, and a silhouette "
        "against city lights."
    ),
    "outro_two_hosts": (
        f"{STYLE} Two friendly presenter characters (one male, one female, matching "
        "earlier descriptions) standing together, waving and smiling at the camera "
        "with a thumbs-up gesture, warm gradient background with small heart and "
        "bell icon shapes."
    ),
    "outro_solo": (
        f"{STYLE} The friendly male presenter waving goodbye at the camera with a "
        "thumbs-up, warm gradient background with small heart and bell icon shapes."
    ),
}

# Where the red "click here" circle goes on each screen (normalized 0-1).
#
# These are derived from the exact pixel coordinates the mockups in
# app/services/mockups.py draw their controls at, on the 1280x720 content
# canvas — so the circle lands on the control it points at, not near it.
# If you move a control in mockups.py, move its cue here too.
#
# A cue points at one control. Past roughly r=0.2 it stops pointing and
# starts enclosing half the screen, which tells the viewer nothing — so a
# target that is really a region (a timeline, a text area) gets a circle on
# its middle rather than a circle around the whole of it.
CUES: dict[str, CueCircle] = {
    # treblo_simple: prompt box 110-1170 x 160-400; 생성 button at (640, 548)
    "treblo_prompt_box": CueCircle(enabled=True, x=0.500, y=0.389, r=0.19),
    "treblo_generate": CueCircle(enabled=True, x=0.500, y=0.761, r=0.13),
    # treblo_advanced: "Advanced" tab at (210,100); chips row y 250-288;
    # sliders at y 400 and 500 spanning x 110-1170, knob at 68% of the track
    "treblo_advanced_tab": CueCircle(enabled=True, x=0.199, y=0.153, r=0.075),
    "treblo_style_tags": CueCircle(enabled=True, x=0.260, y=0.374, r=0.145),
    # The Style Strength knob — the part you actually drag. This was r=0.30
    # centred between the two sliders: a 384px radius on a 720px-tall canvas,
    # so it ran off both edges and pointed at nothing in particular.
    "treblo_sliders": CueCircle(enabled=True, x=0.648, y=0.563, r=0.10),
    # claude_chat: input bar 110-1070 x 580-640
    "claude_input": CueCircle(enabled=True, x=0.461, y=0.847, r=0.20),
    # flow_image: 생성 button at (640, 600)
    "flow_generate": CueCircle(enabled=True, x=0.500, y=0.833, r=0.13),
    # flow_video: first ingredient thumb 110-240 x 145-275; 생성 at (640, 610)
    "flow_reference": CueCircle(enabled=True, x=0.137, y=0.292, r=0.095),
    "flow_video_generate": CueCircle(enabled=True, x=0.500, y=0.847, r=0.13),
    # capcut: clip lane y 470-546 across x 100-1170; 내보내기 at (1063, 88)
    "capcut_timeline": CueCircle(enabled=True, x=0.500, y=0.706, r=0.14),
    "capcut_export": CueCircle(enabled=True, x=0.830, y=0.122, r=0.105),
}


def visual(name: str) -> str:
    return VISUALS[name]


def cue(name: str | None) -> CueCircle:
    return CUES[name] if name else CueCircle()
