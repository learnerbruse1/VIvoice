# AGENTS.md

Guidance for AI agents (and humans) working on VIvoice. This file is short on
purpose: the full working manual is [docs/AI_HANDBOOK.md](docs/AI_HANDBOOK.md).

## Start here

1. Read [CONTEXT.md](CONTEXT.md) for the project vocabulary and
   [docs/adr/](docs/adr/) for decisions you must not silently reverse.
2. Read [docs/AI_HANDBOOK.md](docs/AI_HANDBOOK.md) before writing code.
3. Never commit model weights or vendored sources: `third_party/*` is
   git-ignored; only `third_party/README.md` is tracked.

## Quality gates (must all pass)

```bash
uv sync --extra dev --extra realtime
uv run ruff check .
uv run mypy src
QT_QPA_PLATFORM=offscreen uv run pytest
```

## Non-negotiable invariants

- MIT-compatible dependencies only; check THIRD_PARTY_NOTICES.md first.
- The audio core has no mutable global state and effects are deterministic.
- Effects that claim `streaming`/`block_process` must satisfy the contracts in
  the handbook; there are tests that enforce this.
- Heavy work never runs on the GUI or audio thread.
