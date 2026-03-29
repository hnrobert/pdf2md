#!/usr/bin/env python3
"""Bump project version in pyproject.toml and package __init__.py."""

from __future__ import annotations

import pathlib
import re
import sys

SEMVER_PATTERN = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?(?:\+([0-9A-Za-z.-]+))?$"
)


def normalize_version(raw: str) -> str:
    text = raw.strip()
    match = SEMVER_PATTERN.match(text)
    if not match:
        raise ValueError(f"Invalid semver version: {raw}")

    major, minor, patch, prerelease, build = match.groups()
    normalized = f"{major}.{minor}.{patch}"
    if prerelease:
        normalized += f"-{prerelease}"
    if build:
        normalized += f"+{build}"
    return normalized


def replace_once(content: str, pattern: str, replacement: str, path: pathlib.Path) -> str:
    updated, count = re.subn(pattern, replacement, content, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Could not update {path}")
    return updated


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <version>", file=sys.stderr)
        return 1

    try:
        version = normalize_version(sys.argv[1])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    root = pathlib.Path(__file__).resolve().parent.parent
    init_file = root / "pdf2dotmd" / "__init__.py"
    pyproject_file = root / "pyproject.toml"

    init_content = init_file.read_text(encoding="utf-8")
    pyproject_content = pyproject_file.read_text(encoding="utf-8")

    init_updated = replace_once(
        init_content,
        r'^__version__\s*=\s*"[^"]+"',
        f'__version__ = "{version}"',
        init_file,
    )
    pyproject_updated = replace_once(
        pyproject_content,
        r'^version\s*=\s*"[^"]+"',
        f'version = "{version}"',
        pyproject_file,
    )

    init_file.write_text(init_updated, encoding="utf-8")
    pyproject_file.write_text(pyproject_updated, encoding="utf-8")

    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
