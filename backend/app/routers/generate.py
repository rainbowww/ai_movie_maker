"""Endpoints that call out to Gemini (image + TTS). Require GEMINI_API_KEY."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..deps import get_store
from ..models import Scene
from ..services.gemini_image import GeminiImageError, generate_image
from ..services.gemini_tts import GeminiTTSError, generate_speech
from ..services.overlay import apply_cue_circle

router = APIRouter(prefix="/api/projects", tags=["generate"])


def _generate_for_scene(project_id: str, scene: Scene, force: bool) -> dict:
    settings = get_settings()
    store = get_store()
    project = store.get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")

    scenes_dir = project.scenes_dir(settings.storage_dir)
    errors: dict[str, str] = {}

    if (force or not scene.image_path) and scene.image_prompt.strip():
        raw_path = scenes_dir / f"{scene.id}_raw.png"
        final_path = scenes_dir / f"{scene.id}.png"
        try:
            generate_image(settings, scene.image_prompt, raw_path)
            if scene.cue.enabled:
                apply_cue_circle(raw_path, final_path, scene.cue.x, scene.cue.y, scene.cue.r)
            else:
                final_path.write_bytes(raw_path.read_bytes())
            scene.image_path = str(final_path.relative_to(settings.storage_dir))
        except GeminiImageError as e:
            errors["image"] = str(e)

    if (force or not scene.audio_path) and scene.caption.strip():
        audio_path = scenes_dir / f"{scene.id}.wav"
        voice = project.voice_m if scene.speaker == "m" else project.voice_f
        try:
            generate_speech(settings, scene.caption, voice, audio_path)
            scene.audio_path = str(audio_path.relative_to(settings.storage_dir))
        except GeminiTTSError as e:
            errors["audio"] = str(e)

    for i, s in enumerate(project.scenes):
        if s.id == scene.id:
            project.scenes[i] = scene
            break
    store.save(project)

    if errors:
        return {"scene": scene.model_dump(), "errors": errors}
    return {"scene": scene.model_dump(), "errors": None}


@router.post("/{project_id}/scenes/{scene_id}/generate", response_model=Scene)
def generate_scene_assets(project_id: str, scene_id: str, force: bool = False):
    project = get_store().get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
    scene = next((s for s in project.scenes if s.id == scene_id), None)
    if not scene:
        raise HTTPException(404, "장면을 찾을 수 없습니다.")

    result = _generate_for_scene(project_id, scene, force)
    if result["errors"]:
        raise HTTPException(502, {"message": "일부 자산 생성 실패", "errors": result["errors"]})
    return result["scene"]


@router.post("/{project_id}/generate-all")
def generate_all(project_id: str, force: bool = False):
    project = get_store().get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")

    results = []
    for scene in sorted(project.scenes, key=lambda s: s.order):
        results.append({"scene_id": scene.id, **_generate_for_scene(project_id, scene, force)})
    return results
