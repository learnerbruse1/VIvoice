from __future__ import annotations

from vivoice.paths import guide_path, load_guide_markdown


def test_guide_loads_bilingual_steps() -> None:
    markdown = load_guide_markdown()
    assert "使用指南" in markdown
    assert "HuggingFace" in markdown
    assert "https://" in markdown


def test_guide_path_resolves_from_checkout() -> None:
    assert guide_path() is not None
