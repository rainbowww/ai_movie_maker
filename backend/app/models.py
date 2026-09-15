"""Data models for a video project: an ordered list of narrated scenes,
persisted as one JSON file per project under STORAGE_DIR.

This is intentionally a flat-file store, not a database: the app is a
single-user local tool, and a project.json next to its generated media is
easy to inspect, back up, or hand-edit. Swap ProjectStore for a real
database later if this needs multi-user access.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

Speaker = Literal["m", "f"]


class CueCircle(BaseModel):
    """Normalized (0-1) position of the red 'click here' callout drawn on
    top of a scene's generated image. (0,0) is the top-left corner."""

    x: float = 0.5
    y: float = 0.5
    r: float = 0.12
    enabled: bool = False


class Scene(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    order: int
    chapter: str = ""
    speaker: Speaker = "m"
    caption: str = ""
    image_prompt: str = ""
    # Name of the locally drawn mockup for this screen (app.services.mockups).
    # Lets the zero-cost path draw the exact layout the cue circle points at.
    visual_key: str = ""
    cue: CueCircle = Field(default_factory=CueCircle)
    # Timecode of the matching beat in the source video ("0:14-0:16"), kept so a
    # remake can be checked against the original's pacing.
    source_timecode: str = ""
    # How long to hold a narration-free scene (music/logo beats). Ignored when
    # the scene has audio, since audio length wins.
    hold_seconds: Optional[float] = None
    image_path: Optional[str] = None  # relative to STORAGE_DIR
    audio_path: Optional[str] = None  # relative to STORAGE_DIR
    audio_seconds: Optional[float] = None


class Project(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str = "제목 없는 프로젝트"
    # Gemini TTS prebuilt voice names (see README for the full voice list –
    # verify actual timbre in Google AI Studio before committing to a pair).
    voice_m: str = "Puck"
    voice_f: str = "Kore"
    scenes: list[Scene] = Field(default_factory=list)
    video_path: Optional[str] = None

    def scenes_dir(self, storage_root: Path) -> Path:
        d = storage_root / self.id / "scenes"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def project_dir(self, storage_root: Path) -> Path:
        d = storage_root / self.id
        d.mkdir(parents=True, exist_ok=True)
        return d


class ProjectStore:
    def __init__(self, storage_root: Path):
        self.storage_root = storage_root
        self.storage_root.mkdir(parents=True, exist_ok=True)

    def _path(self, project_id: str) -> Path:
        return self.storage_root / project_id / "project.json"

    def list(self) -> list[Project]:
        out: list[Project] = []
        for child in sorted(self.storage_root.iterdir()):
            p = child / "project.json"
            if p.exists():
                out.append(Project.model_validate_json(p.read_text(encoding="utf-8")))
        return out

    def get(self, project_id: str) -> Optional[Project]:
        p = self._path(project_id)
        if not p.exists():
            return None
        return Project.model_validate_json(p.read_text(encoding="utf-8"))

    def save(self, project: Project) -> Project:
        p = self._path(project.id)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        return project

    def delete(self, project_id: str) -> None:
        d = self.storage_root / project_id
        if d.exists():
            shutil.rmtree(d)
