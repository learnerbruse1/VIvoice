#!/usr/bin/env python3
"""Vendor the official MIT-licensed RVC repository at a pinned commit.

The vendored sources live in ``third_party/RVC`` (git-ignored), and the exact
commit is recorded in ``third_party/RVC_COMMIT.txt`` so builds are reproducible.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

RVC_REPOSITORY = "https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vendor the RVC repository at a pinned ref.")
    parser.add_argument("--ref", default="main", help="branch, tag, or commit to pin")
    parser.add_argument(
        "--target", type=Path, default=Path("third_party/RVC"), help="destination directory"
    )
    parser.add_argument("--force", action="store_true", help="replace an existing checkout")
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    target = (root / args.target).resolve()
    if not str(target).startswith(str(root)):
        print(f"error: target must stay inside the repository: {target}", file=sys.stderr)
        return 1

    if target.exists():
        if not args.force:
            print(f"RVC is already vendored at {target}. Use --force to replace it.")
            return 0
        shutil.rmtree(target)

    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"cloning {RVC_REPOSITORY} …")
    subprocess.run(["git", "clone", RVC_REPOSITORY, str(target)], check=True)
    subprocess.run(["git", "-C", str(target), "checkout", args.ref], check=True)

    commit = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    pin_file = root / "third_party" / "RVC_COMMIT.txt"
    pin_file.write_text(f"ref: {args.ref}\ncommit: {commit}\n", encoding="utf-8")

    if not (target / "LICENSE").is_file():
        print("error: LICENSE file not found in the vendored repository", file=sys.stderr)
        return 1

    print(f"vendored RVC at commit {commit} (ref {args.ref})")
    print("recorded pin in third_party/RVC_COMMIT.txt")
    print()
    print("Next steps:")
    print("  uv sync --extra ai")
    print("  uv pip install -r third_party/RVC/requirements.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
