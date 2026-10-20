from __future__ import annotations

from pathlib import Path

import pytest

from vivoice.core import ModelError, ModelNotFoundError
from vivoice.models import ModelRegistry, pull_model


@pytest.fixture
def registry(tmp_path, monkeypatch) -> ModelRegistry:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    checkpoint = tmp_path / "voice.pth"
    checkpoint.write_bytes(b"checkpoint")
    return ModelRegistry()


def test_add_list_get_remove(tmp_path, registry: ModelRegistry) -> None:
    checkpoint = tmp_path / "voice.pth"
    index = tmp_path / "voice.index"
    index.write_bytes(b"index")
    registry.add("alice", checkpoint, index)

    assert registry.names() == ["alice"]
    model = registry.get("alice")
    assert model.checkpoint.is_file()
    assert model.index is not None and model.index.is_file()

    registry.remove("alice")
    assert registry.names() == []
    with pytest.raises(ModelNotFoundError):
        registry.get("alice")


def test_duplicate_name_is_rejected(tmp_path, registry: ModelRegistry) -> None:
    registry.add("alice", tmp_path / "voice.pth")
    with pytest.raises(ModelError, match="already exists"):
        registry.add("alice", tmp_path / "voice.pth")


def test_missing_checkpoint_is_rejected(tmp_path, registry: ModelRegistry) -> None:
    with pytest.raises(ModelError, match="not found"):
        registry.add("ghost", tmp_path / "missing.pth")


def test_pull_model_registers_checkpoint(tmp_path, monkeypatch) -> None:
    def fake_snapshot(repo_id: str, local_dir: str, revision: str | None) -> str:
        directory = Path(local_dir)
        directory.mkdir(parents=True)
        (directory / "model.pth").write_bytes(b"pth")
        (directory / "model.index").write_bytes(b"index")
        return str(directory)

    monkeypatch.setattr("vivoice.models.hub._snapshot_download", fake_snapshot)
    model = pull_model("owner/character", root=tmp_path)

    assert model.name == "character"
    assert model.source == "huggingface:owner/character"
    assert model.checkpoint.is_file()
    assert model.index is not None and model.index.is_file()


def test_pull_model_requires_owner_repo(tmp_path) -> None:
    with pytest.raises(ModelError, match="owner/repository"):
        pull_model("not-a-repo-id", root=tmp_path)
