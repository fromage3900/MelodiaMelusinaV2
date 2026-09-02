#!/usr/bin/env python3
"""Local, deterministic art-drop inventory and archive builder.

The command is intentionally offline: it never calls AWS, uploads, deletes, or
changes files in the project.  Inventory is constrained by a JSON manifest.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
from typing import Iterable

DEFAULT_EXCLUDES = (
    "Binaries", "Build", "DerivedDataCache", "Intermediate", "Saved",
    "Temp", ".git", "__pycache__", "Marketplace", "Fab", "_Archive",
)


def load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("include"), list):
        raise ValueError("manifest must be an object with an include list")
    return data


def _excluded(relative: str, patterns: Iterable[str]) -> bool:
    rel = PurePosixPath(relative)
    parts = set(rel.parts)
    for pattern in patterns:
        p = pattern.replace("\\", "/").strip("/")
        if not p:
            continue
        if p in parts or rel.match(p) or rel.match(f"**/{p}"):
            return True
    return False


def iter_files(root: Path, manifest: dict) -> tuple[list[Path], list[str]]:
    excludes = tuple(DEFAULT_EXCLUDES) + tuple(manifest.get("exclude", []))
    files: list[Path] = []
    missing: list[str] = []
    for item in manifest["include"]:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("manifest include entries must be non-empty strings")
        rel_item = item.replace("\\", "/").strip("/")
        candidate = (root / Path(rel_item)).resolve()
        if not candidate.is_relative_to(root.resolve()):
            raise ValueError(f"include path escapes root: {item}")
        if not candidate.exists():
            missing.append(rel_item)
            continue
        candidates = [candidate] if candidate.is_file() else sorted(candidate.rglob("*"))
        found = False
        for path in candidates:
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(root).as_posix()
            if not _excluded(rel, excludes):
                files.append(path)
                found = True
        if not found and candidate.is_dir():
            missing.append(rel_item)
    return sorted(set(files), key=lambda p: p.relative_to(root).as_posix()), missing


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path, manifest_path: Path) -> dict:
    manifest = load_manifest(manifest_path)
    files, missing = iter_files(root, manifest)
    entries = []
    for path in files:
        entries.append({
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        })
    return {
        "format": "bs-godfile-artdrop-v1",
        "manifest": manifest_path.name,
        "files": entries,
        "file_count": len(entries),
        "total_bytes": sum(item["size"] for item in entries),
        "missing_includes": missing,
    }


def write_bundle(root: Path, output: Path, report: dict) -> None:
    output = output.resolve()
    content = (root / "Content").resolve()
    if output == root.resolve() or output.is_relative_to(content):
        raise ValueError("archive output must be outside the project Content directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        # Suppress both the gzip timestamp and output filename. Explicitly
        # closing this wrapper writes the gzip trailer before the raw stream.
        with gzip.GzipFile(
            filename="", fileobj=stream, mode="wb", mtime=0
        ) as gzip_stream:
            with tarfile.open(
                fileobj=gzip_stream, mode="w", format=tarfile.PAX_FORMAT
            ) as archive:
                for item in report["files"]:
                    path = root / item["path"]
                    info = archive.gettarinfo(str(path), arcname=item["path"])
                    info.mtime = 0
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    with path.open("rb") as handle:
                        archive.addfile(info, handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, help="write JSON report outside the project if supplied")
    parser.add_argument("--create", type=Path, help="explicitly create a local .tar.gz outside Content")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = inventory(root, args.manifest.resolve())
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.report:
        if args.report.resolve().is_relative_to((root / "Content").resolve()):
            parser.error("--report must be outside Content")
        args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.report.resolve().write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    if args.create:
        write_bundle(root, args.create, report)
        print(f"created local archive: {args.create.resolve()}")
    return 2 if report["missing_includes"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
