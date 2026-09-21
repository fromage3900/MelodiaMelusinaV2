#!/usr/bin/env python3
"""Melodia Studio LIVE gate — AppData addon must match this checkout.

Host (no bpy) or Blender:

  python Tools/melodia_studio_live_gate.py
  blender.exe --background --factory-startup --python Tools/melodia_studio_live_gate.py

LIVE proof requires the checkout sync helper to expose live-only refusal
(``live_only_files``). That API landed in #253. This gate fails closed if it is
absent, so #251 cannot be live-installed through this banner.

Does not install. Does not invent live evidence.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Final

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from melodia_studio_pathbind import (
    SourceBindError,
    argv_after_double_dash,
    bind_live_addons,
    checkout_root_from_this_file,
    measured_builder_ids,
    purge_surreal_arch_modules,
)

BANNER_PASS: Final[str] = "MELODIA STUDIO LIVE GATE: PASS"
BANNER_FAIL: Final[str] = "MELODIA STUDIO LIVE GATE: FAIL"
PROVENANCE_REL: Final[tuple[str, ...]] = (
    "Blender Foundation",
    "Blender",
    "5.2",
    "scripts",
    "addons",
    "melodia_studio_sync_provenance.json",
)
SOURCE_JSON_REL: Final[str] = "Saved/Audit/melodia_studio_source_registry.json"
REQUIRED_SYNC_ATTRS: Final[tuple[str, ...]] = (
    "live_only_files",
    "verify",
    "sync",
)


class LiveGateError(RuntimeError):
    """Fail-closed LIVE assertion. Never swallowed into a PASS."""


@dataclass(slots=True)
class LiveGateReport:
    ok: bool
    checkout_root: str
    sync_helper: str
    live_only: list[str]
    check_ok: bool
    provenance_head: str
    provenance_branch: str
    live_registry_count: int | None
    source_registry_count: int | None
    registry_delta: list[str]
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": "melodia.studio.live_gate.v1",
            "ok": self.ok,
            "checkout_root": self.checkout_root,
            "sync_helper": self.sync_helper,
            "live_only": self.live_only,
            "check_ok": self.check_ok,
            "provenance_head": self.provenance_head,
            "provenance_branch": self.provenance_branch,
            "live_registry_count": self.live_registry_count,
            "source_registry_count": self.source_registry_count,
            "registry_delta": self.registry_delta,
            "errors": self.errors,
        }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Melodia Studio LIVE gate")
    parser.add_argument(
        "--checkout-root",
        default="",
        help="Repo root. Default: parent of Tools/ containing this script.",
    )
    parser.add_argument(
        "--source-json",
        default="",
        help="SOURCE gate JSON to compare live registry against.",
    )
    parser.add_argument(
        "--skip-blender-registry",
        action="store_true",
        help="Host-only: sync --check + live-only + provenance. No bpy import.",
    )
    return parser.parse_args(list(argv))


def load_sync_module(checkout_root: Path) -> ModuleType:
    path = checkout_root / "deploy" / "_sync_addon_to_blender_5_2.py"
    if not path.is_file():
        raise LiveGateError(f"missing sync helper: {path}")
    spec = importlib.util.spec_from_file_location("melodia_studio_sync_checkout", path)
    if spec is None or spec.loader is None:
        raise LiveGateError(f"cannot create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    missing = [name for name in REQUIRED_SYNC_ATTRS if not callable(getattr(module, name, None))]
    if missing:
        raise LiveGateError(
            "checkout sync helper is missing the live-only API "
            f"{missing}; LIVE install is blocked until that guard is in THIS checkout"
        )
    return module


def git_text(root: Path, *git_args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *git_args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def provenance_path() -> Path:
    import os  # noqa: PLC0415

    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise LiveGateError("APPDATA is not set")
    return Path(appdata).joinpath(*PROVENANCE_REL)


def read_provenance() -> tuple[str, str]:
    path = provenance_path()
    if not path.is_file():
        raise LiveGateError(f"missing live provenance: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise LiveGateError("provenance JSON is not an object")
    head = payload.get("head") or payload.get("HEAD") or payload.get("source_head")
    branch = payload.get("branch") or payload.get("source_branch")
    if not isinstance(head, str) or not head:
        raise LiveGateError(f"provenance missing head: keys={sorted(payload)}")
    if not isinstance(branch, str):
        branch = ""
    return head, branch


def load_source_ids(path: Path) -> frozenset[str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise LiveGateError("SOURCE JSON is not an object")
    if payload.get("ok") is not True:
        raise LiveGateError("refusing LIVE compare against a failed SOURCE JSON")
    ids = payload.get("builder_ids")
    if not isinstance(ids, list) or not all(isinstance(item, str) and item for item in ids):
        raise LiveGateError("SOURCE JSON builder_ids is not a list of strings")
    return frozenset(ids)


def measure_live_registry() -> frozenset[str]:
    addon_root = bind_live_addons()
    import surreal_arch.melodia_gn as gn  # noqa: PLC0415
    from surreal_arch.melodia_gn import core as gn_core  # noqa: PLC0415

    gn_file = Path(getattr(gn, "__file__", "") or "")
    if not gn_file.is_file():
        raise LiveGateError("live melodia_gn.__file__ is missing")
    expected = addon_root / "surreal_arch" / "melodia_gn" / "__init__.py"
    if not gn_file.resolve().samefile(expected):
        raise LiveGateError(
            f"LIVE import origin mismatch: {gn_file.resolve()} vs {expected}"
        )
    builders = measured_builder_ids(gn_core.GROUP_BUILDERS)
    return frozenset(builders)


def run(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    checkout = (
        Path(args.checkout_root).expanduser().resolve()
        if args.checkout_root
        else checkout_root_from_this_file(Path(__file__))
    )

    live_only: list[str] = []
    check_ok = False
    provenance_head = ""
    provenance_branch = ""
    live_count: int | None = None
    source_count: int | None = None
    delta: list[str] = []
    sync_path = str(checkout / "deploy" / "_sync_addon_to_blender_5_2.py")

    try:
        sync_mod = load_sync_module(checkout)
        live_only = list(sync_mod.live_only_files(checkout))
        if live_only:
            raise LiveGateError(
                f"LIVE-ONLY managed files present ({len(live_only)}); refusing LIVE PASS"
            )
        check_ok = bool(sync_mod.verify(checkout))
        if not check_ok:
            raise LiveGateError("sync --check is not green for this checkout")
        provenance_head, provenance_branch = read_provenance()
        checkout_head = git_text(checkout, "rev-parse", "HEAD")
        if not checkout_head:
            raise LiveGateError("cannot resolve checkout HEAD")
        if provenance_head != checkout_head:
            raise LiveGateError(
                f"provenance head {provenance_head} != checkout HEAD {checkout_head}"
            )
    except (LiveGateError, SourceBindError, OSError, TypeError, ValueError) as exc:
        errors.append(str(exc))

    if not errors and not args.skip_blender_registry:
        try:
            import bpy  # noqa: PLC0415, F401
        except ImportError:
            errors.append(
                "bpy unavailable; rerun under Blender or pass --skip-blender-registry "
                "for host-only check (not full LIVE proof)"
            )
        else:
            try:
                source_json = (
                    Path(args.source_json).resolve()
                    if args.source_json
                    else checkout / SOURCE_JSON_REL
                )
                if not source_json.is_file():
                    raise LiveGateError(
                        f"missing SOURCE JSON {source_json}; run SOURCE gate first"
                    )
                source_ids = load_source_ids(source_json)
                source_count = len(source_ids)
                live_ids = measure_live_registry()
                live_count = len(live_ids)
                only_live = sorted(live_ids - source_ids)
                only_source = sorted(source_ids - live_ids)
                delta = [f"+live:{item}" for item in only_live] + [
                    f"-live:{item}" for item in only_source
                ]
                if delta:
                    raise LiveGateError(
                        "live registry != SOURCE registry: " + ", ".join(delta[:20])
                    )
            except (LiveGateError, SourceBindError) as exc:
                errors.append(str(exc))
            finally:
                purge_surreal_arch_modules()

    ok = not errors
    report = LiveGateReport(
        ok=ok,
        checkout_root=str(checkout),
        sync_helper=sync_path,
        live_only=live_only,
        check_ok=check_ok,
        provenance_head=provenance_head,
        provenance_branch=provenance_branch,
        live_registry_count=live_count,
        source_registry_count=source_count,
        registry_delta=delta,
        errors=errors,
    )
    print("LIVE checkout:", report.checkout_root)
    print("LIVE sync helper:", report.sync_helper)
    print("LIVE-ONLY count:", len(report.live_only))
    print("LIVE check_ok:", report.check_ok)
    print("LIVE provenance:", report.provenance_branch, report.provenance_head)
    print("LIVE registry:", report.live_registry_count)
    print("SOURCE registry:", report.source_registry_count)
    for error in errors:
        print("LIVE error:", error)
    print(BANNER_PASS if ok else BANNER_FAIL)
    return 0 if ok else 1


def main() -> int:
    tools_dir = str(Path(__file__).resolve().parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    return run(argv_after_double_dash(sys.argv))


if __name__ == "__main__":
    raise SystemExit(main())
