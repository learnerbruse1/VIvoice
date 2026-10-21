param(
    [string]$Name = "vivoice"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    uv sync --extra dev --extra packaging
    uv run pyinstaller --noconfirm --clean --windowed `
        --name "$Name-gui" `
        --add-data "docs/USER_GUIDE.md;vivoice/resources" `
        "scripts/launch_gui.py"
    uv run pyinstaller --noconfirm --clean --console `
        --name "$Name" `
        --collect-all vivoice `
        "scripts/launch_cli.py"
    Write-Output "Artifacts written to dist/"
} finally {
    Pop-Location
}
