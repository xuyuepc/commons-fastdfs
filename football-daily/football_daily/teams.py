from __future__ import annotations

from .config import TEAM_ALIASES


def normalize_team(name: str) -> str:
    name = (name or "").strip()
    return TEAM_ALIASES.get(name, name)