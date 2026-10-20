# Roadmap

Milestones are ordered by dependency, not by promise of delivery dates.

| Milestone | Scope | Status |
| --------- | ----- | ------ |
| v0.1 | Framework: engine, effects, presets, model registry, HuggingFace pulls, GUI + CLI, CUDA auto-detection, CI, bilingual docs | shipped in this repo |
| v0.2 | RVC integration hardening: real RVC inference through the adapter, model download UX, quality presets, progress and cancellation | planned |
| v0.3 | Effect quality: higher-quality pitch/formant shifting, noise gate, EQ; `Effect` block-processing contract for streaming | planned |
| v1.0 | Real-time streaming via sounddevice/PortAudio: DSP chain <50 ms; AI conversion labeled at its measured latency; VB-Cable routing guide | planned |
| v1.1 | Reference-audio cloning (OpenVoice-style zero-shot) behind the adapter; more engines | planned |
| v1.2 | Third-party effect/adapter plugins via Python entry points; installer packaging (PyInstaller/Nuitka) | planned |

## Explicit non-goals for now

- Bundling model weights in this repository
- Training voice models inside VIvoice (use the upstream RVC WebUI)
- Cloud services; VIvoice is local-first
