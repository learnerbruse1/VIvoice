# Changelog

All notable changes to VIvoice are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

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
