# Changelog

All notable changes to VIvoice are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [0.5.0] - 2026-10-21

### Added

- `rvc-hub` engine backed by the MIT-licensed `huggingface-hub-rvc` pipeline:
  loads classic RVC-WebUI `.pth`/`.index` character models without fairseq/av
  and was verified end-to-end on CPU with a real character model (input/output
  correlation dropped to 0.063 after conversion).
- Soundfile-based `torchaudio.load/save` shim so shared FFmpeg libraries are
  not required for decoding.
- ADR-0004, `ai-voice-rvc-hub.yaml` preset, and HuggingFace/proxy-CA network
  troubleshooting documentation.

### Changed

- The `ai` extra now declares the `rvc-hub` dependency set
  (huggingface-hub-rvc, librosa, safetensors, transformers, torchaudio).

## [0.4.0] - 2026-10-20

### Added

- In-process RVC adapter wiring (`VC.get_vc` / `vc_single`) with lazy upstream
  imports, device mapping, and error normalization; logic verified with a fake
  engine.
- `rvc-http` adapter and a reference conversion server (`vivoice serve`,
  `scripts/rvc_server.py`) implementing the documented WAV-in/WAV-out protocol
  ([docs/RVC_SERVER_PROTOCOL.md](docs/RVC_SERVER_PROTOCOL.md)); client tested
  against a fake server and server endpoints tested directly.
- GUI "Live" page for real-time preview with device, sample-rate, and
  block-size selectors.
- Packaging: PyInstaller build scripts, launch entry points, and a
  tag-triggered release workflow ([docs/PACKAGING.md](docs/PACKAGING.md)).
- `ai-voice-http.yaml` example preset and the `ConversionError` error class.

### Fixed

- Restored `PresetsPage` methods that a misordered class insertion had
  shadowed (caught by the GUI smoke test during loop-back).

## [0.3.0] - 2026-10-20

### Added

- Chunked, bounded-memory offline rendering with smooth progress and per-block
  cancellation (used automatically when every effect is `block_process`).
- Real-time pitch shifting via a delay-line algorithm with crossfaded wraps;
  offline quality stays on the phase vocoder (`process_stream` contract).
- Third-party plugins through the `vivoice.effects` / `vivoice.adapters`
  entry-point groups, plus JSON parameter schemas (`vivoice effects <type>`,
  `vivoice schema`).
- User configuration (`vivoice config list|get|set`) feeding stream and GUI
  defaults; atomic writes and validation.
- `ModelAddWorker` (local imports no longer block the GUI) and a global GUI
  exception hook.
- `AGENTS.md` and `docs/AI_HANDBOOK.md` for AI contributors.

### Fixed

- `AudioIOError` wraps file read/write failures so the CLI reports them as
  expected errors instead of tracebacks.
- Cancelled chunked renders remove the partial output file.
- Precise shape/state checks in the chunked render path.

## [0.2.0] - 2026-10-20

### Added

- Three new effects: three-band EQ (`eq`), noise gate (`noise-gate`), and
  Schroeder/Freeverb-style reverb (`reverb`).
- A streaming contract (`Effect.streaming`, `Effect.reset()`,
  `Chain.open_stream()` / `StreamSession`) and a real-time preview command:
  `vivoice stream`.
- Cooperative cancellation for long renders (`should_cancel` / `Cancelled`),
  wired to the GUI Cancel button.
- Case-insensitive duplicate detection in the model registry.
- `broadcast.yaml` and `phone.yaml` example presets.

### Fixed

- Robot effect carrier phase now continues across blocks instead of resetting
  (removes clicks in streaming).
- Echo and EQ filter state is carried across streaming blocks via filter `zi`
  state.
- HuggingFace downloads fail cleanly when the destination directory exists.
- Model removal only deletes directories inside the registry root.

## [0.1.0] - 2026-10-20

### Added

- Initial framework: audio core with `Effect`/`Chain`, gain/pitch/robot/echo
  effects, YAML presets, local model registry and HuggingFace pulls, PySide6
  GUI with an in-app bilingual user guide, headless CLI, CUDA auto-detection,
  CI, and bilingual documentation.
