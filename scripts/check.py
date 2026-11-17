# /// script
# requires-python = ">=3.10"
# dependencies = ["h5py", "pyyaml"]
# ///
"""Check the layout of the repository, the meta.yml files and that every .h5 file opens."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import h5py
import yaml

ROOT = Path(__file__).resolve().parent.parent
#: Top-level directories that hold no results.
SKIP = {".git", ".github", "scripts"}
META_KEYS = {"label", "date", "info"}
MAX_BYTES = 50_000_000


def check_meta(path: Path, errors: list[str]) -> None:
    """A meta.yml is a mapping of label, date and info."""
    try:
        meta = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{path}: not valid YAML: {exc}")
        return
    if not isinstance(meta, dict):
        errors.append(f"{path}: must be a mapping")
        return
    unknown = set(meta) - META_KEYS
    if unknown:
        errors.append(
            f"{path}: unknown keys {sorted(unknown)} (allowed: {sorted(META_KEYS)})"
        )
    if "date" in meta and not isinstance(meta["date"], (datetime.date, str)):
        errors.append(f"{path}: date must be a date such as 2026-11-17")
    if "info" in meta and not isinstance(meta["info"], dict):
        errors.append(f"{path}: info must be a mapping")


def check_run(path: Path, errors: list[str]) -> None:
    """A run file opens with h5py and is not too large."""
    if path.stat().st_size > MAX_BYTES:
        errors.append(f"{path}: larger than {MAX_BYTES // 1_000_000} MB")
    try:
        with h5py.File(path, "r"):
            pass
    except OSError as exc:
        errors.append(f"{path}: cannot be opened: {exc}")


def check_execution(directory: Path, errors: list[str]) -> int:
    """An execution holds run files and optionally meta.yml; returns the number of runs."""
    runs = 0
    for item in sorted(directory.iterdir()):
        if item.is_dir():
            errors.append(
                f"{item}: an execution holds files only (<code>/<case>/<execution>/)"
            )
        elif item.name == "meta.yml":
            check_meta(item, errors)
        elif item.suffix == ".h5":
            check_run(item, errors)
            runs += 1
    if runs == 0:
        errors.append(f"{directory}: no .h5 files")
    return runs


def main() -> int:
    errors: list[str] = []
    runs = 0
    for code in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP):
        for case in sorted(p for p in code.iterdir() if p.is_dir()):
            for item in sorted(case.iterdir()):
                if item.is_dir():
                    runs += check_execution(item, errors)
                else:
                    errors.append(
                        f"{item}: files go into an execution directory (<case>/<execution>/)"
                    )
        for item in code.iterdir():
            if item.is_file() and item.suffix == ".h5":
                errors.append(f"{item}: runs go into <code>/<case>/<execution>/")
    for error in errors:
        print(error, file=sys.stderr)
    print(f"{runs} run files checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
