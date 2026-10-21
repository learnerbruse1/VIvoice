#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

uv sync --extra ai --extra packaging
uv run pyinstaller --noconfirm --clean --console --name vivoice-ai \
    --collect-all vivoice \
    --collect-all huggingface_hub_rvc \
    --collect-all huggingface_hub \
    --collect-all transformers \
    --collect-all librosa \
    --collect-all soundfile \
    --collect-all faiss \
    --collect-all numba \
    --collect-all llvmlite \
    --collect-all torchaudio \
    --collect-all torchcodec \
    --copy-metadata torchcodec \
    --hidden-import huggingface_hub_rvc \
    --hidden-import torchaudio \
    --hidden-import torch \
    scripts/launch_cli.py
echo "AI artifact written to dist/vivoice-ai/"
