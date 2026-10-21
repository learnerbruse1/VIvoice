# AI Handbook

This handbook tells an AI agent everything it needs to extend VIvoice without
breaking the things that make it stable. Read it before editing code, and
update it when you add a new kind of extension point.

## 1. Mental model

VIvoice is a layered application with one shared engine:

```
GUI (PySide6) ─┐
CLI (argparse) ┴─► Chain ─► [Effect, Effect, ...] ─► audio files / real-time blocks
                        ├─► VoiceConversionAdapter (RVC, or third-party)
                        └─► Device resolver (CUDA → MPS → CPU)
```

Presets are YAML documents that name a chain of `type: params` entries. The
registry (`core/effect.py`) maps type strings to classes, so presets never
reference Python class names. The adapter registry (`ai/adapter.py`) does the
same for AI engines. See [ARCHITECTURE.md](ARCHITECTURE.md) and [adr/](adr/).

## 2. Invariants you must not break

1. **Determinism.** `Chain.process`/`render_file` call `Effect.reset()` first;
   the same input and parameters must always give the same output.
2. **No mutable global state in the core.** Effect state lives on the instance.
3. **float32, `(channels, frames)`, 48 kHz.** The AI layer converts to
   engine-native rates (RVC: 40 kHz) at the adapter boundary only.
4. **Streaming contracts.**
   - `streaming = True` means the effect works in `vivoice stream` via
     `process_stream` (default = `process`).
   - `block_process = True` means `process` itself accepts blocks with state
     carried across calls; `render_file` then renders in bounded memory with
     smooth progress and cancellation.
   - `tests/test_streaming.py` proves block-wise and whole-buffer processing
     agree; extend the parametrized list for new block effects.
5. **Never block the GUI/audio thread.** Use the workers in `gui/workers.py`.
6. **Licensing.** MIT-compatible dependencies only. GPL/AGPL/non-commercial
   code (Seed-VC, Applio, JUCE, Rubber Band) must stay out; see
   [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) and ADR-0002.
7. **Expected failures are `VivoiceError`.** Front-ends rely on that to show a
   friendly message instead of a traceback. Add subclasses in
   `core/errors.py`, not ad-hoc exceptions.

## 3. How to add an effect

See [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md). Minimum bar:

- subclass `Effect`, set `effect_type`, `default_params`, `param_constraints`;
- implement `process`; set `streaming`/`block_process` honestly;
- stateful effects implement `reset()` and satisfy contract 4;
- register by importing the module in `effects/__init__.py` or via the
  `vivoice.effects` entry point;
- add tests: property test, preset example if useful, docs row in
  [preset-format.md](preset-format.md), and a CHANGELOG entry.

## 4. How to add an AI engine

Implement `VoiceConversionAdapter` (`engine`, `sample_rate`, `convert`) and
register it with `register_adapter`, either in-tree or through the
`vivoice.adapters` entry point. The `voice-conversion` effect already handles
mono downmix, resampling, and channel restore; the adapter never sees
48 kHz stereo.

### RVC status (important)

Two engines ship today:

- **`rvc` (in-process).** Setup checks, device plumbing, lazy upstream
  imports, `VC.get_vc`/`vc_single` wiring, and the full
  downmix→resample→convert→restore pipeline are implemented. The wiring is
  unit-tested with a fake engine (`tests/test_rvc_adapter.py`) and the
  pipeline contract is pinned by `tests/test_voice_conversion.py`. Real
  inference needs PyTorch and the vendored repo: `uv sync --extra ai` then
  `python scripts/fetch_rvc.py`. Verify offline on CPU first, then CUDA;
  upstream RVC is sensitive to its Python/toolchain version, so a dedicated
  environment may be required.

- **`rvc-hub` (recommended, verified).** Uses the MIT-licensed
  `huggingface-hub-rvc` pipeline; loads the same community `.pth`/`.index`
  models without fairseq/av. Real CPU inference is verified end-to-end in this
  repository (`vivoice process` with an imported character model). It needs
  the `ai` extra and downloads base assets (hubert/rmvpe) from
  `lj1995/VoiceConversionWebUI` on first use. The adapter swaps
  `torchaudio.load/save` for a soundfile implementation so shared FFmpeg
  libraries are not required.

