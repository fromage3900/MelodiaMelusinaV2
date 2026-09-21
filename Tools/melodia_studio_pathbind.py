#!/usr/bin/env python3
"""Typed checkout vs AppData path binding for Melodia Studio gates.

This module is the SOURCE/LIVE contract. It does not grep builder files, does
not trust PYTHONPATH, and does not leave Blender user addons on sys.path during
a SOURCE bind. Import origin is proven by the bound package's ``__file__``.
"""
from __future__ import annotations

import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final

BLENDER_VERSION: Final[str] = "5.2"


class SourceBindError(RuntimeError):
    """Fail-closed SOURCE bind / import error. Never swallowed."""


@dataclass(frozen=True, slots=True)
class CheckoutBind:
    checkout_root: Path
    deploy_root: Path
    gn_init: Path
    stripped_appdata_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class BoundMelodiaGn:
    bind: CheckoutBind
    package_file: Path
    gn_init_file: Path
    builder_ids: frozenset[str]
    builder_callables: Mapping[str, Callable[..., object]]


def argv_after_double_dash(argv: list[str]) -> list[str]:
    """Return arguments after Blender's ``--`` separator, else ``argv[1:]``."""
    if "--" in argv:
        return argv[argv.index("--") + 1 :]
    return argv[1:]


def checkout_root_from_this_file(tools_file: Path) -> Path:
    """Resolve the repo root from a file under ``Tools/``."""
    tools_dir = tools_file.resolve().parent
    if tools_dir.name != "Tools":
        raise SourceBindError(
            f"expected Tools/ script, got {tools_file} (parent={tools_dir.name})"
        )
    return tools_dir.parent


def known_blender_user_addon_roots() -> tuple[Path, ...]:
    """Return existing ``.../Blender/<ver>/scripts/addons`` dirs under APPDATA."""
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        return ()
    base = Path(appdata) / "Blender Foundation" / "Blender"
    if not base.is_dir():
        return ()
    roots: list[Path] = []
    try:
        versions = list(base.iterdir())
    except OSError as exc:
        raise SourceBindError(f"cannot list Blender user script versions: {exc}") from exc
    for version_dir in versions:
        addons = version_dir / "scripts" / "addons"
        if addons.is_dir():
            roots.append(addons.resolve())
    return tuple(roots)


def _resolve_existing(path: str) -> Path | None:
    try:
        resolved = Path(path).resolve()
    except OSError:
        return None
    return resolved


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
    except OSError as exc:
        raise SourceBindError(f"cannot resolve path relation {path} vs {root}: {exc}") from exc


def is_blender_user_addons_path(path: str, addon_roots: tuple[Path, ...]) -> bool:
    resolved = _resolve_existing(path)
    if resolved is None:
        return False
    for root in addon_roots:
        if resolved == root or is_under(resolved, root):
            return True
    parts = [part.lower() for part in resolved.parts]
    try:
        idx = parts.index("blender foundation")
    except ValueError:
        return False
    return (
        idx + 4 < len(parts)
        and parts[idx + 1] == "blender"
        and "scripts" in parts[idx + 2 :]
        and "addons" in parts[idx + 2 :]
    )


def shadowing_surreal_arch_paths(deploy_root: Path) -> tuple[Path, ...]:
    """sys.path entries other than deploy_root that contain surreal_arch.melodia_gn."""
    deploy = deploy_root.resolve()
    shadows: list[Path] = []
    for raw in sys.path:
        if not raw or raw == ".":
            continue
        resolved = _resolve_existing(raw)
        if resolved is None:
            continue
        if resolved == deploy:
            continue
        gn_init = resolved / "surreal_arch" / "melodia_gn" / "__init__.py"
        if gn_init.is_file():
            shadows.append(resolved)
    return tuple(shadows)


def purge_surreal_arch_modules() -> tuple[str, ...]:
    """Drop cached surreal_arch modules so the next import cannot reuse a shadow."""
    names = tuple(
        name
        for name in list(sys.modules)
        if name == "surreal_arch" or name.startswith("surreal_arch.")
    )
    for name in names:
        del sys.modules[name]
    return names


def strip_blender_user_addons_from_sys_path() -> tuple[Path, ...]:
    addon_roots = known_blender_user_addon_roots()
    stripped: list[Path] = []
    kept: list[str] = []
    for raw in sys.path:
        if raw and is_blender_user_addons_path(raw, addon_roots):
            resolved = _resolve_existing(raw)
            stripped.append(resolved if resolved is not None else Path(raw))
            continue
        kept.append(raw)
    sys.path[:] = kept
    return tuple(stripped)


