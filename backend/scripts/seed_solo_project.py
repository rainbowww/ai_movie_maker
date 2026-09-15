"""Seed CONCEPT 2 — 1인칭 단독 진행 (solo first-person narration).

원본 영상의 38개 장면을 그대로 따라갑니다. 진행자가 말한 대목마다 한국어
대사가 1:1로 대응하고, 말이 없는 대목(오프닝 음악, 로고 스팅, 마지막
몽타주)은 대사 없이 원본과 같은 길이만큼 화면을 유지합니다. 각 장면에
원본 타임코드가 붙어 있어 완성본을 원본과 나란히 대조할 수 있습니다.

대사는 원본 진행자가 실제로 한 말을 한국어로 옮긴 것입니다. 발화 순서와
개수, 내용을 바꾸지 않았고, 원본이 한 문장에서 한 말은 한 장면 안에
들어갑니다. 오프닝에 흐르는 노래 가사는 옮기지 않았습니다.

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
    # ── 오프닝: 완성된 뮤직비디오 미리보기 (진행자 말 없음) ──────────────
    ("0:00-0:01", "오프닝 (완성본 미리보기)", "", "hook_rooftop", None, 1.0),
    ("0:01-0:02", "오프닝 (완성본 미리보기)", "", "hook_light_particles", None, 1.0),
    ("0:02-0:03", "오프닝 (완성본 미리보기)", "", "hook_fireflies", None, 1.0),
    ("0:03-0:05", "오프닝 (완성본 미리보기)", "", "hook_skyline_gaze", None, 2.0),
    ("0:05-0:11", "오프닝 (완성본 미리보기)", "", "hook_street_run", None, 6.0),
    ("0:11-0:15", "오프닝 (완성본 미리보기)", "", "hook_light_particles", None, 4.0),

    # ── 도입 ────────────────────────────────────────────────────────────
    ("0:15-0:28", "도입",
     "방금 보신 저 뮤직비디오 전부, 저는 0원으로 만들었습니다. 카메라도, 밴드도, 악기도, "
     "편집 경험도 필요 없습니다. 무료 AI 도구 몇 개와 반나절 정도면 됩니다.",
     "host_m", None, None),
    ("0:28-0:33", "도입", "", "logo_sting", None, 5.0),

    # ── Treblo로 작곡하기 ───────────────────────────────────────────────
    ("0:33-0:37", "Treblo로 작곡하기",
     "가장 먼저 필요한 건 노래입니다. 그리고 그건 트레블로를 사용합니다.",
     "host_m_laptop", None, None),
    ("0:38-0:42", "Treblo로 작곡하기",
     "100% 무료 AI 음악·작곡 생성기입니다.",
     "treblo_home", None, None),
    ("0:42-0:56", "Treblo로 작곡하기",
     "로그인하고 나면 화면이 이렇게 나옵니다. 여기가 아이디어를 입력하는 프롬프트 "
     "입력창입니다. 아래쪽에는 인기곡이 나옵니다.",
     "treblo_simple", "treblo_prompt_box", None),
    ("0:56-1:10", "Treblo로 작곡하기",
     "곡을 만드는 방법은 두 가지입니다. 심플과 어드밴스드. 아이디어만 있으시면 심플을 "
     "쓰세요. 곡 아이디어를 입력하고 생성을 누릅니다.",
     "treblo_simple", "treblo_generate", None),
    ("1:10-1:22", "Treblo로 작곡하기",
     "예를 들어 저는 '첫눈에 반한 사랑에 대한 90년대 인디팝 곡'이라고 입력하겠습니다. "
     "두 개의 곡이 생성되고 있습니다.",
     "treblo_simple", None, None),
    ("1:23-1:42", "Treblo로 작곡하기", "", "treblo_results", None, 19.0),
    ("1:43-1:51", "Treblo로 작곡하기",
     "두 곡 다 정말 괜찮습니다. 하지만 심플 모드에서는 곡의 방향을 지시하거나 원하는 "
     "것을 정확히 얻을 수 없습니다.",
     "host_m", None, None),
    ("1:52-2:11", "Treblo로 작곡하기",
     "어드밴스드 모드를 써야 합니다. 여기서는 설정과 가사를 입력할 수 있습니다. 먼저 "
     "스타일 태그가 있습니다. 원하는 스타일을 고르셔도 되고, 직접 입력하셔도 됩니다.",
     "treblo_advanced", "treblo_style_tags", None),
    ("2:12-2:29", "Treblo로 작곡하기",
     "가사와 기술적인 설정은 이미 클로드로 만들어 뒀습니다. 이걸 복사해서 트레블로에 "
     "붙여넣겠습니다.",
     "claude_chat", None, None),
    ("2:30-2:56", "Treblo로 작곡하기",
     "가사 항목에는 세 가지 선택지가 있습니다. 오토, 커스텀, 그리고 연주곡용 논. "
     "저는 여기에 제 가사를 입력하겠습니다.",
     "treblo_advanced", "treblo_lyrics", None),
    ("2:57-3:00", "Treblo로 작곡하기",
     "설정을 전부 맞추고 생성 버튼을 누릅니다. 두 곡이 생성되고 있습니다.",
     "treblo_advanced", "treblo_advanced_generate", None),
    ("3:01-3:39", "Treblo로 작곡하기", "", "treblo_results", None, 38.0),

    # ── Claude로 스토리 만들기 ──────────────────────────────────────────
    ("3:40-4:00", "Claude로 스토리 만들기",
     "이제 이 곡을 뮤직비디오로 만들 차례입니다. 등장인물과 사물을 일관되게 유지해야 "
     "하기 때문에, 저는 클로드와 마스터 프롬프트를 사용하겠습니다.",
     "host_m_pointing", None, None),
    ("4:01-4:17", "Claude로 스토리 만들기",
     "마스터 프롬프트를 복사해서 챗 모델에 붙여넣습니다. 그러면 가사와 영상 사양을 "
     "물어봅니다.",
     "master_prompt_card", None, None),
    ("4:18-4:41", "Claude로 스토리 만들기",
     "길이와 장르, 비주얼 스타일을 입력합니다. 그러면 언어 모델이 전부 분석해서 "
     "이야기를 만들어 줍니다.",
     "claude_chat", "claude_input", None),
    ("4:42-4:56", "Claude로 스토리 만들기",
     "여기 상세한 줄거리와 테마, 색 팔레트, 장면 계획이 나옵니다. 다음 단계로 넘어가려면 "
     "'확인'이라고 입력하세요.",
     "claude_storyplan", None, None),
    ("4:57-5:13", "Claude로 스토리 만들기",
     "AI가 핵심 요소를 만들어 줍니다. 등장인물과 장소, 이미지 프롬프트입니다. 확인하고 "
     "승인하세요.",
     "claude_storyplan", None, None),
    ("5:14-5:29", "Claude로 스토리 만들기",
     "이 단계에서는 모든 장면의 영상 프롬프트를 만들어 줍니다. 프롬프트마다 타임코드가 "
     "붙어 있어서 타임라인은 신경 쓰지 않아도 됩니다.",
     "claude_storyplan", None, None),

    # ── Google Flow로 영상 만들기 ───────────────────────────────────────
    ("5:30-5:39", "Google Flow로 영상 만들기",
     "이제 구글 플로우로 이걸 실제로 만들어 봅니다. 여기서는 이미지와 클립을 무제한으로, "
     "무료로 만들 수 있습니다.",
     "host_m_flow", None, None),
    ("5:40-6:00", "Google Flow로 영상 만들기",
     "프로젝트를 만듭니다. 이미지 모드와 화면 비율, AI 모델을 설정합니다. 클로드에서 첫 "
     "번째 캐릭터 프롬프트를 복사합니다.",
     "flow_image", "flow_generate", None),
    ("6:01-6:08", "Google Flow로 영상 만들기",
     "이걸 보세요. 우리 캐릭터입니다. 정말 훌륭합니다.",
     "flow_gallery", None, None),
    ("6:09-6:33", "Google Flow로 영상 만들기",
     "과정은 똑같습니다. 장소 프롬프트를 복사해서 생성합니다. 이제 등장인물과 장소, 소품 "
     "이미지가 전부 준비됐습니다.",
     "flow_image", "flow_generate", None),
    ("6:34-6:58", "Google Flow로 영상 만들기",
     "나중에 쉽게 찾을 수 있도록 클로드가 알려준 대로 이미지 이름을 바꿉니다. 모든 "
     "이미지에 대해 해 주세요.",
     "flow_rename", None, None),
    ("6:59-7:17", "Google Flow로 영상 만들기",
     "설정으로 가서 비디오 모드로 바꿉니다. 재료를 레퍼런스로 선택하고 비디오 모델도 "
     "고릅니다.",
     "flow_video", "flow_reference", None),
    ("7:18-7:51", "Google Flow로 영상 만들기",
     "장면 프롬프트를 붙여넣습니다. 프롬프트 안에서 @ 기호로 애셋 이름을 태그하면 맞는 "
     "이미지가 연결됩니다.",
     "flow_video", "flow_video_generate", None),
    ("7:52-8:02", "Google Flow로 영상 만들기",
     "제 곡에 딱 맞는 완벽한 오프닝 샷입니다.",
     "final_montage", None, None),
    ("8:03-8:41", "Google Flow로 영상 만들기",
     "같은 방법으로 나머지 장면을 전부 만듭니다. 다 되면 기기에 저장하세요.",
     "flow_video", None, None),

    # ── 편집과 마무리 ───────────────────────────────────────────────────
    ("8:42-9:05", "편집과 마무리",
     "클립과 노래를 영상 편집기로 불러옵니다. 순서대로 배치하고, 클립의 원본 오디오는 "
     "음소거한 다음, 전환이나 효과를 넣습니다.",
     "capcut", "capcut_timeline", None),
    ("9:06-9:44", "편집과 마무리", "", "final_montage", None, 38.0),
    ("9:45-10:04", "편집과 마무리",
     "이제 직접 만들어 보세요. 링크는 전부 설명란에 있습니다. 더 많은 튜토리얼을 "
     "원하시면 좋아요와 구독 부탁드립니다. 시청해 주셔서 감사합니다!",
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
