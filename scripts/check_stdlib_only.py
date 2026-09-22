#!/usr/bin/env python3
"""Fail if any tooling script imports something that is not the standard library.

This repository promises that a contributor can run the tooling with the Python
they already have: no pip install, no npm, no lockfile, no virtualenv. That
promise is easy to break accidentally with one convenient import, so CI checks
it. An allow-list rather than `sys.stdlib_module_names` keeps the check working
on older Python versions too.

Usage:
    python3 scripts/check_stdlib_only.py
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every standard-library module the tooling is allowed to use.
ALLOWED = {
    "__future__",
    "argparse",
    "ast",
    "csv",
    "datetime",
    "html",
    "io",
    "json",
    "os",
    "pathlib",
    "re",
    "socket",
    "sys",
    "time",
    "urllib",
    "concurrent",
    "check_stdlib_only",
    "enrich_brreg",
    "fetch_signals",
    "build",
    "validate",
    "linkcheck",
}


def main() -> int:
    offenders: list[str] = []
    checked = 0
    for path in sorted((ROOT / "scripts").glob("*.py")):
        checked += 1
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root not in ALLOWED:
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import within this package
                    continue
                root = (node.module or "").split(".")[0]
                if root and root not in ALLOWED:
                    offenders.append(f"{path.name}: from {node.module} import ...")

    if offenders:
        print("third-party imports found -- this breaks the zero-dependency promise:")
        for offender in offenders:
            print(f"  - {offender}")
        return 1

    print(f"checked {checked} scripts: standard library only, no third-party imports")
    return 0


if __name__ == "__main__":
    sys.exit(main())
