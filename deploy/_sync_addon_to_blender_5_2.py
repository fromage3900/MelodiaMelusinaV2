"""Deterministically sync the current checkout's Melodia Studio deploy tree to Blender 5.2.

The source of truth is the checkout that contains THIS script. Older versions silently
preferred C:\\EnvironmentPortfolio\\BS_GodFile\\deploy when that directory existed, which
could install stale code from a different clone on a second workstation.

Usage:
    python deploy/_sync_addon_to_blender_5_2.py
    python deploy/_sync_addon_to_blender_5_2.py --check
    python deploy/_sync_addon_to_blender_5_2.py --source-root C:\\explicit\\MelodiaMelusinaV2
    python deploy/_sync_addon_to_blender_5_2.py --allow-live-only-delete

--source-root is the only way to override the current checkout. There is no implicit
machine-specific source path. A normal install refuses to remove managed files that exist
only in the live addon; --allow-live-only-delete is the explicit destructive override.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve()
DEFAULT_PROJECT_ROOT = SCRIPT.parent.parent
BLENDER_VERSION = "5.2"
ADDON_ROOT = (
    Path(os.environ.get("APPDATA", ""))
    / "Blender Foundation"
    / "Blender"
    / BLENDER_VERSION
    / "scripts"
    / "addons"
)
PROVENANCE_PATH = ADDON_ROOT / "melodia_studio_sync_provenance.json"
PACKAGE_NAMES = ("surreal_arch", "surreal_os", "surreal_world", "surreal_greybox")
IGNORED_NAMES = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync/check Melodia Studio live Blender addon")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Read-only: verify live addon bytes/provenance against the selected checkout.",
    )
    parser.add_argument(
        "--source-root",
        default="",
        help="Explicit Melodia repository root. By default the checkout containing this script wins.",
    )
    parser.add_argument(
        "--allow-live-only-delete",
        action="store_true",
        help=(
            "Destructive override: permit sync to remove files under managed addon packages "
            "that exist live but not in the selected checkout."
        ),
    )
    return parser.parse_args()


def resolve_project_root(raw: str) -> Path:
    root = Path(raw).expanduser().resolve() if raw else DEFAULT_PROJECT_ROOT
    deploy = root / "deploy"
    required = (deploy / "surreal_arch", deploy / "surreal_architecture_gen.py")
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "Selected source root is not a complete Melodia deploy checkout; missing: "
            + ", ".join(missing)
        )
    return root


def git_text(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_source_files(deploy: Path):
    monolith = deploy / "surreal_architecture_gen.py"
    yield monolith, ADDON_ROOT / monolith.name

    for package_name in PACKAGE_NAMES:
        source_root = deploy / package_name
        if not source_root.is_dir():
            continue
        dest_root = ADDON_ROOT / package_name
        for source in source_root.rglob("*"):
            if not source.is_file():
                continue
            if any(part in IGNORED_NAMES for part in source.parts):
                continue
            if source.suffix.lower() in IGNORED_SUFFIXES:
                continue
            yield source, dest_root / source.relative_to(source_root)


def expected_manifest(project_root: Path) -> dict[str, str]:
    deploy = project_root / "deploy"
    return {
        str(dest.relative_to(ADDON_ROOT)).replace("\\", "/"): sha256(source)
        for source, dest in iter_source_files(deploy)
    }


def live_manifest(project_root: Path) -> tuple[dict[str, str], list[str]]:
    expected = expected_manifest(project_root)
    present: dict[str, str] = {}
    missing: list[str] = []
    for rel in expected:
        path = ADDON_ROOT / Path(rel)
        if not path.is_file():
            missing.append(rel)
            continue
        present[rel] = sha256(path)
    return present, missing


def live_only_files(project_root: Path) -> list[str]:
    """Return managed live-addon files that do not exist in the checkout.

    These are the files package replacement would otherwise silently delete. The scan is
    intentionally limited to PACKAGE_NAMES so unrelated Blender addons are never treated
    as Melodia Studio output.
    """
    expected = expected_manifest(project_root)
    extras: list[str] = []
    for package_name in PACKAGE_NAMES:
        live_root = ADDON_ROOT / package_name
        if not live_root.is_dir():
            continue
        for path in live_root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORED_NAMES for part in path.parts):
                continue
            if path.suffix.lower() in IGNORED_SUFFIXES:
                continue
            rel = str(path.relative_to(ADDON_ROOT)).replace("\\", "/")
            if rel not in expected:
                extras.append(rel)
    return sorted(extras)


def provenance(project_root: Path, manifest: dict[str, str]) -> dict:
    return {
        "schema": "melodia.blender_live_sync.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "blender_version": BLENDER_VERSION,
        "source_project_root": str(project_root),
        "source_deploy_root": str(project_root / "deploy"),
        "git_head": git_text(project_root, "rev-parse", "HEAD"),
        "git_branch": git_text(project_root, "branch", "--show-current"),
        "file_count": len(manifest),
        "manifest_sha256": hashlib.sha256(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }


def read_provenance() -> dict:
    if not PROVENANCE_PATH.is_file():
        return {}
    try:
        return json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def verify(project_root: Path, *, require_provenance: bool = True) -> bool:
    expected = expected_manifest(project_root)
    present, missing = live_manifest(project_root)
    mismatched = [rel for rel, digest in expected.items() if present.get(rel) not in (None, digest)]

    prov = read_provenance()
    expected_head = git_text(project_root, "rev-parse", "HEAD")
    expected_branch = git_text(project_root, "branch", "--show-current")
    provenance_ok = bool(prov)
    if require_provenance:
        provenance_ok = (
            prov.get("git_head") == expected_head
            and prov.get("git_branch") == expected_branch
            and Path(prov.get("source_project_root", "")).resolve() == project_root.resolve()
        )

    print(f"Source checkout: {project_root}")
    print(f"Source branch:   {expected_branch or '(detached)'}")
    print(f"Source HEAD:     {expected_head or '(unknown)'}")
    print(f"Live addon:      {ADDON_ROOT}")
    print(
        f"Live byte check: {len(expected) - len(missing) - len(mismatched)}/{len(expected)} match"
    )

    if missing:
        print(f"MISSING live files ({len(missing)}):")
        for rel in missing[:20]:
            print(f"  {rel}")
    if mismatched:
        print(f"STALE live files ({len(mismatched)}):")
        for rel in mismatched[:20]:
            print(f"  {rel}")

    live_only = live_only_files(project_root)
    if live_only:
        print(
            f"LIVE-ONLY managed files ({len(live_only)}): present in AppData but absent "
            "from this checkout; a package replacement would delete them:"
        )
        for rel in live_only[:20]:
            print(f"  {rel}")
        if len(live_only) > 20:
            print(f"  ... and {len(live_only) - 20} more")

    if require_provenance and not provenance_ok:
        print("STALE/MISSING provenance: live addon is not stamped from this exact checkout + HEAD.")

    ok = (
        not missing
        and not mismatched
        and not live_only
        and (provenance_ok or not require_provenance)
    )
    print("LIVE ADDON SYNC: OK" if ok else "LIVE ADDON SYNC: OUT OF DATE")
    return ok


def sync(project_root: Path, *, allow_live_only_delete: bool = False) -> bool:
    deploy = project_root / "deploy"
    ADDON_ROOT.mkdir(parents=True, exist_ok=True)

    live_only = live_only_files(project_root)
    if live_only and not allow_live_only_delete:
        print(
            "REFUSING TO SYNC: managed live-only files exist and package replacement "
            "would delete them.",
            file=sys.stderr,
        )
        for rel in live_only:
            print(f"  {rel}", file=sys.stderr)
        print(
            "Recover or intentionally remove those files first. If deletion is deliberate, "
            "rerun with --allow-live-only-delete.",
            file=sys.stderr,
        )
        return False
    if live_only:
        print(
            f"WARNING: --allow-live-only-delete permits deletion of {len(live_only)} "
            "managed live-only file(s):"
        )
        for rel in live_only:
            print(f"  {rel}")

    print(f"Source checkout: {project_root}")
    print(f"Source branch:   {git_text(project_root, 'branch', '--show-current') or '(detached)'}")
    print(f"Source HEAD:     {git_text(project_root, 'rev-parse', 'HEAD') or '(unknown)'}")
    print(f"Target addons:   {ADDON_ROOT}")

    for package_name in PACKAGE_NAMES:
        source = deploy / package_name
        if not source.is_dir():
            print(f"  {package_name}: source absent; skipped")
            continue
        destination = ADDON_ROOT / package_name
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        count = sum(1 for p in source.rglob("*") if p.is_file())
        print(f"  {package_name}: synced ({count} source file(s))")

    monolith_src = deploy / "surreal_architecture_gen.py"
    monolith_dst = ADDON_ROOT / "surreal_architecture_gen.py"
    shutil.copy2(monolith_src, monolith_dst)
    print(f"  monolith: synced ({monolith_src.stat().st_size} bytes)")

    for pycache in ADDON_ROOT.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)

    manifest = expected_manifest(project_root)
    PROVENANCE_PATH.write_text(
        json.dumps(provenance(project_root, manifest), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  provenance: {PROVENANCE_PATH}")
    return verify(project_root)


def main() -> int:
    args = parse_args()
    try:
        project_root = resolve_project_root(args.source_root)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not os.environ.get("APPDATA"):
        print("ERROR: APPDATA is not set; cannot locate Blender live addons.", file=sys.stderr)
        return 2

    if args.check:
        return 0 if verify(project_root) else 1
    return 0 if sync(
        project_root,
        allow_live_only_delete=args.allow_live_only_delete,
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
