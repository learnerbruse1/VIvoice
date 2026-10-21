# Third-party notices

VIvoice itself is MIT licensed. This file documents the notable third-party
components and their licenses.

## Vendored components

| Component | License | Notes |
| --------- | ------- | ----- |
| [RVC-Project/Retrieval-based-Voice-Conversion-WebUI](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI) | MIT | Optional AI engine, fetched by `scripts/fetch_rvc.py` at a pinned commit into `third_party/RVC` (git-ignored). The commit hash is recorded in `third_party/RVC_COMMIT.txt`. |
| [huggingface-hub-rvc](https://pypi.org/project/huggingface-hub-rvc/) | MIT | Primary local RVC inference engine (`rvc-hub`). Reimplements the RVC architecture and loads classic RVC-WebUI `.pth`/`.index` models; base assets are fetched from `lj1995/VoiceConversionWebUI`. |

## Python dependencies

| Package | License |
| ------- | ------- |
| numpy | BSD-3-Clause |
| scipy | BSD-3-Clause |
| PyYAML | MIT |
| soundfile | BSD-3-Clause |
| PySide6 | LGPL-3.0 |
| huggingface-hub | Apache-2.0 |
| sounddevice (optional, realtime) | MIT |
| torch (optional, ai) | BSD-style |
| torchaudio, torchcodec (optional, ai) | BSD-style |
| huggingface-hub-rvc, librosa, safetensors, transformers (optional, ai) | MIT / Apache-2.0 |
| pytest, ruff, mypy (dev) | MIT |

## Licensing notes

- PySide6 (LGPL-3.0) is dynamically linked; VIvoice's MIT terms are not
  affected, and users may replace Qt as permitted by the LGPL.
- The following libraries were deliberately **not** adopted so that VIvoice can
  remain permissively licensed: Rubber Band (GPL/commercial), JUCE
  (AGPL/commercial), SoundTouch (LGPL), Seed-VC (GPL-3.0, archived), and Applio
  (MIT, non-commercial). See ADR-0002.

If you vendor an additional component, list it here with its license and keep a
copy of its license text in the vendored directory.
