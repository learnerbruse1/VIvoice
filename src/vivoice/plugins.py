"""Third-party plugin loading via Python entry points.

Plugins register themselves by importing a module that decorates an
:class:`Effect` with ``@register_effect`` or a
:class:`VoiceConversionAdapter` with ``@register_adapter``. Installing a
package that declares the ``vivoice.effects`` or ``vivoice.adapters`` entry
point group is enough; VIvoice imports the group at startup.
"""

from __future__ import annotations

from collections.abc import Iterable
from importlib import metadata
from typing import Any

EFFECTS_GROUP = "vivoice.effects"
ADAPTERS_GROUP = "vivoice.adapters"


def load_entry_points(group: str) -> list[Any]:
    """Load every entry point in a group; returns what each ``load()`` returns."""
    points = metadata.entry_points()
    selected: Iterable[Any]
    if hasattr(points, "select"):
        selected = points.select(group=group)
    else:
        selected = getattr(points, "get", lambda _group, _default: [])(group, [])
    return [point.load() for point in selected]


def load_plugins() -> None:
    """Import all installed VIvoice plugins so they can self-register."""
    for group in (EFFECTS_GROUP, ADAPTERS_GROUP):
        load_entry_points(group)
