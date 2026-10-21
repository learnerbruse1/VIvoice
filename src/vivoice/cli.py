"""Headless command-line front-end over the same engine the GUI uses."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import yaml

import vivoice.effects  # noqa: F401  (registers built-in effects)
from vivoice import __version__
from vivoice.ai.device import describe_device
from vivoice.config import UserConfig
from vivoice.core import Cancelled, MissingDependencyError, VivoiceError
from vivoice.core.effect import get_effect_class, registered_effects
from vivoice.models import ModelRegistry, pull_model
from vivoice.paths import guide_path, models_root
from vivoice.plugins import load_plugins
from vivoice.presets import Preset

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vivoice",
        description="VIvoice: an offline-first, extensible voice changer.",
    )
    parser.add_argument("--version", action="version", version=f"vivoice {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="convert an audio file with a preset")
    process.add_argument("input", type=Path, help="input WAV/FLAC/OGG file")
    process.add_argument("output", type=Path, help="output WAV/FLAC/OGG file")
    process.add_argument("--preset", type=Path, required=True, help="preset YAML file")
    process.set_defaults(handler=_cmd_process)

    effects = subparsers.add_parser("effects", help="list registered effects")
    effects.add_argument("type", nargs="?", help="show one effect's parameter schema")
    effects.set_defaults(handler=_cmd_effects)

    schema = subparsers.add_parser("schema", help="export all effect schemas as JSON")
    schema.set_defaults(handler=_cmd_schema)

    config = subparsers.add_parser("config", help="view or change user settings")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    config_list = config_sub.add_parser("list", help="print all settings")
    config_list.set_defaults(handler=_cmd_config_list)
    config_get = config_sub.add_parser("get", help="print one setting")
    config_get.add_argument("key")
    config_get.set_defaults(handler=_cmd_config_get)
    config_set = config_sub.add_parser("set", help="change one setting")
    config_set.add_argument("key")
    config_set.add_argument("value")
    config_set.set_defaults(handler=_cmd_config_set)

    stream = subparsers.add_parser("stream", help="process microphone input in real time")
    stream.add_argument("--preset", type=Path, help="preset YAML file")
    stream.add_argument("--samplerate", type=int, help="stream sample rate (default: preset value)")
    stream.add_argument("--block", type=int, help="block size in frames")
    stream.add_argument("--channels", type=int, help="input and output channel count")
    stream.add_argument("--input-device", help="input device name or index")
    stream.add_argument("--output-device", help="output device name or index")
    stream.add_argument("--latency", choices=["low", "high"], help="PortAudio latency hint")
    stream.add_argument("--list-devices", action="store_true", help="list audio devices and exit")
    stream.set_defaults(handler=_cmd_stream)

    devices = subparsers.add_parser("devices", help="show the detected compute device")
    devices.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda", "mps"])
    devices.set_defaults(handler=_cmd_devices)

    preset = subparsers.add_parser("preset", help="validate a preset")
    preset.add_argument("action", choices=["validate"])
    preset.add_argument("file", type=Path)
    preset.set_defaults(handler=_cmd_preset_validate)

    model = subparsers.add_parser("model", help="manage voice models")
    model_sub = model.add_subparsers(dest="model_command", required=True)

    model_add = model_sub.add_parser("add", help="import a local .pth checkpoint")
    model_add.add_argument("checkpoint", type=Path)
    model_add.add_argument("--name", required=True, help="display name for the model")
    model_add.add_argument("--index", type=Path, help="optional .index file")
    model_add.set_defaults(handler=_cmd_model_add)

    model_list = model_sub.add_parser("list", help="list imported models")
    model_list.set_defaults(handler=_cmd_model_list)

    model_remove = model_sub.add_parser("remove", help="remove an imported model")
    model_remove.add_argument("name")
    model_remove.set_defaults(handler=_cmd_model_remove)

    model_pull = model_sub.add_parser("pull", help="download a model from HuggingFace")
    model_pull.add_argument("repo_id", help="owner/repository identifier")
    model_pull.add_argument("--name", help="local display name")
    model_pull.add_argument("--revision", help="branch, tag, or commit")
    model_pull.add_argument(
        "--path", help="download one repo-relative file instead of the whole repository"
    )
    model_pull.add_argument("--index", help="repo-relative .index file (with --path)")
    model_pull.set_defaults(handler=_cmd_model_pull)

    guide = subparsers.add_parser("guide", help="show the user guide location")
    guide.set_defaults(handler=_cmd_guide)

    serve = subparsers.add_parser("serve", help="run the voice-conversion HTTP server")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=7865)
    serve.set_defaults(handler=_cmd_serve)

    gui = subparsers.add_parser("gui", help="launch the desktop application")
    gui.set_defaults(handler=_cmd_gui)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        log_level = str(UserConfig().get("log_level")).upper()
    except VivoiceError:
        log_level = "INFO"
    logging.basicConfig(level=log_level, format="%(levelname)s %(message)s")
    load_plugins()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except Cancelled:
        print("cancelled", file=sys.stderr)
        return 130
    except VivoiceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except Exception:
        logger.exception("unexpected failure")
        return 2


def _cmd_process(args: argparse.Namespace) -> int:
    preset = Preset.load(args.preset)
    preset.build_chain().render_file(args.input, args.output)
    print(f"wrote {args.output}")
    return 0


def _cmd_effects(args: argparse.Namespace) -> int:
    if args.type:
        try:
            schema = get_effect_class(args.type).params_schema()
        except VivoiceError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(schema, indent=2))
        return 0
    for name, effect_class in sorted(registered_effects().items()):
        marker = " [streaming]" if effect_class.streaming else ""
        print(f"{name:<20} {effect_class.description}{marker}")
    return 0


def _cmd_schema(args: argparse.Namespace) -> int:
    schemas = {
        name: effect_class.params_schema()
        for name, effect_class in sorted(registered_effects().items())
    }
    print(json.dumps(schemas, indent=2))
    return 0


def _cmd_stream(args: argparse.Namespace) -> int:
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise MissingDependencyError(
            "sounddevice is required for streaming. Run: uv sync --extra realtime"
        ) from exc

    if args.list_devices:
        print(sd.query_devices())
        return 0

    if args.preset is None:
        raise VivoiceError("--preset is required for streaming (or use --list-devices)")

    preset = Preset.load(args.preset)
    chain = preset.build_chain()
    config = UserConfig().load()
    sample_rate = int(args.samplerate or config["sample_rate"])
    session = chain.open_stream(sample_rate)
    stop = threading.Event()

    def callback(
        indata: np.ndarray,
        outdata: np.ndarray,
        frames: int,
        time_info: object,
        status: object,
    ) -> None:
        if status:
            print(status, file=sys.stderr)
        block = np.ascontiguousarray(indata, dtype=np.float32).T
        try:
            processed = session.process_block(block)
        except Exception:
            stop.set()
            raise sd.CallbackAbort from None
        outdata.fill(0.0)
        copied = min(frames, processed.shape[1])
        channels = min(outdata.shape[1], processed.shape[0])
        outdata[:copied, :channels] = processed[:channels, :copied].T

    try:
        with sd.Stream(
            samplerate=sample_rate,
            blocksize=args.block if args.block is not None else int(config["block_size"]),
            dtype="float32",
            device=(
                args.input_device or config["input_device"],
                args.output_device or config["output_device"],
            ),
            channels=(args.channels, args.channels) if args.channels else None,
            latency=args.latency or "low",
            callback=callback,
        ) as _:
            print("streaming; press Ctrl+C to stop", file=sys.stderr)
            while not stop.wait(0.25):
                pass
    except KeyboardInterrupt:
        stop.set()
    except (ValueError, sd.PortAudioError) as exc:
        raise VivoiceError(f"Audio stream failed: {exc}") from exc
    return 0


def _cmd_config_list(args: argparse.Namespace) -> int:
    print(yaml.safe_dump(UserConfig().load(), sort_keys=False, allow_unicode=True), end="")
    return 0


def _cmd_config_get(args: argparse.Namespace) -> int:
    print(UserConfig().get(args.key))
    return 0


def _cmd_config_set(args: argparse.Namespace) -> int:
    value = yaml.safe_load(args.value)
    UserConfig().set(args.key, value)
    print(f"set {args.key} = {value!r}")
    return 0


def _cmd_devices(args: argparse.Namespace) -> int:
    print(describe_device(args.device))
    return 0


def _cmd_preset_validate(args: argparse.Namespace) -> int:
    preset = Preset.load(args.file)
    preset.build_chain()
    print(f"preset '{preset.name}' is valid ({len(preset.chain_config)} effects)")
    return 0


def _cmd_model_add(args: argparse.Namespace) -> int:
    model = ModelRegistry().add(
        args.name,
        args.checkpoint,
        args.index,
    )
    print(f"imported voice model '{model.name}'")
    return 0


def _cmd_model_list(args: argparse.Namespace) -> int:
    models = ModelRegistry().all()
    if not models:
        print(f"no voice models in {models_root()}")
        return 0
    for model in models:
        index = model.index.name if model.index else "-"
        print(f"{model.name:<24} {model.source:<24} index: {index}")
    return 0


def _cmd_model_remove(args: argparse.Namespace) -> int:
    ModelRegistry().remove(args.name)
    print(f"removed voice model '{args.name}'")
    return 0


def _cmd_model_pull(args: argparse.Namespace) -> int:
    model = pull_model(
        args.repo_id,
        name=args.name,
        revision=args.revision,
        path=args.path,
        index_path=args.index,
    )
    print(f"downloaded voice model '{model.name}' from {model.source}")
    return 0


def _cmd_guide(args: argparse.Namespace) -> int:
    path = guide_path()
    if path is None:
        print("The user guide is available inside the GUI (Help > User guide).")
    else:
        print(f"user guide: {path}")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    from vivoice.server import main as serve_main

    return serve_main(["--host", args.host, "--port", str(args.port)])


def _cmd_gui(args: argparse.Namespace) -> int:
    try:
        from vivoice.gui.app import main as gui_main
    except ImportError as exc:
        print(f"error: {exc}. Run: uv sync", file=sys.stderr)
        return 1
    return gui_main()
