# Packaging

The recommended way to run VIvoice is `uv sync` from the repository. For
distribution to end users, PyInstaller builds are provided.

The build tooling is a first-class optional dependency:

```bash
uv sync --extra packaging
```

```bash
# Windows (PowerShell)
scripts/build_pyinstaller.ps1

# macOS / Linux
scripts/build_pyinstaller.sh
```

Output: `dist/vivoice-gui/` (windowed app) and `dist/vivoice/` (console CLI).
The user guide is bundled into the GUI so the in-app "User guide" page works
without the repository.

For a self-contained build that includes the AI engine (PyTorch, rvc-hub,
faiss — a multi-GB bundle):

```bash
# Windows (PowerShell)
scripts/build_pyinstaller_ai.ps1

# macOS / Linux
scripts/build_pyinstaller_ai.sh
```

The AI bundle collects the heavyweight dependencies explicitly (numba,
llvmlite, transformers, torchcodec metadata, faiss). It has been verified to
perform a real voice conversion on Windows.

Notes:

- Build on each target OS; PyInstaller binaries are not cross-platform.
- The optional AI engine is large. Include it in the build with
  `uv sync --extra ai` before packaging and expect a multi-GB bundle.
- The HTTP engine (`rvc-http`) keeps heavy RVC dependencies out of the bundle:
  ship the GUI/CLI without PyTorch and run `vivoice serve` on the machine that
  has the RVC environment.
- CI builds artifacts on every version tag via
  `.github/workflows/release.yml`.
