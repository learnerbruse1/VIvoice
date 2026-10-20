"""Headless command-line front-end over the same engine the GUI uses."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

import vivoice.effects  # noqa: F401  (registers built-in effects)
from vivoice import __version__
from vivoice.ai.device import describe_device
from vivoice.core import VivoiceError
from vivoice.core.effect import registered_effects
from vivoice.models import ModelRegistry, pull_model
from vivoice.paths import guide_path, models_root
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
    effects.set_defaults(handler=_cmd_effects)

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
    model_pull.set_defaults(handler=_cmd_model_pull)

    guide = subparsers.add_parser("guide", help="show the user guide location")
    guide.set_defaults(handler=_cmd_guide)

    gui = subparsers.add_parser("gui", help="launch the desktop application")
    gui.set_defaults(handler=_cmd_gui)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
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
    for name, effect_class in sorted(registered_effects().items()):
        print(f"{name:<20} {effect_class.description}")
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
    model = pull_model(args.repo_id, name=args.name, revision=args.revision)
    print(f"downloaded voice model '{model.name}' from {model.source}")
    return 0


def _cmd_guide(args: argparse.Namespace) -> int:
    path = guide_path()
    if path is None:
        print("The user guide is available inside the GUI (Help > User guide).")
    else:
        print(f"user guide: {path}")
    return 0


def _cmd_gui(args: argparse.Namespace) -> int:
    try:
        from vivoice.gui.app import main as gui_main
    except ImportError as exc:
        print(f"error: {exc}. Run: uv sync", file=sys.stderr)
        return 1
    return gui_main()
