# Roadmap

Milestones are ordered by dependency, not by promise of delivery dates.

| Milestone | Scope | Status |
| --------- | ----- | ------ |
| v0.1 | Framework: engine, effects, presets, model registry, HuggingFace pulls, GUI + CLI, CUDA auto-detection, CI, bilingual docs | shipped |
| v0.2 | EQ / noise-gate / reverb effects, streaming contract and `vivoice stream` real-time preview, cooperative cancellation, registry robustness fixes | shipped |
| v0.3 | Chunked bounded-memory rendering, streaming pitch shifter, entry-point plugins, param schemas, user config, end-to-end voice-conversion pipeline tests (fake adapter), AI handbook | shipped |
| v0.4 | RVC dual path (in-process wiring + `rvc-http` client/server), GUI Live page, packaging configuration and release workflow | shipped |
| v0.5 | Real RVC inference through `rvc-hub` verified end-to-end on CPU; soundfile-based decode shim; network troubleshooting docs | shipped |
| v0.6 | Targeted model downloads and a fully functional conversion server (`server.convert_audio` via rvc-hub) | shipped |
| v0.7 | Formant-shift effect, `vivoice doctor` diagnostics, checkpoint format validation, GUI download status | shipped |
| v0.8 | Verify CUDA acceleration on a GPU machine; build and verify an AI-enabled distribution bundle | planned |
| v0.9 | Effect quality: higher-quality pitch/formant shifting; more engines behind the adapter | planned |
| v1.0 | Full real-time streaming: pitch and AI conversion in the stream path, DSP chain <50 ms, VB-Cable routing guide | planned |
| v1.1 | Reference-audio cloning (OpenVoice-style zero-shot) behind the adapter; more engines | planned |
| v1.2 | Third-party effect/adapter plugins via Python entry points; installer packaging (PyInstaller/Nuitka) | planned |

## Explicit non-goals for now

- Bundling model weights in this repository
- Training voice models inside VIvoice (use the upstream RVC WebUI)
- Cloud services; VIvoice is local-first
