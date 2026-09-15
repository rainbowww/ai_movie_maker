"""Write the read-aloud script doc from the seeded project.

The doc and the seed say the same thing, so only one of them should be
typed by hand. It was the doc, and it drifted: the seed grew to 38 scenes
while the doc still claimed 35. Generating it means the two cannot
disagree again.

    cd backend && python -m scripts.write_script_doc demo-solo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.deps import get_store  # noqa: E402

DOC_BY_PROJECT = {
    "demo-solo": ("docs/script_solo_ko.md", "1인칭 단독 진행 대본 (한국어) — 원본 38장면 1:1"),
    "demo-2host": ("docs/script_2host_ko.md", "두 사람 진행 대본 (한국어)"),
}

SPEAKER_LABEL = {"m": "남", "f": "여"}


def escape(text: str) -> str:
    """Keep a caption from breaking out of its table cell."""
    return text.replace("|", "\\|").replace("\n", " ")


def build(project, title: str, two_speakers: bool) -> str:
    scenes = sorted(project.scenes, key=lambda s: s.order)
    spoken = [s for s in scenes if s.caption.strip()]
    silent = len(scenes) - len(spoken)
    last = scenes[-1].source_timecode.split("-")[-1] if scenes else "?"

    lines = [
        f"# {title}",
        "",
        "원본 영상의 장면 순서와 타임코드를 그대로 따릅니다. 진행자가 말한 대목마다",
        "한국어 대사가 하나씩 대응하고, 말이 없는 대목(오프닝 음악·로고 스팅·완성본",
        "몽타주)은 대사 없이 화면만 유지합니다.",
        "",
        "**읽는 법**: `대사` 칸을 그대로 읽으면 됩니다. `화면`은 그때 보여야 할 장면,",
        "`빨간 원`은 클릭 지점 강조가 들어가는 곳입니다.",
        "",
        f"**분량**: 전체 {len(scenes)}장면 / 대사 있는 장면 {len(spoken)}개 / "
        f"무대사 {silent}개 (원본 약 {last})",
        "",
        "> 이 문서는 `python -m scripts.write_script_doc`으로 시드에서 생성됩니다.",
        "> 직접 고치지 마시고 `scripts/seed_*.py`를 고친 뒤 다시 생성하세요.",
        "",
    ]

    header = ["#", "원본 타임코드", "챕터"]
    if two_speakers:
        header.append("화자")
    header += ["대사", "화면", "빨간 원"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))

    for scene in scenes:
        caption = escape(scene.caption) if scene.caption.strip() else (
            f"*(무대사 · {scene.hold_seconds:.0f}초 유지)*" if scene.hold_seconds
            else "*(무대사)*"
        )
        row = [
            str(scene.order + 1),
            scene.source_timecode or "—",
            scene.chapter or "—",
        ]
        if two_speakers:
            row.append(SPEAKER_LABEL.get(scene.speaker, scene.speaker))
        row += [
            caption,
            f"`{scene.visual_key}`" if scene.visual_key else "—",
            "●" if scene.cue.enabled else "",
        ]
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="시드에서 낭독용 대본 문서 생성")
    parser.add_argument("project_id", nargs="?", default="demo-solo")
    args = parser.parse_args()

    if args.project_id not in DOC_BY_PROJECT:
        raise SystemExit(
            f"대본 문서를 만들 프로젝트가 아닙니다: {args.project_id}\n"
            f"가능한 값: {', '.join(DOC_BY_PROJECT)}"
        )

    project = get_store().get(args.project_id)
    if not project:
        raise SystemExit(f"프로젝트를 찾을 수 없습니다: {args.project_id}")

    rel_path, title = DOC_BY_PROJECT[args.project_id]
    out_path = Path(__file__).resolve().parents[2] / rel_path
    two_speakers = len({s.speaker for s in project.scenes}) > 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build(project, title, two_speakers), encoding="utf-8")
    print(f"[doc] {out_path} ({len(project.scenes)}장면)")


if __name__ == "__main__":
    main()
