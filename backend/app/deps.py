from __future__ import annotations

from functools import lru_cache

from .config import get_settings
from .models import ProjectStore


@lru_cache
def get_store() -> ProjectStore:
    return ProjectStore(get_settings().storage_dir)
