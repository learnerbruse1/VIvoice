from __future__ import annotations

from vivoice.audio import AudioBuffer, save_audio
from vivoice.cli import main


def test_effects_lists_builtins(capsys) -> None:
    assert main(["effects"]) == 0
    output = capsys.readouterr().out
    assert "gain" in output
    assert "voice-conversion" in output
    assert "[streaming]" in output


def test_process_with_preset(tmp_path, robot_preset, sine_440, capsys) -> None:
    source = tmp_path / "in.wav"
    destination = tmp_path / "out.wav"
    save_audio(AudioBuffer(sine_440, 48_000), source)

    result = main(
        ["process", str(source), str(destination), "--preset", str(robot_preset)]
    )
    assert result == 0
    assert destination.is_file()
    assert "wrote" in capsys.readouterr().out


def test_devices_prints_cpu_without_torch(capsys) -> None:
    assert main(["devices"]) == 0
    assert "CPU" in capsys.readouterr().out


def test_missing_preset_fails_cleanly(tmp_path, capsys) -> None:
    result = main(
        [
            "process",
            str(tmp_path / "in.wav"),
            str(tmp_path / "out.wav"),
            "--preset",
            str(tmp_path / "missing.yaml"),
        ]
    )
    assert result == 1
    assert "error:" in capsys.readouterr().err


def test_model_add_and_list(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    checkpoint = tmp_path / "voice.pth"
    checkpoint.write_bytes(b"checkpoint")

    assert main(["model", "add", str(checkpoint), "--name", "alice"]) == 0
    assert main(["model", "list"]) == 0
    assert "alice" in capsys.readouterr().out


def test_effects_detail_prints_schema(capsys) -> None:
    assert main(["effects", "gain"]) == 0
    assert '"type": "gain"' in capsys.readouterr().out


def test_schema_exports_all_effects(capsys) -> None:
    assert main(["schema"]) == 0
    output = capsys.readouterr().out
    assert '"voice-conversion"' in output
    assert '"pitch"' in output


def test_config_commands_roundtrip(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("VIVOICE_HOME", str(tmp_path))
    assert main(["config", "list"]) == 0
    assert main(["config", "set", "sample_rate", "44100"]) == 0
    assert main(["config", "get", "sample_rate"]) == 0
    assert "44100" in capsys.readouterr().out


def test_doctor_reports_environment(capsys) -> None:
    assert main(["doctor"]) == 0
    output = capsys.readouterr().out
    assert "vivoice" in output
    assert "NumPy" in output
    assert "PyTorch" in output
    assert "compute device" in output
