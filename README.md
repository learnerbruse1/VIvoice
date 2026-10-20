# VIvoice

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-informational.svg)](pyproject.toml)
[![CI](https://github.com/VIvoice/VIvoice/actions/workflows/ci.yml/badge.svg)](https://github.com/VIvoice/VIvoice/actions/workflows/ci.yml)

VIvoice is an offline-first, extensible voice changer. It combines deterministic DSP effects
(pitch shift, formant-style effects, robot voice, delay, gain) with a pluggable AI voice
conversion layer. The default AI engine is
[RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI), so you can import
the community's `.pth` / `.index` character voice models from HuggingFace, voice-models.com, and
similar sites.

> 中文说明请见 [README.zh-CN.md](README.zh-CN.md)。

## Why VIvoice

- **Extensible** — effects and AI engines are small, well-defined classes. See
  [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md).
- **Stable** — the audio core is a pure, unit-tested pipeline with no mutable global state; the
  GUI and CLI are thin front-ends over the same engine.
- **Local-first** — everything runs on your machine. If a CUDA GPU is available it is detected
  and used automatically; otherwise the CPU is used.
- **Honest about latency** — v0 is offline file-to-file. Real-time streaming is a planned
  milestone with documented latency targets ([docs/ROADMAP.md](docs/ROADMAP.md)).

## Features (v0.1)

- Headless engine with a desktop GUI (PySide6) and a CLI (`vivoice`)
- Block-free, float32 processing at 48 kHz with multi-channel DSP support
- Built-in effects: gain, pitch shift (phase vocoder), robot (ring modulation), echo,
  three-band EQ, noise gate, reverb
- YAML presets and an effect registry (`vivoice effects`)
- Real-time preview (`vivoice stream`) with a streaming pitch shifter; offline
  rendering keeps the higher-quality phase vocoder
- Chunked, bounded-memory rendering with smooth progress and cancellation
- Local voice-model manager (`vivoice model add/list/remove`) and HuggingFace downloads
  (`vivoice model pull <repo-id>`)
- Automatic compute-device detection: CUDA → MPS → CPU, with `--device` override
- Third-party plugins via entry points and JSON parameter schemas
  (`vivoice schema`, `vivoice effects <type>`)
- User settings (`vivoice config list|get|set`)
- Bilingual README and a detailed in-app usage guide with links

## Quick start

Requirements: Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/VIvoice/VIvoice.git
cd VIvoice
uv sync --extra dev --extra realtime
uv run vivoice effects
uv run vivoice-gui
```

For the AI voice-conversion engine (optional, heavy):

```bash
uv sync --extra ai
python scripts/fetch_rvc.py            # vendors the official MIT-licensed RVC repo
uv run vivoice model pull <hf-repo-id> # or: vivoice model add path/to/model.pth
```

## Command-line tour

```bash
vivoice process input.wav output.wav --preset examples/presets/robot.yaml
vivoice effects                    # list registered effects
vivoice schema                     # export JSON schemas for tooling
vivoice devices                    # show the detected compute device
vivoice model add voice.pth --name alice --index voice.index
vivoice model list
vivoice model pull wok000/vcclient000
vivoice gui                        # launch the desktop app
vivoice stream --preset examples/presets/broadcast.yaml
vivoice config set sample_rate 44100
```

See `vivoice --help` and [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for the full walkthrough.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [User guide (bilingual)](docs/USER_GUIDE.md)
- [Developing effects and adapters](docs/PLUGIN_DEVELOPMENT.md)
- [Preset format](docs/preset-format.md)
- [Roadmap](docs/ROADMAP.md)
- [Architecture decision records](docs/adr/)
- [Glossary](CONTEXT.md)

## Ethics

Voice conversion can be misused. Before cloning a voice, obtain the speaker's informed consent.
Read [ETHICS.md](ETHICS.md) and do not use VIvoice for impersonation or fraud.

## License and third parties

VIvoice is [MIT](LICENSE) licensed. The optional RVC adapter vendors the MIT-licensed
[RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
at a pinned commit; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Voice models you import
have their own licenses — respect them.
