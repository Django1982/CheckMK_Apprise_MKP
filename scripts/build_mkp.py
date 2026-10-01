#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build the Checkmk MKP from ``src/local`` using only the standard library.

The archive is reproducible: fixed timestamps, owners and sorted members, so the
same sources always yield the same bytes. Usage::

    python scripts/build_mkp.py [--output-dir dist]

Layout of the MKP (gzip tar): ``info``, ``info.json`` and one inner tar per
Checkmk file part (``notifications.tar``, ``cmk_addons_plugins.tar``).
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import pprint
import tarfile
from pathlib import Path

PACKAGE_NAME = "apprise"
PACKAGE_VERSION = "0.2.0"  # SemVer
MIN_CHECKMK = "2.5.0"
# TODO(M0.2 smoke test): confirm the accepted value for version.packaged on a real 2.5 site.
PACKAGED_WITH = "2.5.0"

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL = REPO_ROOT / "src" / "local"

# Checkmk part name -> (source directory, mode override for files)
PARTS: dict[str, Path] = {
    "notifications": LOCAL / "share" / "check_mk" / "notifications",
    "cmk_addons_plugins": LOCAL / "lib" / "python3" / "cmk_addons" / "plugins",
}
EXECUTABLE_FILES = {("notifications", "apprise")}
IGNORED_NAMES = {".gitkeep", "__pycache__"}
FIXED_MTIME = 0


def collect_files(part: str) -> list[str]:
    root = PARTS[part]
    files = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not path.is_file() or IGNORED_NAMES & set(rel.parts) or path.suffix == ".pyc":
            continue
        files.append(rel.as_posix())
    return files


def _tar_bytes(part: str, files: list[str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for rel in files:
            data = (PARTS[part] / rel).read_bytes().replace(b"\r\n", b"\n")
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            info.mtime = FIXED_MTIME
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mode = 0o755 if (part, rel) in EXECUTABLE_FILES else 0o644
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def build_manifest(parts: dict[str, list[str]]) -> dict:
    return {
        "title": "Apprise notifications",
        "name": PACKAGE_NAME,
        "description": "Send Checkmk notifications to an Apprise API server.",
        "version": PACKAGE_VERSION,
        "version.packaged": PACKAGED_WITH,
        "version.min_required": MIN_CHECKMK,
        "version.usable_until": None,
        "author": "Daniel Heinen",
        "download_url": "",
        "files": parts,
    }


def build_mkp() -> tuple[str, bytes]:
    parts = {part: collect_files(part) for part in PARTS}
    parts = {part: files for part, files in parts.items() if files}
    manifest = build_manifest(parts)

    members: dict[str, bytes] = {
        "info": (pprint.pformat(manifest) + "\n").encode(),
        "info.json": (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
    }
    for part, files in parts.items():
        members[f"{part}.tar"] = _tar_bytes(part, files)

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for name in sorted(members):
            info = tarfile.TarInfo(name)
            info.size = len(members[name])
            info.mtime = FIXED_MTIME
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(members[name]))
    compressed = gzip.compress(buf.getvalue(), mtime=0)
    return f"{PACKAGE_NAME}-{PACKAGE_VERSION}.mkp", compressed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(REPO_ROOT / "dist"))
    args = parser.parse_args()
    filename, data = build_mkp()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / filename).write_bytes(data)
    print(f"Built {out / filename} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
