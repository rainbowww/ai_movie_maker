"""Seed CONCEPT 2 — 1인칭 단독 진행 (solo first-person narration).

Same tutorial, but told the way the source video tells it: one narrator,
first person, walking through each step in order. Finer-grained than the
two-host version (28 scenes vs 13) so the pacing tracks the original more
closely.

The narration is an original Korean adaptation of the workflow — it
paraphrases the steps rather than transcribing the source video, and it
does not reproduce the song lyrics heard in the source video's opening.

    cd backend && python -m scripts.seed_solo_project
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.models import CueCircle, Project, ProjectStore, Scene  # noqa: E402
from scripts._scene_library import cue, visual  # noqa: E402

PROJECT_ID = "demo-solo"

# (chapter, caption, visual key, cue key) — 화자는 전부 1인칭 단독 진행자
RAW_SCENES = [
    ("오프닝",
     "방금 보신 이 뮤직비디오, 저는 단 한 푼도 쓰지 않고 만들었습니다.",
     "hook_rooftop", None),
    ("오프닝",
     "카메라도, 밴드도, 악기도, 편집 경험도 필요하지 않았습니다.",
     "host_m", None),
    ("오프닝",
     "무료 AI 도구 몇 개와 반나절이면 충분합니다. 지금부터 순서대로 보여드리겠습니다.",
     "host_m_pointing", None),
    ("Treblo로 작곡하기",
     "가장 먼저 필요한 건 노래입니다. 저는 무료 AI 작곡 도구인 트레블로를 사용했습니다.",
     "host_m", None),
    ("Treblo로 작곡하기",
     "로그인하면 이런 화면이 나옵니다. 여기 프롬프트 입력창에 원하는 곡을 설명해 주세요.",
     "treblo_simple", "treblo_prompt_box"),
    ("Treblo로 작곡하기",
     "저는 첫눈에 반한 사랑에 대한 90년대 인디팝이라고 적고, 생성 버튼을 눌렀습니다.",
     "treblo_simple", "treblo_generate"),
    ("Treblo로 작곡하기",
     "잠시 기다리면 두 곡이 만들어집니다. 둘 다 들어보고 마음에 드는 쪽을 고르면 됩니다.",
     "treblo_results", None),
    ("Treblo로 작곡하기",
     "다만 심플 모드로는 곡의 방향을 세밀하게 잡기 어렵습니다. 그래서 어드밴스드 모드로 넘어갑니다.",
     "treblo_advanced", "treblo_advanced_tab"),
    ("Treblo로 작곡하기",
     "여기서는 스타일 태그를 직접 고르거나, 원하는 장르를 직접 입력할 수 있습니다.",
     "treblo_advanced", "treblo_style_tags"),
    ("Treblo로 작곡하기",
     "가사와 세부 설정은 클로드에게 미리 만들어 달라고 요청해 두었습니다.",
     "claude_chat", None),
    ("Treblo로 작곡하기",
     "만들어진 스타일과 가사를 각각 붙여넣고, 스타일 강도와 곡 길이를 조절합니다.",
     "treblo_advanced", "treblo_sliders"),
    ("Treblo로 작곡하기",
     "이번에는 훨씬 완성도 높은 곡 두 개가 나왔습니다. 노래는 이걸로 준비되었습니다.",
     "treblo_results", None),
    ("Claude로 스토리 만들기",
     "이제 이 곡을 뮤직비디오로 만들 차례입니다.",
     "host_m", None),
    ("Claude로 스토리 만들기",
     "저는 미리 준비해 둔 마스터 프롬프트를 사용합니다. 이 프롬프트는 설명란에 함께 올려두겠습니다.",
     "host_m_pointing", None),
    ("Claude로 스토리 만들기",
     "마스터 프롬프트를 붙여넣으면 가사를 물어봅니다. 가사를 입력하고 전송하세요.",
     "claude_chat", "claude_input"),
    ("Claude로 스토리 만들기",
     "그러면 가사를 분석해서 이야기 구성을 만들어 줍니다. 마음에 들면 확인이라고 입력합니다.",
     "claude_chat", None),
    ("Claude로 스토리 만들기",
     "등장인물과 장소, 장면별 이미지 프롬프트까지 한 번에 정리해 줍니다. 내용을 한 번 훑어보세요.",
     "claude_storyplan", None),
    ("Google Flow로 장면 만들기",
     "이 장면들을 실제 이미지로 만들 차례입니다. 저는 구글 플로우를 사용했습니다.",
     "host_m", None),
    ("Google Flow로 장면 만들기",
     "프로젝트를 만들고 이미지 모드와 화면 비율을 설정한 다음, 캐릭터 프롬프트를 붙여넣고 생성을 누릅니다.",
     "flow_image", "flow_generate"),
    ("Google Flow로 장면 만들기",
     "같은 방식으로 장소 이미지도 만듭니다. 프롬프트만 바꿔서 반복하면 됩니다.",
     "flow_image", "flow_generate"),
    ("Google Flow로 장면 만들기",
     "필요한 이미지가 모두 준비됐습니다. 나중에 찾기 쉽도록 이름도 정리해 둡니다.",
     "flow_gallery", None),
    ("Google Flow로 장면 만들기",
     "이제 설정을 비디오 모드로 바꾸고, 방금 만든 이미지를 레퍼런스로 지정합니다.",
     "flow_video", "flow_reference"),
    ("Google Flow로 장면 만들기",
     "장면 프롬프트를 넣고 레퍼런스를 추가한 뒤 생성을 누르면, 첫 장면이 완성됩니다.",
     "flow_video", "flow_video_generate"),
    ("Google Flow로 장면 만들기",
     "같은 방법으로 나머지 장면도 하나씩 만들고, 클립을 전부 저장합니다.",
     "flow_video", None),
    ("CapCut으로 완성하기",
     "마지막으로 캡컷에서 모든 클립과 음원을 불러와 타임라인에 배치합니다.",
     "capcut", "capcut_timeline"),
    ("CapCut으로 완성하기",
     "전환 효과를 더하고 내보내기를 누르면, 뮤직비디오가 완성됩니다.",
     "capcut", "capcut_export"),
    ("마무리",
     "이렇게 완성된 결과물입니다. 여기까지 들어간 비용은 0원이었습니다.",
     "final_montage", None),
    ("마무리",
     "도움이 되셨다면 좋아요와 구독 부탁드립니다. 다음 영상에서 뵙겠습니다.",
     "outro_solo", None),
]


def build_project() -> Project:
    scenes = [
        Scene(
            order=i,
            chapter=chapter,
            speaker="m",  # 단독 진행: 모든 장면이 같은 목소리
            caption=caption,
            image_prompt=visual(visual_key),
            cue=cue(cue_key) if cue_key else CueCircle(),
        )
        for i, (chapter, caption, visual_key, cue_key) in enumerate(RAW_SCENES)
    ]
    return Project(
        id=PROJECT_ID,
        title="컨셉 2 · 1인칭 단독 진행 (0원 뮤비 만들기)",
        voice_m="Puck",
        voice_f="Kore",  # 사용되지 않지만 스키마상 유지
        scenes=scenes,
    )


def main() -> None:
    store = ProjectStore(get_settings().storage_dir)
    project = store.save(build_project())
    print(f"[seed] 컨셉 2(1인칭 단독) 저장 완료: id={project.id}, 장면 수={len(project.scenes)}")


if __name__ == "__main__":
    main()
