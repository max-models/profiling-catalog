# /// script
# requires-python = ">=3.10"
# dependencies = ["h5py", "pyyaml"]
# ///
"""Check the layout of the repository, the metadata files and that every .h5 file opens.

The results live in ``<code>/<case>/<execution>/``. An execution is either a folder that
``scope-profiler jobs --upload`` wrote (``case_metadata.json``, ``inputs/``, ``run01/`` with
``profiling_data.h5`` and ``run_metadata.json``, ...) or one put together by hand (``np1.h5``,
``np2.h5``, ... and an optional ``meta.yml``).
"""

from __future__ import annotations

import datetime
import json
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


def check_json(path: Path, errors: list[str]) -> None:
    """A metadata file of a profiling job is a JSON object."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        errors.append(f"{path}: not valid JSON: {exc}")
        return
    if not isinstance(value, dict):
        errors.append(f"{path}: must be a JSON object")


def check_run(path: Path, errors: list[str]) -> None:
    """A run file opens with h5py."""
    try:
        with h5py.File(path, "r"):
            pass
    except OSError as exc:
        errors.append(f"{path}: cannot be opened: {exc}")


def check_execution(directory: Path, errors: list[str]) -> int:
    """One execution of a case; returns the number of run files in it."""
    runs = 0
    for item in sorted(directory.rglob("*")):
        if not item.is_file():
            continue
        if item.stat().st_size > MAX_BYTES:
            errors.append(f"{item}: larger than {MAX_BYTES // 1_000_000} MB")
        if item.name == "meta.yml" and item.parent == directory:
            check_meta(item, errors)
        elif item.name in ("case_metadata.json", "run_metadata.json"):
            check_json(item, errors)
        elif item.suffix == ".h5":
            check_run(item, errors)
            runs += 1
    if runs == 0:
        errors.append(f"{directory}: no .h5 files")
    return runs


def main() -> int:
    errors: list[str] = []
    runs = 0
    for code in sorted(
        p
        for p in ROOT.iterdir()
        if p.is_dir() and p.name not in SKIP and not p.name.startswith(".")
    ):
        for item in sorted(code.iterdir()):
            if item.is_file() and item.suffix == ".h5":
                errors.append(f"{item}: runs go into <code>/<case>/<execution>/")
            if not item.is_dir():
                continue
            for execution in sorted(item.iterdir()):
                if execution.is_dir():
                    runs += check_execution(execution, errors)
                else:
                    errors.append(
                        f"{execution}: files go into an execution directory "
                        "(<code>/<case>/<execution>/)"
                    )
    for error in errors:
        print(error, file=sys.stderr)
    print(f"{runs} run files checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
