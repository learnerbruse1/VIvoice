"""Filesystem locations used by VIvoice.

Everything is resolved lazily so tests can point ``VIVOICE_HOME`` at a
temporary directory.
"""

from __future__ import annotations

import os
from pathlib import Path


def data_home() -> Path:
    """Root directory for user data (models, user presets)."""
    override = os.environ.get("VIVOICE_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".vivoice"


def models_root() -> Path:
    return data_home() / "models"


def user_presets_dir() -> Path:
    return data_home() / "presets"


def repo_root() -> Path | None:
    """Repository root when running from a checkout, otherwise ``None``."""
    for candidate in (Path.cwd(), Path(__file__).resolve().parents[2]):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return None


def shipped_presets_dir() -> Path | None:
    root = repo_root()
    if root is None:
        return None
    return root / "examples" / "presets"


def guide_path() -> Path | None:
    """Filesystem path of the user guide, when one exists."""
    candidates: list[Path] = []
    override = os.environ.get("VIVOICE_DOCS_DIR")
    if override:
        candidates.append(Path(override).expanduser() / "USER_GUIDE.md")
    root = repo_root()
    if root is not None:
        candidates.append(root / "docs" / "USER_GUIDE.md")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_guide_markdown() -> str:
    """Guide text as Markdown, from the checkout or the installed wheel."""
    path = guide_path()
    if path is not None:
        return path.read_text(encoding="utf-8")
    from importlib import resources

    resource = resources.files("vivoice") / "resources" / "USER_GUIDE.md"
    return resource.read_text(encoding="utf-8")
