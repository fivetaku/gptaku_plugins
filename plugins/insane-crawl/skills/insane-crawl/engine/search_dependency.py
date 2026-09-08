"""Locate insane-search without assuming the plugins share a cache version."""
from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import TypeAlias

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)


def search_skill_roots() -> Iterator[Path]:
    """Prefer the explicit skill, registered installPaths, then a source sibling."""
    override = os.environ.get("INSANE_SEARCH_SKILL_ROOT", "").strip()
    if override:
        yield Path(override).expanduser().resolve()
    yield from _registered_skill_roots()
    yield Path(__file__).resolve().parents[4] / "insane-search" / "skills" / "insane-search"


def _registered_skill_roots() -> Iterator[Path]:
    registry = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    try:
        payload: JsonValue = json.loads(registry.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return  # Source-only development does not require a plugin registry.
    except (ValueError, UnicodeError) as error:
        raise RuntimeError(f"Invalid plugin registry {registry}: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Invalid plugin registry {registry}: expected an object")
    plugins = payload.get("plugins")
    if not isinstance(plugins, dict):
        raise RuntimeError(f"Invalid plugin registry {registry}: expected a plugins object")
    for name, entries in plugins.items():
        if name.partition("@")[0] != "insane-search":
            continue
        if not isinstance(entries, list):
            raise RuntimeError(f"Invalid plugin registry {registry}: {name} must contain an installation list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise RuntimeError(f"Invalid plugin registry {registry}: {name} installation must be an object")
            install_path = entry.get("installPath")
            if not isinstance(install_path, str) or not install_path.strip():
                raise RuntimeError(f"Invalid plugin registry {registry}: {name} installation needs installPath")
            yield Path(install_path).expanduser().resolve() / "skills" / "insane-search"
