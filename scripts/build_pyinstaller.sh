#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

uv sync --extra dev --extra packaging
uv run pyinstaller --noconfirm --clean --windowed \
    --name vivoice-gui \
    --add-data "docs/USER_GUIDE.md:vivoice/resources" \
    scripts/launch_gui.py
uv run pyinstaller --noconfirm --clean --console \
    --name vivoice \
    --collect-all vivoice \
    scripts/launch_cli.py
echo "Artifacts written to dist/"