def bind_checkout_deploy(checkout_root: Path) -> CheckoutBind:
    """Put checkout ``deploy/`` first on sys.path and remove AppData addons.

    Does not import ``surreal_arch``. Callers must import only after this bind
    and then assert ``__file__`` via :func:`import_checkout_melodia_gn`.
    """
    root = checkout_root.resolve()
    deploy = (root / "deploy").resolve()
    gn_init = deploy / "surreal_arch" / "melodia_gn" / "__init__.py"
    if not gn_init.is_file():
        raise SourceBindError(f"SOURCE bind failed: missing {gn_init}")

    stripped = strip_blender_user_addons_from_sys_path()
    purge_surreal_arch_modules()

    deploy_s = str(deploy)
    sys.path[:] = [entry for entry in sys.path if _resolve_existing(entry) != deploy]
    sys.path.insert(0, deploy_s)

    shadows = shadowing_surreal_arch_paths(deploy)
    if shadows:
        joined = ", ".join(str(path) for path in shadows)
        raise SourceBindError(
            "SOURCE bind failed closed: surreal_arch.melodia_gn would be shadowed by "
            f"{joined}"
        )
    return CheckoutBind(
        checkout_root=root,
        deploy_root=deploy,
        gn_init=gn_init,
        stripped_appdata_paths=stripped,
    )


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise SourceBindError(f"{label} is not a file: {path}")
    return path.resolve()


def measured_builder_ids(group_builders: object) -> dict[str, Callable[..., object]]:
    """Copy GROUP_BUILDERS into a typed dict. Fail closed on untyped garbage."""
    if not isinstance(group_builders, dict):
        raise SourceBindError(
            f"GROUP_BUILDERS must be a dict, got {type(group_builders).__name__}"
        )
    measured: dict[str, Callable[..., object]] = {}
    for key, value in group_builders.items():
        if not isinstance(key, str) or not key:
            raise SourceBindError(f"builder id is not a non-empty str: {key!r}")
        if not callable(value):
            raise SourceBindError(
                f"{key}: GROUP_BUILDERS value is not callable ({type(value).__name__})"
            )
        measured[key] = value
    return measured


def import_checkout_melodia_gn(bind: CheckoutBind) -> BoundMelodiaGn:
    """Import ``surreal_arch.melodia_gn`` and prove it came from the checkout."""
    shadows = shadowing_surreal_arch_paths(bind.deploy_root)
    if shadows:
        raise SourceBindError(
            "refusing import: AppData/other surreal_arch still shadows "
            f"{tuple(str(path) for path in shadows)}"
        )

    import surreal_arch  # noqa: PLC0415
    import surreal_arch.melodia_gn as gn  # noqa: PLC0415
    from surreal_arch.melodia_gn import core as gn_core  # noqa: PLC0415

    package_file = _require_file(
        Path(getattr(surreal_arch, "__file__", "") or ""),
        "surreal_arch.__file__",
    )
    gn_file = _require_file(
        Path(getattr(gn, "__file__", "") or ""),
        "surreal_arch.melodia_gn.__file__",
    )
    expected_package = (bind.deploy_root / "surreal_arch" / "__init__.py").resolve()
    expected_gn = bind.gn_init.resolve()
    if not package_file.samefile(expected_package):
        raise SourceBindError(
            "SOURCE import origin mismatch: surreal_arch came from "
            f"{package_file}, expected {expected_package}"
        )
    if not gn_file.samefile(expected_gn):
        raise SourceBindError(
            "SOURCE import origin mismatch: melodia_gn came from "
            f"{gn_file}, expected {expected_gn}"
        )
    builders = measured_builder_ids(gn_core.GROUP_BUILDERS)
    return BoundMelodiaGn(
        bind=bind,
        package_file=package_file,
        gn_init_file=gn_file,
        builder_ids=frozenset(builders),
        builder_callables=builders,
    )


def bind_live_addons() -> Path:
    """Bind the live Blender 5.2 AppData addons path. Inverse of SOURCE bind."""
    appdata = os.environ.get("APPDATA", "").strip()
    if not appdata:
        raise SourceBindError("LIVE bind failed: APPDATA is not set")
    addon_root = (
        Path(appdata)
        / "Blender Foundation"
        / "Blender"
        / BLENDER_VERSION
        / "scripts"
        / "addons"
    ).resolve()
    if not addon_root.is_dir():
        raise SourceBindError(f"LIVE bind failed: missing {addon_root}")
    live_gn = addon_root / "surreal_arch" / "melodia_gn" / "__init__.py"
    if not live_gn.is_file():
        raise SourceBindError(f"LIVE bind failed: missing {live_gn}")

    purge_surreal_arch_modules()
    addon_s = str(addon_root)
    sys.path[:] = [entry for entry in sys.path if _resolve_existing(entry) != addon_root]
    sys.path.insert(0, addon_s)
    return addon_root