- **`rvc-http` (client/server).** Talks the protocol in
  [RVC_SERVER_PROTOCOL.md](RVC_SERVER_PROTOCOL.md) to `vivoice serve`
  (`src/vivoice/server.py`). The client is fully tested against a fake server
  (`tests/test_rvc_http.py`). The server performs real conversion through the
  `rvc-hub` engine (`convert_audio` in `src/vivoice/server.py`) and reports
  readiness dynamically on `/health`; it needs `uv sync --extra ai`.

Do not change the pipeline contract to make an engine fit; change the adapter.

### Network troubleshooting

- HuggingFace blocked? Set `HF_ENDPOINT=https://hf-mirror.com`.
- A proxy that intercepts TLS may break certificate verification. Export the
  Windows root certificates to a PEM file and set `REQUESTS_CA_BUNDLE` and
  `SSL_CERT_FILE` to it (the repository smoke test used this approach).
- After the first conversion, base assets (hubert/rmvpe) are cached under the
  HuggingFace cache; set `HF_HUB_OFFLINE=1` to skip the metadata refresh round
  trips that slow proxies can add to every run.

### CUDA acceleration

`uv.lock` pins the CPU PyTorch wheels for reproducible CI. On a CUDA machine,
install matching CUDA wheels explicitly:

```bash
uv pip install "torch==2.14.1+cu126" "torchaudio==2.11.0+cu126" \
  --index-url https://download.pytorch.org/whl/cu126
```

Verified on an NVIDIA RTX 4050: `vivoice devices` reports CUDA and `rvc-hub`
conversion runs on the GPU. The first GPU run compiles kernels and is slow;
subsequent runs are faster. Feature extraction and index retrieval timing
depend on the upstream pipeline.

## 5. Plugin entry points

Third-party packages register by declaring groups in `pyproject.toml`:

```toml
[project.entry-points."vivoice.effects"]
my-effect = "my_package.effects"

[project.entry-points."vivoice.adapters"]
my-engine = "my_package.adapter"
```

The pointed-to module registers itself on import. `load_plugins()` runs at CLI
and GUI startup. Introspection is available as `vivoice effects TYPE` and
`vivoice schema` (JSON), which is also the contract other tools should consume.

## 6. Configuration

User settings live in `~/.vivoice/config.yaml` (`VIVOICE_HOME` overrides the
directory) and are edited via `vivoice config list|get|set`. Keys:
`device`, `sample_rate`, `block_size`, `input_device`, `output_device`,
`log_level`. Validate any new key in `config.py::UserConfig._validate`.

## 7. Pitfalls that have already bitten us

- **scipy `lfilter` (≥1.18)** returns only `y` when `zi=None`. Always pass an
  explicit zero `zi` shaped `(channels, order)` and keep the returned `zf`.
- **Windows case-insensitivity.** Model names and registry lookups must use
  case-insensitive comparisons; tests cover this.
- **PCM16 quantization.** When comparing file round-trips, compare file to
  file, not file to in-memory float32 (the chunked-render test does this).
- **`EntryPoints.select` returns an iterable, not a list**, and old Pythons
  only have `.get`; `plugins.py` handles both.
- **Phase-vocoder direction.** Pitch shift = time-stretch by `factor`, then
  `resample_poly(up=1000, down=factor*1000)`. The streaming pitch shifter is a
  separate delay-line algorithm; do not mix the two paths.

## 8. Quality loop ("回环检查")

After any change, run the full loop in order:

```bash
uv lock
uv run ruff check .
uv run mypy src
QT_QPA_PLATFORM=offscreen uv run pytest
uv run vivoice --version && uv run vivoice effects
uv run vivoice process examples/../sample.wav out.wav --preset examples/presets/broadcast.yaml
uv run vivoice stream --list-devices
python -m compileall -q src tests scripts
```

Do not relax a test to hide a regression; fix the behavior instead. If a fix
needs a lower tolerance, explain the numerical reason in the test.

## 9. Roadmap handoffs

Next milestones are listed in [ROADMAP.md](ROADMAP.md). The next large,
verification-bound piece is real RVC inference (section 4). Packaging
(PyInstaller/Nuitka) and zero-shot reference-audio cloning come later and have
their own adapter/entry-point surfaces already defined.
