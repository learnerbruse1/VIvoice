#!/usr/bin/env python3
"""Thin wrapper so the reference server can be run from a checkout without an
installed VIvoice package."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from vivoice.server import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
