param(
    [string]$Name = "vivoice-ai"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    uv sync --extra ai --extra packaging
    uv run pyinstaller --noconfirm --clean --console --name $Name `
        --collect-all vivoice `
        --collect-all huggingface_hub_rvc `
        --collect-all huggingface_hub `
        --collect-all transformers `
        --collect-all librosa `
        --collect-all soundfile `
        --collect-all faiss `
        --collect-all numba `
        --collect-all llvmlite `
        --collect-all torchaudio `
        --collect-all torchcodec `
        --copy-metadata torchcodec `
        --hidden-import huggingface_hub_rvc `
        --hidden-import torchaudio `
        --hidden-import torch `
        "scripts/launch_cli.py"
    Write-Output "AI artifact written to dist/$Name/"
} finally {
    Pop-Location
}
