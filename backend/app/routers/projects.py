from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..deps import get_store
from ..models import Project, Scene

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[Project])
def list_projects():
    return get_store().list()


@router.post("", response_model=Project)
def create_project(project: Project):
    return get_store().save(project)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str):
    project = get_store().get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, project: Project):
    if project.id != project_id:
        raise HTTPException(400, "경로의 project_id와 본문의 id가 다릅니다.")
    if not get_store().get(project_id):
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
    return get_store().save(project)


@router.delete("/{project_id}")
def delete_project(project_id: str):
    get_store().delete(project_id)
    return {"ok": True}


@router.put("/{project_id}/scenes/{scene_id}", response_model=Project)
def update_scene(project_id: str, scene_id: str, scene: Scene):
    project = get_store().get(project_id)
    if not project:
        raise HTTPException(404, "프로젝트를 찾을 수 없습니다.")
    for i, s in enumerate(project.scenes):
        if s.id == scene_id:
            project.scenes[i] = scene
            return get_store().save(project)
    raise HTTPException(404, "장면을 찾을 수 없습니다.")
