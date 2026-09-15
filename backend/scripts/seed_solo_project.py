"""Seed CONCEPT 2 — 1인칭 단독 진행 (solo first-person narration).

원본 영상의 35개 장면 구조를 그대로 따라갑니다. 원본에서 진행자가 말한
대목마다 한국어 대사가 1:1로 대응하고, 말이 없는 대목(오프닝 음악, 로고
스팅, 마지막 몽타주)은 대사 없이 원본과 같은 길이만큼 화면을 유지합니다.
각 장면에는 원본 타임코드가 붙어 있어 완성본을 원본과 나란히 대조할 수
있습니다.

대사는 원본 진행자의 말을 한국어로 옮긴 것이며, 발화 순서·개수·내용을
바꾸지 않았습니다. 다만 오프닝에 흐르는 노래 가사는 옮기지 않았습니다.

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

# (원본 타임코드, 챕터, 한국어 대사, 화면 키, 빨간원 키, 대사 없을 때 유지 시간)
RAW_SCENES: list[tuple[str, str, str, str, str | None, float | None]] = [
    ("0:00-0:02", "오프닝 (완성본 미리보기)", "",
     "hook_rooftop", None, 2.0),
    ("0:02-0:04", "오프닝 (완성본 미리보기)", "",
     "hook_fireflies", None, 2.0),
    ("0:04-0:05", "오프닝 (완성본 미리보기)", "",
     "hook_skyline_gaze", None, 1.0),
    ("0:05-0:11", "오프닝 (완성본 미리보기)", "",
     "hook_street_run", None, 6.0),
    ("0:11-0:14", "오프닝 (완성본 미리보기)", "",
     "hook_light_particles", None, 3.0),

    ("0:14-0:16", "도입", "방금 보신 이 뮤직비디오 전부, 저는 0원으로 만들었습니다.",
     "host_m", None, None),
    ("0:16-0:20", "도입", "카메라도, 밴드도, 악기도, 편집 경험도 필요 없습니다.",
     "host_m", None, None),
    ("0:20-0:28", "도입",
     "무료 AI 도구 몇 개와 반나절 정도면 됩니다. 이 영상에서 처음부터 끝까지 순서대로 "
     "보여드리겠습니다. 바로 시작하죠.",
     "host_m_laptop", None, None),
    ("0:28-0:33", "도입", "",
     "logo_sting", None, 5.0),

    ("0:33-0:37", "Treblo로 작곡하기", "가장 먼저 필요한 건 노래입니다. 그리고 그건 트레블로를 사용합니다.",
     "host_m_pointing", None, None),
    ("0:37-0:56", "Treblo로 작곡하기",
     "100% 무료 AI 음악·작곡 생성기입니다. 로그인하고 나면 화면이 이렇게 나옵니다.",
     "treblo_home", None, None),
    ("0:56-1:23", "Treblo로 작곡하기",
     "여기가 프롬프트 입력창입니다. 예를 들어 저는 '첫눈에 반한 사랑에 대한 90년대 인디팝 곡'이라고 "
     "입력합니다. 이제 생성 버튼만 누르면 됩니다.",
     "treblo_simple", "treblo_generate", None),
    ("1:23-1:43", "Treblo로 작곡하기", "두 곡이 모두 준비됐습니다. 한번 들어보겠습니다.",
     "treblo_results", None, None),
    ("1:43-2:00", "Treblo로 작곡하기",
     "심플 모드에서는 곡의 방향을 지시할 수 없습니다. 그렇게 하려면 어드밴스드 모드를 써야 합니다.",
     "treblo_advanced", "treblo_advanced_tab", None),
    ("2:00-2:11", "Treblo로 작곡하기",
     "먼저 스타일 태그가 있습니다. 여기서 하나 고르셔도 되고, 직접 입력하셔도 됩니다.",
     "treblo_advanced", "treblo_style_tags", None),
    ("2:11-2:23", "Treblo로 작곡하기",
     "이 곡은 가사와 기술적인 설정을 이미 클로드로 만들어 두었습니다.",
     "claude_chat", None, None),
    ("2:23-2:54", "Treblo로 작곡하기",
     "스타일을 복사해서 여기에 붙여넣습니다. 가사 항목으로 와서 가사를 입력합니다. 마지막으로 "
     "스타일 강도와 길이 같은 것을 선택할 수 있습니다.",
     "treblo_advanced", "treblo_sliders", None),
    ("2:54-3:39", "Treblo로 작곡하기", "이번에도 두 곡이 생성됐습니다.",
     "treblo_results", None, None),

    ("3:39-3:52", "Claude로 스토리 만들기",
     "노래를 얻었습니다. 이제 이 곡을 뮤직비디오로 만들 차례입니다.",
     "host_m", None, None),
    ("3:52-4:02", "Claude로 스토리 만들기",
     "저는 클로드와 이 마스터 프롬프트를 사용하겠습니다. 이건 설명란에 올려두겠습니다.",
     "master_prompt_card", None, None),
    ("4:02-4:27", "Claude로 스토리 만들기",
     "마스터 프롬프트를 챗 모델에 붙여넣습니다. 그러면 곡의 가사를 물어봅니다. 가사를 입력하고 "
     "전송을 누릅니다.",
     "claude_chat", "claude_input", None),
    ("4:27-4:57", "Claude로 스토리 만들기",
     "AI가 가사를 분석해서 이야기를 만들기 시작합니다. 마음에 드시면 '확인'이라고 입력하면 됩니다.",
     "claude_chat", None, None),
    ("4:57-5:29", "Claude로 스토리 만들기",
     "AI 모델이 핵심 요소를 전부 만들어 줍니다. 등장인물과 장소, 이미지 프롬프트를 만들어 줍니다. "
     "전부 한번 훑어보세요.",
     "claude_storyplan", None, None),

    ("5:29-5:39", "Google Flow로 장면 만들기",
     "이제 이걸 실제로 구현할 차례입니다. 그러기 위해 저는 구글 플로우를 사용하겠습니다.",
     "host_m_flow", None, None),
    ("5:39-6:01", "Google Flow로 장면 만들기",
     "프로젝트를 만듭니다. 이미지 모드와 화면 비율을 설정합니다. 첫 번째 캐릭터 프롬프트를 복사해서 "
     "생성을 누릅니다.",
     "flow_image", "flow_generate", None),
    ("6:01-6:21", "Google Flow로 장면 만들기",
     "두 번째 이미지를 만들겠습니다. 장소 프롬프트를 복사해서 생성을 누르기만 하면 됩니다.",
     "flow_image", "flow_generate", None),
    ("6:21-6:43", "Google Flow로 장면 만들기", "자, 여기 있습니다. 이미지가 전부 준비됐습니다.",
     "flow_gallery", None, None),
    ("6:43-7:01", "Google Flow로 장면 만들기",
     "이미지 이름을 전부 클로드가 정해준 대로 바꾸겠습니다. 나중에 맞는 재료를 찾을 때 도움이 되기 "
     "때문입니다.",
     "flow_rename", None, None),
    ("7:01-7:18", "Google Flow로 장면 만들기",
     "설정으로 가서 비디오 모드로 바꿉니다. 재료를 레퍼런스로 선택합니다.",
     "flow_video", "flow_reference", None),
    ("7:18-8:02", "Google Flow로 장면 만들기",
     "첫 번째 장면 프롬프트를 복사합니다. 재료를 추가합니다. 생성을 누릅니다. 완벽한 오프닝 샷입니다.",
     "flow_video", "flow_video_generate", None),
    ("8:02-8:24", "Google Flow로 장면 만들기", "이제 두 번째 장면을 만들겠습니다.",
     "flow_video", None, None),
    ("8:24-8:41", "Google Flow로 장면 만들기",
     "같은 방법으로 나머지 장면을 전부 만듭니다. 영상 클립을 모두 저장합니다.",
     "flow_gallery", None, None),

    ("8:41-9:10", "CapCut으로 완성하기",
     "클립과 노래를 전부 불러옵니다. 순서대로 배치합니다. 효과와 전환을 넣습니다. 영상을 내보냅니다.",
     "capcut", "capcut_export", None),

    ("9:10-9:49", "완성본", "",
     "final_montage", None, 39.0),
    ("9:49-10:04", "마무리",
     "이 영상이 도움이 되셨다면 좋아요를 눌러주시고, 더 좋은 튜토리얼을 위해 구독해 주세요. "
     "시청해 주셔서 감사합니다. 다음 영상에서 뵙겠습니다.",
     "outro_solo", None, None),
]


def build_project() -> Project:
    scenes = [
        Scene(
            order=i,
            chapter=chapter,
            speaker="m",  # 단독 진행: 모든 장면이 같은 목소리
            caption=caption,
            image_prompt=visual(visual_key),
            visual_key=visual_key,
            cue=cue(cue_key) if cue_key else CueCircle(),
            source_timecode=timecode,
            hold_seconds=hold,
        )
        for i, (timecode, chapter, caption, visual_key, cue_key, hold) in enumerate(RAW_SCENES)
    ]
    return Project(
        id=PROJECT_ID,
        title="컨셉 2 · 1인칭 단독 진행 (원본 35장면 1:1)",
        voice_m="Puck",
        voice_f="Kore",  # 사용되지 않지만 스키마상 유지
        scenes=scenes,
    )


def main() -> None:
    store = ProjectStore(get_settings().storage_dir)
    project = store.save(build_project())
    spoken = sum(1 for s in project.scenes if s.caption.strip())
    print(f"[seed] 컨셉 2(1인칭 단독) 저장 완료: id={project.id}, 장면 {len(project.scenes)}개")
    print(f"[seed] 대사 있는 장면 {spoken}개 / 무대사(음악·로고·몽타주) {len(project.scenes) - spoken}개")


if __name__ == "__main__":
    main()
