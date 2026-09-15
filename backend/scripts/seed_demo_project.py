"""Seed the default demo project: a 13-scene Korean two-host adaptation of
an AI-music-video-making tutorial (Treblo -> Claude -> Google Flow ->
CapCut). Run once to create it; safe to re-run (overwrites by same id).

    cd backend && python -m scripts.seed_demo_project

This only writes project.json (script + image prompts + cue positions).
It does NOT call Gemini — run `POST /api/projects/{id}/generate-all` (or
click "전체 생성" in the frontend) afterwards to actually generate the
images and narration audio.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.models import CueCircle, Project, ProjectStore, Scene  # noqa: E402

DEMO_PROJECT_ID = "demo-mv-tutorial"

STYLE = (
    "Modern flat vector illustration, clean lines, soft gradient background, "
    "cohesive indigo-purple-teal palette, tutorial explainer video aesthetic, "
    "no photorealism, no readable long paragraphs of text, 16:9."
)

RAW_SCENES = [
    # (chapter, speaker, caption, image_prompt, cue)
    ("오프닝", "m",
     "이 뮤직비디오, 어떻게 만들었을 것 같으세요?",
     f"{STYLE} A young woman stands on a city rooftop at night, warm bokeh "
     "city lights behind her, dreamy cinematic mood.",
     None),
    ("오프닝", "f",
     "믿기지 않으시겠지만, 이 영상 전부 단 한 푼도 안 들이고 만들어졌어요.",
     f"{STYLE} Friendly young female presenter character, warm smile, casual "
     "smart outfit, standing in a soft pink-teal gradient studio, facing camera.",
     None),
    ("오프닝", "m",
     "카메라도, 밴드도, 악기도, 편집 경험도 전혀 필요 없습니다.",
     f"{STYLE} Friendly young male presenter character, short hair, glasses, "
     "light beard, grey t-shirt, standing in a blue neon gradient studio, facing camera.",
     None),
    ("오프닝", "f",
     "무료 AI 툴 몇 개랑, 오후 시간 한나절이면 충분해요. 지금부터 순서대로 알려드릴게요.",
     f"{STYLE} The same friendly female presenter, gesturing enthusiastically "
     "while presenting, pink-teal gradient studio background.",
     None),
    ("Treblo로 작곡하기", "m",
     "가장 먼저 필요한 건 노래예요. 여기서는 무료 AI 음악 생성기, 트레블로를 사용합니다.",
     f"{STYLE} The same male presenter, pointing toward an off-screen laptop, "
     "blue gradient studio background.",
     None),
    ("Treblo로 작곡하기", "f",
     "로그인하면 이런 화면이 나와요. 프롬프트 입력창에 원하는 곡 설명을 적고 생성 버튼을 누르면, "
     "몇 초 뒤 두 개의 곡이 완성돼요.",
     f"{STYLE} Mockup of a dark-themed AI music generator web app: a large "
     "text prompt input box and a rounded 'Generate' button below it, minimal "
     "browser window chrome.",
     CueCircle(enabled=True, x=0.5, y=0.76, r=0.13)),
    ("Treblo로 작곡하기", "m",
     "다만 심플 모드에서는 세밀한 설정이 어려워서, 어드밴스드 모드로 넘어가면 스타일 태그와 슬라이더로 "
     "더 정교하게 다듬을 수 있어요. 저는 가사와 세부 설정을 클로드에게 미리 만들어달라고 부탁했어요.",
     f"{STYLE} Mockup of a dark-themed music app 'advanced mode': a row of "
     "genre style tag chips and two labeled horizontal sliders (Style Strength, "
     "Duration), minimal browser window chrome.",
     CueCircle(enabled=True, x=0.5, y=0.68, r=0.28)),
    ("Treblo로 작곡하기", "f",
     "클로드가 만들어준 스타일과 가사를 붙여넣고 조절하면, 이번엔 훨씬 완성도 높은 곡이 나와요. "
     "노래는 준비됐고, 이제 뮤직비디오를 만들 차례예요.",
     f"{STYLE} Mockup of a music app results screen: two song result cards, "
     "each with a play button icon and waveform bars, minimal browser window chrome.",
     None),
    ("Claude로 스토리 만들기", "m",
     "저는 클로드와 미리 준비한 마스터 프롬프트를 사용할 거예요. 붙여넣고 가사를 입력해서 전송하면, "
     "클로드가 스토리를 만들어주고, 마음에 들면 확인이라고 입력해요. 그러면 등장인물과 장소, 각 장면의 "
     "이미지 프롬프트까지 전부 만들어줍니다.",
     f"{STYLE} Mockup of a minimalist AI chat assistant interface: chat bubble "
     "conversation on the left, a text input bar with a send icon at the bottom, "
     "warm orange accent color, minimal browser window chrome.",
     CueCircle(enabled=True, x=0.5, y=0.85, r=0.18)),
    ("Google Flow로 장면 만들기", "f",
     "이 장면들을 실제로 만들려면 구글 플로우를 사용해요. 프로젝트를 만들고 이미지 모드와 비율을 설정한 "
     "다음, 캐릭터와 장소 프롬프트를 붙여넣고 생성을 누르면, 필요한 이미지가 전부 준비돼요.",
     f"{STYLE} Mockup of an AI image-generation studio interface: left settings "
     "sidebar with toggle switches, large central canvas with a generated portrait "
     "thumbnail, a prominent 'Generate' button, minimal browser window chrome.",
     CueCircle(enabled=True, x=0.5, y=0.85, r=0.13)),
    ("Google Flow로 장면 만들기", "m",
     "이제 설정에서 비디오 모드로 바꾸고, 방금 만든 이미지를 레퍼런스로 지정해요. 장면별 프롬프트를 넣고 "
     "생성을 누르면, 같은 방법으로 모든 장면을 하나씩 완성해서 저장할 수 있어요.",
     f"{STYLE} Mockup of an AI video-generation studio interface: a row of small "
     "reference thumbnail icons on the side, a large central video preview frame "
     "with a play icon, a prominent 'Generate' button, minimal browser window chrome.",
     CueCircle(enabled=True, x=0.5, y=0.86, r=0.13)),
    ("CapCut으로 완성하기", "f",
     "마지막으로 캡컷을 열어서 모든 클립과 음원을 불러오고, 타임라인에 배치한 다음 전환 효과를 더해줘요. "
     "내보내기 버튼만 누르면, 완성된 뮤직비디오가 나옵니다.",
     f"{STYLE} Mockup of a desktop video editor interface: a horizontal timeline "
     "at the bottom with colored clip blocks and a waveform track, a highlighted "
     "'Export' button in the top-right corner, minimal window chrome.",
     CueCircle(enabled=True, x=0.83, y=0.18, r=0.12)),
    ("마무리", "f",
     "이 영상이 도움이 되셨다면 좋아요와 구독 부탁드려요. 다음 영상에서 만나요!",
     f"{STYLE} Two friendly presenter characters (one male, one female, matching "
     "earlier descriptions) standing together, waving and smiling at the camera "
     "with a thumbs-up gesture, warm gradient background with small heart and "
     "bell icon shapes.",
     None),
]


def build_project() -> Project:
    scenes = [
        Scene(
            order=i,
            chapter=chapter,
            speaker=speaker,
            caption=caption,
            image_prompt=image_prompt,
            cue=cue or CueCircle(),
        )
        for i, (chapter, speaker, caption, image_prompt, cue) in enumerate(RAW_SCENES)
    ]
    return Project(
        id=DEMO_PROJECT_ID,
        title="0원 뮤비 스튜디오 (예시 프로젝트)",
        voice_m="Puck",
        voice_f="Kore",
        scenes=scenes,
    )


def main() -> None:
    store = ProjectStore(get_settings().storage_dir)
    project = build_project()
    store.save(project)
    print(f"[seed] 프로젝트 저장 완료: id={project.id}, 장면 수={len(project.scenes)}")
    print(f"[seed] 경로: {get_settings().storage_dir / project.id / 'project.json'}")


if __name__ == "__main__":
    main()
