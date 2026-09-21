#!/usr/bin/env python3
"""Melodia Studio SOURCE gate — checkout ``deploy/`` is the only import origin.

Run under Blender 5.2 (bpy is required for builder construction):

  blender.exe --background --factory-startup --python Tools/melodia_studio_source_gate.py -- ^
      --require-id GN_PARIS_WallDetail --require-id GN_PARIS_SlabTrim

PYTHONPATH is ignored as evidence. AppData addons are stripped from sys.path.
Registration is proven by the imported GROUP_BUILDERS mapping, not by grepping
source. Construction of --require-id builders is fail-closed (None is FAIL).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from melodia_studio_pathbind import (
    BoundMelodiaGn,
    CheckoutBind,
    SourceBindError,
    argv_after_double_dash,
    bind_checkout_deploy,
    checkout_root_from_this_file,
    import_checkout_melodia_gn,
)

BANNER_PASS: Final[str] = "MELODIA STUDIO SOURCE GATE: PASS"
BANNER_FAIL: Final[str] = "MELODIA STUDIO SOURCE GATE: FAIL"
SOURCE_JSON_REL: Final[str] = "Saved/Audit/melodia_studio_source_registry.json"
LAPTOP_HARDCODE: Final[str] = "P:/MelodiaMelusinaV2-Laptop"


class SourceGateError(RuntimeError):
    """Fail-closed SOURCE assertion. Never swallowed into a PASS."""


@dataclass(slots=True)
class ConstructionRecord:
    builder_id: str
    tree_name: str
    empty: bool
    verts: int


@dataclass(slots=True)
class SourceGateReport:
    ok: bool
    checkout_root: str
    deploy_root: str
    package_file: str
    gn_init_file: str
    stripped_appdata: tuple[str, ...]
    builder_count: int
    builder_ids: list[str]
    required_ids: list[str]
    expected_new_ids: list[str]
    baseline_new: list[str]
    baseline_lost: list[str]
    constructions: list[ConstructionRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": "melodia.studio.source_gate.v1",
            "ok": self.ok,
            "checkout_root": self.checkout_root,
            "deploy_root": self.deploy_root,
            "package_file": self.package_file,
            "gn_init_file": self.gn_init_file,
            "stripped_appdata": list(self.stripped_appdata),
            "builder_count": self.builder_count,
            "builder_ids": self.builder_ids,
            "required_ids": self.required_ids,
            "expected_new_ids": self.expected_new_ids,
            "baseline_new": self.baseline_new,
            "baseline_lost": self.baseline_lost,
            "constructions": [
                {
                    "builder_id": item.builder_id,
                    "tree_name": item.tree_name,
                    "empty": item.empty,
                    "verts": item.verts,
                }
                for item in self.constructions
            ],
            "errors": self.errors,
            "warnings": self.warnings,
        }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Melodia Studio SOURCE gate")
    parser.add_argument(
        "--checkout-root",
        default="",
        help="Repo root. Default: parent of Tools/ containing this script.",
    )
    parser.add_argument(
        "--require-id",
        action="append",
        default=[],
        dest="require_ids",
        help="Builder id that must be present in the imported registry. Repeatable.",
    )
    parser.add_argument(
        "--expect-new",
        action="append",
        default=[],
        dest="expect_new",
        help="Builder id that must be new vs Tools/registry_baseline.json. Repeatable.",
    )
    parser.add_argument(
        "--strict-baseline",
        action="store_true",
        help="FAIL on any baseline lost/new besides --expect-new. Off: report drift only.",
    )
    parser.add_argument(
        "--json-out",
        default="",
        help="Write the SOURCE registry JSON here. Default: Saved/Audit/...",
    )
    return parser.parse_args(list(argv))


def unwrap_node_tree(result: object, builder_id: str) -> object:
    """Unwrap a builder return into a bpy NodeTree. None is FAIL."""
    if result is None:
        raise SourceGateError(f"{builder_id}: builder returned None")
    tree: object
    if isinstance(result, (tuple, list)):
        if len(result) == 0:
            raise SourceGateError(f"{builder_id}: builder returned an empty sequence")
        tree = result[0]
    else:
        tree = result
    if tree is None:
        raise SourceGateError(f"{builder_id}: builder returned a None tree")
    return tree


def assert_node_tree(tree: object, builder_id: str) -> str:
    import bpy  # noqa: PLC0415

    if not isinstance(tree, bpy.types.NodeTree):
        raise SourceGateError(
            f"{builder_id}: expected bpy.types.NodeTree, got {type(tree).__name__}"
        )
    name = str(tree.name)
    if not name:
        raise SourceGateError(f"{builder_id}: NodeTree has an empty name")
    return name


def measure_evaluated_verts(tree: object, builder_id: str) -> int:
    import bpy  # noqa: PLC0415

    scene = bpy.context.scene
    if scene is None:
        raise SourceGateError(f"{builder_id}: bpy.context.scene is None")
    mesh = bpy.data.meshes.new(f"__src_gate_{builder_id}__")
    obj = bpy.data.objects.new(f"__src_gate_{builder_id}__", mesh)
    scene.collection.objects.link(obj)
    try:
        modifier = obj.modifiers.new("source_gate", "NODES")
        modifier.node_group = tree
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = obj.evaluated_get(depsgraph)
        evaluated_mesh = evaluated.to_mesh()
        verts = len(evaluated_mesh.vertices) if evaluated_mesh is not None else 0
        evaluated.to_mesh_clear()
        return verts
    finally:
        obj.modifiers.clear()
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)


def construct_required(
    loaded: BoundMelodiaGn,
    required_ids: Sequence[str],
) -> list[ConstructionRecord]:
    records: list[ConstructionRecord] = []
    for builder_id in required_ids:
        fn = loaded.builder_callables.get(builder_id)
        if fn is None:
            raise SourceGateError(
                f"{builder_id}: required id is absent from imported GROUP_BUILDERS"
            )
        result = fn()
        tree = unwrap_node_tree(result, builder_id)
        tree_name = assert_node_tree(tree, builder_id)
        verts = measure_evaluated_verts(tree, builder_id)
        records.append(
            ConstructionRecord(
                builder_id=builder_id,
                tree_name=tree_name,
                empty=verts == 0,
                verts=verts,
            )
        )
    return records


def ast_constant_register_ids(py_path: Path) -> tuple[frozenset[str], bool]:
    """Return constant register_builder ids in a module, plus a dynamic-id flag."""
    source = py_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(py_path))
    ids: set[str] = set()
    dynamic = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_register = (isinstance(func, ast.Name) and func.id == "register_builder") or (
            isinstance(func, ast.Attribute) and func.attr == "register_builder"
        )
        if not is_register:
            continue
        if not node.args:
            raise SourceGateError(f"{py_path}: register_builder() call has no arguments")
        arg0 = node.args[0]
        if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str) and arg0.value:
            ids.add(arg0.value)
        else:
            dynamic = True
    return frozenset(ids), dynamic


def assert_required_declared_in_checkout(
    bind: CheckoutBind,
    required_ids: Sequence[str],
) -> None:
    """Required ids must be constant register_builder args in checkout sources."""
    gn_dir = bind.deploy_root / "surreal_arch" / "melodia_gn"
    declared: dict[str, Path] = {}
    for py_path in sorted(gn_dir.glob("*.py")):
        ids, _dynamic = ast_constant_register_ids(py_path)
        for builder_id in ids:
            declared[builder_id] = py_path
    missing = [builder_id for builder_id in required_ids if builder_id not in declared]
    if missing:
        raise SourceGateError(
            "required ids have no constant register_builder() in checkout sources: "
            + ", ".join(missing)
        )


def assert_no_laptop_hardcode(bind: CheckoutBind, required_ids: Sequence[str]) -> None:
    """Fail if the claimed modules still teach the laptop P: path as current."""
    gn_dir = bind.deploy_root / "surreal_arch" / "melodia_gn"
    checked = {gn_dir / "__init__.py", gn_dir / "core.py"}
    for py_path in sorted(gn_dir.glob("*.py")):
        ids, _dynamic = ast_constant_register_ids(py_path)
        if any(builder_id in ids for builder_id in required_ids):
            checked.add(py_path)
    for py_path in sorted(checked):
        if not py_path.is_file():
            continue
        text = py_path.read_text(encoding="utf-8-sig")
        if LAPTOP_HARDCODE in text:
            raise SourceGateError(
                f"{py_path.relative_to(bind.checkout_root)} still hardcodes {LAPTOP_HARDCODE}"
            )


def load_baseline_package_ids(checkout_root: Path) -> frozenset[str] | None:
    baseline = checkout_root / "Tools" / "registry_baseline.json"
    if not baseline.is_file():
        return None
    payload = json.loads(baseline.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise SourceGateError("registry_baseline.json is not an object")
    package = payload.get("package")
    if not isinstance(package, dict):
        raise SourceGateError("registry_baseline.json package is not an object")
    ids: list[str] = []
    for key in package:
        if not isinstance(key, str) or not key:
            raise SourceGateError(f"baseline package key is not a str: {key!r}")
        ids.append(key)
    return frozenset(ids)


def write_report(path: Path, report: SourceGateReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8")


def run(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    errors: list[str] = []
    warnings: list[str] = []
    try:
        import bpy  # noqa: PLC0415, F401
    except ImportError as exc:
        print(BANNER_FAIL)
        print("SOURCE gate requires Blender bpy; do not run this as host CPython.")
        print(exc)
        return 2

    checkout = (
        Path(args.checkout_root).expanduser().resolve()
        if args.checkout_root
        else checkout_root_from_this_file(Path(__file__))
    )
    required_ids = tuple(dict.fromkeys(args.require_ids))
    expected_new = tuple(dict.fromkeys(args.expect_new))

    try:
        bind = bind_checkout_deploy(checkout)
        assert_no_laptop_hardcode(bind, required_ids)
        if required_ids:
            assert_required_declared_in_checkout(bind, required_ids)
        loaded = import_checkout_melodia_gn(bind)
    except (SourceBindError, SourceGateError) as exc:
        print(BANNER_FAIL)
        print(str(exc))
        return 1

    missing_required = [builder_id for builder_id in required_ids if builder_id not in loaded.builder_ids]
    if missing_required:
        errors.append(
            "required ids absent from imported GROUP_BUILDERS: " + ", ".join(missing_required)
        )

    baseline_ids = load_baseline_package_ids(checkout)
    baseline_new: list[str] = []
    baseline_lost: list[str] = []
    if baseline_ids is None:
        warnings.append("Tools/registry_baseline.json missing; skipped delta")
    else:
        baseline_new = sorted(loaded.builder_ids - baseline_ids)
        baseline_lost = sorted(baseline_ids - loaded.builder_ids)
        missing_expected = [
            builder_id for builder_id in expected_new if builder_id not in loaded.builder_ids
        ]
        not_actually_new = [
            builder_id for builder_id in expected_new if builder_id not in set(baseline_new)
        ]
        unexpected_new = [
            builder_id for builder_id in baseline_new if builder_id not in expected_new
        ]
        if missing_expected:
            errors.append("expected-new ids not registered: " + ", ".join(missing_expected))
        if expected_new and not_actually_new:
            errors.append(
                "expected-new ids are registered but not new vs baseline: "
                + ", ".join(not_actually_new)
            )
        if args.strict_baseline:
            if unexpected_new:
                errors.append("unexpected new ids vs baseline: " + ", ".join(unexpected_new))
            if baseline_lost:
                errors.append("lost ids vs baseline: " + ", ".join(baseline_lost))
        else:
            if unexpected_new:
                warnings.append(
                    "baseline already drifted (extra new, not --strict-baseline): "
                    + ", ".join(unexpected_new)
                )
            if baseline_lost:
                warnings.append(
                    "baseline already drifted (lost, not --strict-baseline): "
                    + ", ".join(baseline_lost)
                )

    constructions: list[ConstructionRecord] = []
    if not missing_required:
        try:
            constructions = construct_required(loaded, required_ids)
        except SourceGateError as exc:
            errors.append(str(exc))

    ok = not errors
    report = SourceGateReport(
        ok=ok,
        checkout_root=str(bind.checkout_root),
        deploy_root=str(bind.deploy_root),
        package_file=str(loaded.package_file),
        gn_init_file=str(loaded.gn_init_file),
        stripped_appdata=tuple(str(path) for path in bind.stripped_appdata_paths),
        builder_count=len(loaded.builder_ids),
        builder_ids=sorted(loaded.builder_ids),
        required_ids=list(required_ids),
        expected_new_ids=list(expected_new),
        baseline_new=baseline_new,
        baseline_lost=baseline_lost,
        constructions=constructions,
        errors=errors,
        warnings=warnings,
    )
    json_out = Path(args.json_out).resolve() if args.json_out else checkout / SOURCE_JSON_REL
    write_report(json_out, report)

    print("SOURCE checkout:", report.checkout_root)
    print("SOURCE deploy:", report.deploy_root)
    print("SOURCE package file:", report.package_file)
    print("SOURCE gn file:", report.gn_init_file)
    print("SOURCE stripped AppData:", len(report.stripped_appdata))
    print("SOURCE registry count:", report.builder_count)
    print("SOURCE required:", report.required_ids)
    print("SOURCE baseline new:", report.baseline_new)
    print("SOURCE baseline lost:", report.baseline_lost)
    for item in constructions:
        print(
            f"SOURCE constructed {item.builder_id} tree={item.tree_name} "
            f"verts={item.verts} empty={item.empty}"
        )
    for warning in warnings:
        print("SOURCE warning:", warning)
    for error in errors:
        print("SOURCE error:", error)
    print("SOURCE json:", json_out)
    print(BANNER_PASS if ok else BANNER_FAIL)
    return 0 if ok else 1


def main() -> int:
    tools_dir = str(Path(__file__).resolve().parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    return run(argv_after_double_dash(sys.argv))


if __name__ == "__main__":
    raise SystemExit(main())
