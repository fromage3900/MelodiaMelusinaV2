#!/usr/bin/env python3
"""
sculpt_intake_check.py - offline gate for Imports/Sculpt/Inbox drops.

No Unreal required. Blocks obvious foot-guns before an editor import:
  - empty / missing inbox
  - bad names
  - files over LimitMB (default 50 for collab-sized drops; use 512 for hero)
  - sidecar overwrite_existing:true
  - intended_ue_path that already has a tracked .uasset (redirector risk)

Usage:
  python Tools/sculpt_intake_check.py
  python Tools/sculpt_intake_check.py --limit-mb 50
  python Tools/sculpt_intake_check.py --inbox Imports/Sculpt/Inbox
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = ROOT / "Imports" / "Sculpt" / "Inbox"
NAME_RE = re.compile(r"^(SM|SK|T)_[A-Za-z0-9]+_.+_v\d{2}\.(fbx|obj|png|tga|exr)$", re.I)
MESH_SUFFIX = {".fbx", ".obj"}
TEX_SUFFIX = {".png", ".tga", ".exr", ".jpg", ".jpeg"}


def tracked_uasset_stems() -> set[str]:
    proc = subprocess.run(
        ["git", "ls-files", "Content"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    stems: set[str] = set()
    for line in proc.stdout.splitlines():
        p = Path(line)
        if p.suffix.lower() == ".uasset":
            stems.add(p.stem.lower())
    return stems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    parser.add_argument("--limit-mb", type=float, default=50.0)
    args = parser.parse_args()

    inbox: Path = args.inbox
    if not inbox.is_dir():
        print(f"FAIL: inbox missing: {inbox}", file=sys.stderr)
        return 1

    files = [
        p
        for p in sorted(inbox.iterdir())
        if p.is_file() and p.name not in {"README.md", ".gitkeep"}
    ]
    if not files:
        print(f"OK: inbox empty ({inbox}) - drop FBX when sculpt is ready.")
        return 0

    tracked = tracked_uasset_stems()
    limit = int(args.limit_mb * 1024 * 1024)
    errors: list[str] = []
    warnings: list[str] = []
    total = 0

    print(f"Sculpt inbox: {inbox} ({len(files)} files, limit {args.limit_mb:.0f} MB)")
    for path in files:
        size = path.stat().st_size
        total += size
        print(f"  {size / (1024 * 1024):7.2f} MB  {path.name}")

        if size == 0:
            errors.append(f"{path.name}: zero-byte")
        if size > limit:
            errors.append(f"{path.name}: {size / (1024 * 1024):.1f} MB > limit {args.limit_mb:.0f} MB")

        suffix = path.suffix.lower()
        if suffix in MESH_SUFFIX | TEX_SUFFIX:
            if not NAME_RE.match(path.name):
                warnings.append(
                    f"{path.name}: name should match SM_|SK_|T_<Role>_<Name>_vNN.ext"
                )
            stem = path.stem
            # strip _vNN for collision check against existing assets
            base = re.sub(r"_v\d{2}$", "", stem, flags=re.I)
            if base.lower() in tracked or stem.lower() in tracked:
                errors.append(
                    f"{path.name}: tracked Content already has '{base}' - "
                    "do NOT import onto that path (redirector risk). Use a new UE path."
                )

        if path.name.endswith(".sculpt.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.name}: invalid JSON ({exc})")
                continue
            if data.get("overwrite_existing") is True:
                errors.append(f"{path.name}: overwrite_existing must be false")
            ue = str(data.get("intended_ue_path", ""))
            if ue:
                leaf = ue.rstrip("/").split("/")[-1]
                if leaf.lower() in tracked:
                    errors.append(
                        f"{path.name}: intended_ue_path '{ue}' already exists in Content"
                    )

    print(f"Batch total: {total / (1024 * 1024):.2f} MB")
    if total > limit:
        errors.append(f"batch total {total / (1024 * 1024):.1f} MB exceeds {args.limit_mb:.0f} MB")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print("FAIL: fix inbox before UE import.", file=sys.stderr)
        return 1
    print("OK: sculpt inbox ready for a single LFS-aware import session.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
