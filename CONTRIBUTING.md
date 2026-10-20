# Contributing to VIvoice

Thanks for your interest in contributing! VIvoice is designed to be extended by
adding effects, voice-conversion adapters, and GUI pages without touching the
core engine.

## Development setup

```bash
git clone https://github.com/VIvoice/VIvoice.git
cd VIvoice
uv sync --extra dev --extra realtime
```

## Quality bar

Before opening a pull request, make sure these pass locally:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

- New behavior should ship with tests.
- The audio core must stay free of mutable global state.
- Blocking work (model inference, network downloads) must never run on the GUI
  or audio thread.
- All terms follow [CONTEXT.md](CONTEXT.md); if you need a new term, add it
  there.
- If your change is a hard-to-reverse design decision, add an ADR under
  `docs/adr/`.

## Where things go

- New DSP effect → `src/vivoice/effects/`, register it and document it in
  [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md).
- New AI engine → implement `VoiceConversionAdapter` in `src/vivoice/ai/`.
- New GUI page → add it to `src/vivoice/gui/`.

## Pull requests

1. Open an issue first for larger changes, and reference it in the PR.
2. Keep commits small and descriptive.
3. Update docs (README, user guide, glossary) when behavior changes.
4. Do not commit downloaded models or vendored third-party sources into git.

By submitting a pull request you agree to license your contribution under the
project's MIT license.
