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
def generate_all(project_id: str, force: bool = False, limit: int = 4):
    """Generate assets for up to `limit` scenes that still need them.

    Deliberately chunked. A 35-scene project means 70 Gemini calls, which
    takes far longer than an HTTP request should live — so this returns
    after a few scenes and reports what is left. Each scene is saved as it
    completes, so calling again resumes where this left off and nothing is
    regenerated (or lost) in between. The frontend loops on `remaining`.
    """
    store = get_store()
    project = store.get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")

    def needs_work(scene) -> bool:
        if force:
            return bool(scene.image_prompt.strip() or scene.caption.strip())
        wants_image = bool(scene.image_prompt.strip()) and not scene.image_path
        wants_audio = bool(scene.caption.strip()) and not scene.audio_path
        return wants_image or wants_audio

    pending = [s for s in sorted(project.scenes, key=lambda s: s.order) if needs_work(s)]
    batch = pending[: max(1, limit)]

    results = []
    succeeded = 0
    for scene in batch:
        outcome = _generate_for_scene(project_id, scene, force)
        if not outcome["errors"]:
            succeeded += 1
        results.append({"scene_id": scene.id, **outcome})

    # `succeeded` is what the caller's loop must watch. `remaining` alone
    # never reaches zero when every call fails the same way (a missing key,
    # an exhausted quota), so a loop driven by it would hammer the API
    # forever instead of surfacing the error.
    return {
        "processed": len(batch),
        "succeeded": succeeded,
        "remaining": max(0, len(pending) - succeeded),
        "total_scenes": len(project.scenes),
        "results": results,
    }
