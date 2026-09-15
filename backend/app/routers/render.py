from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..deps import get_store
from ..services.video_render import RenderError, render_project_video

router = APIRouter(prefix="/api/projects", tags=["render"])


@router.post("/{project_id}/render")
def render_project(project_id: str):
    settings = get_settings()
    store = get_store()
    project = store.get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
    if not project.scenes:
        raise HTTPException(400, "장면이 없습니다.")

    missing_images = [s.order + 1 for s in project.scenes if not s.image_path]
    if missing_images:
        raise HTTPException(400, f"이미지가 없는 장면이 있습니다: {missing_images}. 먼저 생성을 완료하세요.")

    scene_assets = []
    for scene in sorted(project.scenes, key=lambda s: s.order):
        image_path = settings.storage_dir / scene.image_path  # type: ignore[arg-type]
        audio_path = settings.storage_dir / scene.audio_path if scene.audio_path else None
        scene_assets.append((image_path, audio_path))

    out_path = project.project_dir(settings.storage_dir) / "final.mp4"
    work_dir = project.project_dir(settings.storage_dir) / "_render_work"

    try:
        duration = render_project_video(scene_assets, out_path, work_dir)
    except RenderError as e:
        raise HTTPException(500, str(e))

    project.video_path = str(out_path.relative_to(settings.storage_dir))
    store.save(project)
    return {"video_path": project.video_path, "duration_seconds": duration}
