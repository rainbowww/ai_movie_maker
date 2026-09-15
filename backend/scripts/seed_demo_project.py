"""Seed CONCEPT 1 — 두 사람 진행 (two-host dialogue).

A 13-scene Korean adaptation of an AI-music-video-making tutorial
(Treblo → Claude → Google Flow → CapCut), rewritten as a conversation
between a male and a female presenter.

    cd backend && python -m scripts.seed_demo_project

Writes project.json only (script + image prompts + cue positions). It does
NOT call Gemini — run "전체 생성" in the UI (or POST
/api/projects/{id}/generate-all) afterwards to produce images and audio.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.models import CueCircle, Project, ProjectStore, Scene  # noqa: E402
from scripts._scene_library import cue, visual  # noqa: E402

PROJECT_ID = "demo-2host"

# (chapter, speaker, caption, visual key, cue key)
RAW_SCENES = [
    ("오프닝", "m",
     "이 뮤직비디오, 어떻게 만들었을 것 같으세요?",
     "hook_rooftop", None),
    ("오프닝", "f",
     "믿기지 않으시겠지만, 이 영상 전부 단 한 푼도 안 들이고 만들어졌어요.",
     "host_f", None),
    ("오프닝", "m",
     "카메라도, 밴드도, 악기도, 편집 경험도 전혀 필요 없습니다.",
     "host_m", None),
    ("오프닝", "f",
     "무료 AI 툴 몇 개랑, 오후 시간 한나절이면 충분해요. 지금부터 순서대로 알려드릴게요.",
     "host_f_gesturing", None),
    ("Treblo로 작곡하기", "m",
     "가장 먼저 필요한 건 노래예요. 여기서는 무료 AI 음악 생성기, 트레블로를 사용합니다.",
     "host_m_pointing", None),
    ("Treblo로 작곡하기", "f",
     "로그인하면 이런 화면이 나와요. 프롬프트 입력창에 원하는 곡 설명을 적고 생성 버튼을 누르면, "
     "몇 초 뒤 두 개의 곡이 완성돼요.",
     "treblo_simple", "treblo_generate"),
    ("Treblo로 작곡하기", "m",
     "다만 심플 모드에서는 세밀한 설정이 어려워서, 어드밴스드 모드로 넘어가면 스타일 태그와 슬라이더로 "
     "더 정교하게 다듬을 수 있어요. 저는 가사와 세부 설정을 클로드에게 미리 만들어달라고 부탁했어요.",
     "treblo_advanced", "treblo_sliders"),
    ("Treblo로 작곡하기", "f",
     "클로드가 만들어준 스타일과 가사를 붙여넣고 조절하면, 이번엔 훨씬 완성도 높은 곡이 나와요. "
     "노래는 준비됐고, 이제 뮤직비디오를 만들 차례예요.",
     "treblo_results", None),
    ("Claude로 스토리 만들기", "m",
     "저는 클로드와 미리 준비한 마스터 프롬프트를 사용할 거예요. 붙여넣고 가사를 입력해서 전송하면, "
     "클로드가 스토리를 만들어주고, 마음에 들면 확인이라고 입력해요. 그러면 등장인물과 장소, 각 장면의 "
     "이미지 프롬프트까지 전부 만들어줍니다.",
     "claude_chat", "claude_input"),
    ("Google Flow로 장면 만들기", "f",
     "이 장면들을 실제로 만들려면 구글 플로우를 사용해요. 프로젝트를 만들고 이미지 모드와 비율을 설정한 "
     "다음, 캐릭터와 장소 프롬프트를 붙여넣고 생성을 누르면, 필요한 이미지가 전부 준비돼요.",
     "flow_image", "flow_generate"),
    ("Google Flow로 장면 만들기", "m",
     "이제 설정에서 비디오 모드로 바꾸고, 방금 만든 이미지를 레퍼런스로 지정해요. 장면별 프롬프트를 넣고 "
     "생성을 누르면, 같은 방법으로 모든 장면을 하나씩 완성해서 저장할 수 있어요.",
     "flow_video", "flow_video_generate"),
    ("CapCut으로 완성하기", "f",
     "마지막으로 캡컷을 열어서 모든 클립과 음원을 불러오고, 타임라인에 배치한 다음 전환 효과를 더해줘요. "
     "내보내기 버튼만 누르면, 완성된 뮤직비디오가 나옵니다.",
     "capcut", "capcut_export"),
    ("마무리", "f",
     "이 영상이 도움이 되셨다면 좋아요와 구독 부탁드려요. 다음 영상에서 만나요!",
     "outro_two_hosts", None),
]


def build_project() -> Project:
    scenes = [
        Scene(
            order=i,
            chapter=chapter,
            speaker=speaker,
            caption=caption,
            image_prompt=visual(visual_key),
            visual_key=visual_key,
            cue=cue(cue_key) if cue_key else CueCircle(),
        )
        for i, (chapter, speaker, caption, visual_key, cue_key) in enumerate(RAW_SCENES)
    ]
    return Project(
        id=PROJECT_ID,
        title="컨셉 1 · 두 사람 진행 (0원 뮤비 만들기)",
        voice_m="Puck",
        voice_f="Kore",
        scenes=scenes,
    )


def main() -> None:
    store = ProjectStore(get_settings().storage_dir)
    project = store.save(build_project())
    print(f"[seed] 컨셉 1(2인 진행) 저장 완료: id={project.id}, 장면 수={len(project.scenes)}")


if __name__ == "__main__":
    main()
