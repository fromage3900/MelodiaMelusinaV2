#!/usr/bin/env python3
"""Houdini Foundry contract tool -- recipe validation, tile planning, bake-manifest verification.

Contract: Docs/Houdini/FoundryDay_2026-09-24/README.md
Schemas:  specs/houdini_foundry/
Recipes:  recipes/houdini_foundry/

    python Tools/Houdini/foundry/houdini_foundry.py probe [--out PATH]
    python Tools/Houdini/foundry/houdini_foundry.py validate recipes/houdini_foundry/*.json
    python Tools/Houdini/foundry/houdini_foundry.py plan recipes/houdini_foundry/field_atlas_sea_above_test_tile.v1.json
    python Tools/Houdini/foundry/houdini_foundry.py verify Saved/HoudiniFoundry/<recipe_id>_<seed>/bake_manifest.json

This file never cooks, never imports ``hou`` and never imports ``unreal``. It is the
offline gate around the existing Hython families under Tools/Houdini/: a recipe says what
to bake and where it goes; the owning Hython script bakes it; ``verify`` re-derives hashes.
Seeds reuse ``resonant_world_generator.stable_int`` and hashes reuse
``universe_foundry.content_hash`` -- no second seeding or hashing scheme.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SPEC_DIR = ROOT / "specs" / "houdini_foundry"
CHANNELS_PATH = SPEC_DIR / "field_atlas_channels.v1.json"
OUTPUT_ROOT = "Saved/HoudiniFoundry"
EVIDENCE_ROOT = "Saved/Audit/houdini_foundry"

RECIPE_SCHEMA = "melodia.houdini_foundry_recipe.v1"
REQUEST_SCHEMA = "melodia.houdini_foundry_bake_request.v1"
MANIFEST_SCHEMA = "melodia.houdini_foundry_bake_manifest.v1"

PRODUCTS = (
    "hda_engine_smoke", "crystal_cathedral", "field_atlas", "deposition", "flow_volume",
    "volumetric_ecology", "ocean_intelligence", "copernicus_field", "vellum_textile",
)
SOURCE_KINDS = ("hython_script", "hda", "pure_python")
UE_CONSUMERS = (
    "static_mesh", "texture", "world_compiler_points", "pcg_graph", "niagara_system",
    "material_instance", "offline_only",
)
MANIFEST_STATUS = ("PASS", "FAIL", "HOLD")
SEED_MOD = 2**31  # Houdini/VEX seeds are int32-safe
DEFAULT_WINDOWS_HYTHON = r"C:\Program Files\Side Effects Software\Houdini 22.0.368\bin\hython.exe"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)  # dataclasses resolve their module via sys.modules
    spec.loader.exec_module(module)
    return module


rwg = _load_module("resonant_world_generator", ROOT / "Content" / "Python" / "resonant_world_generator.py")
uf = _load_module("universe_foundry", ROOT / "Tools" / "universe_foundry.py")


# ----------------------------------------------------------------------------- helpers

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def derive_seed(seed: int, *parts: object) -> int:
    return rwg.stable_int(seed, "houdini_foundry", *parts) % SEED_MOD


def _is_repo_relative(value: str) -> bool:
    return bool(value) and not value.startswith(("/", "\\")) and ":" not in value.split("/")[0] and ".." not in value.split("/")


def _walk_strings(obj: Any, prefix: str = ""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _walk_strings(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk_strings(value, f"{prefix}[{index}]")
    elif isinstance(obj, str):
        yield prefix, obj


def output_dir(recipe: dict[str, Any]) -> str:
    return f"{OUTPUT_ROOT}/{recipe['recipe_id']}_{recipe['seed']}"


def evidence_dir(recipe: dict[str, Any]) -> str:
    return f"{EVIDENCE_ROOT}/{recipe['recipe_id']}"


# ----------------------------------------------------------------------------- validation

def validate_recipe(recipe: dict[str, Any], *, check_files: bool = True) -> list[str]:
    errors: list[str] = []
    if recipe.get("schema") != RECIPE_SCHEMA:
        return [f"schema must be {RECIPE_SCHEMA}"]
    for key in ("recipe_id", "product", "seed", "status", "source", "params", "outputs", "ue_target", "authority"):
        if key not in recipe:
            errors.append(f"missing {key}")
    if errors:
        return errors
    rid = recipe["recipe_id"]
    if not isinstance(rid, str) or not rid.replace("_", "").isalnum() or rid.lower() != rid:
        errors.append("recipe_id must be lower_snake_case")
    if recipe["product"] not in PRODUCTS:
        errors.append(f"product must be one of {PRODUCTS}")
    if not isinstance(recipe["seed"], int) or isinstance(recipe["seed"], bool) or not 0 <= recipe["seed"] < SEED_MOD:
        errors.append("seed must be an int in [0, 2^31)")
    if recipe["status"] not in ("staged", "source_proven", "live_proven"):
        errors.append("status must be staged | source_proven | live_proven")

    source = recipe["source"]
    if source.get("kind") not in SOURCE_KINDS:
        errors.append(f"source.kind must be one of {SOURCE_KINDS}")
    src_path = source.get("path", "")
    if not _is_repo_relative(src_path):
        errors.append("source.path must be repo-relative")
    elif check_files and source.get("exists_on_main", True) and not (ROOT / src_path).exists():
        errors.append(f"source.path does not exist: {src_path} (set exists_on_main=false if it is authored at college)")

    outputs = recipe["outputs"]
    if not isinstance(outputs, list) or not outputs:
        errors.append("outputs must be a non-empty list")
    else:
        names = [o.get("name") for o in outputs]
        if len(set(names)) != len(names):
            errors.append("outputs[].name must be unique")
        for o in outputs:
            if not o.get("name") or not o.get("format"):
                errors.append("every output needs name + format")

    ue = recipe["ue_target"]
    if ue.get("consumer") not in UE_CONSUMERS:
        errors.append(f"ue_target.consumer must be one of {UE_CONSUMERS}")
    prefix = ue.get("asset_path_prefix")
    if prefix is not None and not str(prefix).startswith("/Game/"):
        errors.append("ue_target.asset_path_prefix must start with /Game/")
    if not ue.get("integration_gate"):
        errors.append("ue_target.integration_gate is required (which FoundryDay gate proves the consumer)")

    auth = recipe["authority"]
    if auth.get("runtime_owner") in (None, "", "houdini", "houdini_foundry"):
        errors.append("authority.runtime_owner must name the existing UE owner, never Houdini/Foundry")
    if auth.get("writes_mpc") is not False:
        errors.append("authority.writes_mpc must be false (existing MPC writers stay sole writers)")

    for where, text in _walk_strings(recipe):
        if (len(text) > 2 and text[1] == ":" and text[2] in "\\/") or text.startswith(("C:\\", "/home/", "/Users/")):
            errors.append(f"{where}: workstation path not allowed in a recipe")

    if "region" in recipe:
        errors.extend(_validate_region(recipe["region"]))
    if recipe["product"] in ("field_atlas", "flow_volume", "volumetric_ecology", "ocean_intelligence", "copernicus_field"):
        errors.extend(_validate_channels(recipe))
    return errors


def _validate_region(region: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    bounds = region.get("bounds_cm")
    if not (isinstance(bounds, list) and len(bounds) == 4 and all(isinstance(v, (int, float)) for v in bounds)):
        return ["region.bounds_cm must be [xmin, ymin, xmax, ymax]"]
    if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
        errors.append("region.bounds_cm min must be < max")
    tile = region.get("tile_size_cm")
    gutter = region.get("gutter_cm", 0)
    if not isinstance(tile, (int, float)) or tile <= 0:
        errors.append("region.tile_size_cm must be > 0")
    elif not isinstance(gutter, (int, float)) or gutter < 0 or gutter * 2 >= tile:
        errors.append("region.gutter_cm must be >= 0 and < tile_size_cm / 2")
    if not region.get("level", "").startswith("/Game/"):
        errors.append("region.level must be a /Game/ level path")
    return errors


def _validate_channels(recipe: dict[str, Any]) -> list[str]:
    vocab = {c["name"] for c in load_json(CHANNELS_PATH)["channels"]}
    channels = recipe["params"].get("channels", [])
    if not channels:
        return ["params.channels must list at least one field channel"]
    unknown = sorted(set(channels) - vocab)
    return [f"params.channels not in {CHANNELS_PATH.name}: {unknown}"] if unknown else []


def validate_request(request: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if request.get("schema") != REQUEST_SCHEMA:
        return [f"schema must be {REQUEST_SCHEMA}"]
    if not request.get("request_id"):
        errors.append("missing request_id")
    recipes = request.get("recipes")
    if not isinstance(recipes, list) or not recipes:
        return errors + ["recipes must be a non-empty list of repo-relative recipe paths"]
    for rel in recipes:
        if not _is_repo_relative(rel) or not (ROOT / rel).exists():
            errors.append(f"recipe not found: {rel}")
            continue
        errors.extend(f"{rel}: {e}" for e in validate_recipe(load_json(ROOT / rel)))
    mission = request.get("mission_ref")
    if mission is not None and not (mission.get("mission_id") and mission.get("task_id")):
        errors.append("mission_ref needs mission_id + task_id (Universe Foundry mission task)")
    return errors


# ----------------------------------------------------------------------------- planning

def plan_tiles(recipe: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic tile grid: ids from integer grid coords, seeds from stable_int."""
    region = recipe["region"]
    xmin, ymin, xmax, ymax = region["bounds_cm"]
    tile = float(region["tile_size_cm"])
    gutter = float(region.get("gutter_cm", 0))
    ix0, iy0 = math.floor(xmin / tile), math.floor(ymin / tile)
    ix1, iy1 = math.ceil(xmax / tile), math.ceil(ymax / tile)
    only = set(region.get("only_tiles", []))
    tiles = []
    for iy in range(iy0, iy1):
        for ix in range(ix0, ix1):
            tile_id = f"tx{ix:+04d}_ty{iy:+04d}"
            if only and tile_id not in only:
                continue
            core = [ix * tile, iy * tile, (ix + 1) * tile, (iy + 1) * tile]
            tiles.append({
                "tile_id": tile_id,
                "ix": ix,
                "iy": iy,
                "seed": derive_seed(recipe["seed"], recipe["recipe_id"], "tile", ix, iy),
                "core_bounds_cm": core,
                "bake_bounds_cm": [core[0] - gutter, core[1] - gutter, core[2] + gutter, core[3] + gutter],
                "output_dir": f"{output_dir(recipe)}/tiles/{tile_id}",
            })
    return tiles


def build_plan(recipe: dict[str, Any]) -> dict[str, Any]:
    plan = {
        "schema": "melodia.houdini_foundry_plan.v1",
        "recipe_id": recipe["recipe_id"],
        "recipe_sha256": uf.content_hash(recipe),
        "product": recipe["product"],
        "seed": recipe["seed"],
        "source": recipe["source"],
        "output_dir": output_dir(recipe),
        "evidence_dir": evidence_dir(recipe),
        "manifest_path": f"{output_dir(recipe)}/bake_manifest.json",
        "ue_target": recipe["ue_target"],
    }
    if "region" in recipe:
        plan["tiles"] = plan_tiles(recipe)
    return plan


# ----------------------------------------------------------------------------- manifest verification

def verify_manifest(manifest_path: Path) -> list[str]:
    manifest = load_json(manifest_path)
    errors: list[str] = []
    if manifest.get("schema") != MANIFEST_SCHEMA:
        return [f"schema must be {MANIFEST_SCHEMA}"]
    for key in ("recipe_id", "recipe_sha256", "seed", "houdini_version", "tool", "outputs", "status"):
        if key not in manifest:
            errors.append(f"missing {key}")
    if errors:
        return errors
    if manifest["status"] not in MANIFEST_STATUS:
        errors.append(f"status must be one of {MANIFEST_STATUS}")
    if manifest["status"] == "PASS" and not manifest["outputs"]:
        errors.append("PASS manifest must list outputs")
    for output in manifest["outputs"]:
        rel = output.get("path", "")
        path = ROOT / rel
        if not _is_repo_relative(rel):
            errors.append(f"output path must be repo-relative: {rel}")
        elif not path.exists():
            errors.append(f"output missing on disk: {rel}")
        elif sha256_file(path) != output.get("sha256"):
            errors.append(f"sha256 mismatch: {rel}")
        elif path.stat().st_size != output.get("bytes"):
            errors.append(f"byte count mismatch: {rel}")
    return errors


# ----------------------------------------------------------------------------- hython probe

def resolve_hython() -> str | None:
    env = os.environ.get("HOUDINI_HYTHON_EXE")
    if env and Path(env).exists():
        return env
    hfs = os.environ.get("HFS")
    if hfs:
        for name in ("hython.exe", "hython"):
            candidate = Path(hfs) / "bin" / name
            if candidate.exists():
                return str(candidate)
    on_path = shutil.which("hython")
    if on_path:
        return on_path
    return DEFAULT_WINDOWS_HYTHON if Path(DEFAULT_WINDOWS_HYTHON).exists() else None


def probe(timeout_s: int = 60) -> dict[str, Any]:
    """Lane law 1: never run hython bare -- hard timeout, kill on hang."""
    result: dict[str, Any] = {"schema": "melodia.houdini_foundry_probe.v1", "hython": resolve_hython()}
    if not result["hython"]:
        result.update(status="HOLD", reason="hython not found (set HOUDINI_HYTHON_EXE or HFS)")
        return result
    code = ("import hou,json;print(json.dumps({'version':hou.applicationVersionString(),"
            "'license':str(hou.licenseCategory()),'python':__import__('sys').version.split()[0]}))")
    try:
        proc = subprocess.run([result["hython"], "-c", code], capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        result.update(status="HOLD", reason=f"hython hung > {timeout_s}s (license server?) -- killed")
        return result
    line = next((ln for ln in reversed(proc.stdout.splitlines()) if ln.startswith("{")), "")
    if proc.returncode != 0 or not line:
        result.update(status="HOLD", reason="hython failed", stderr=proc.stderr[-2000:])
        return result
    result.update(json.loads(line))
    hserver = Path(result["hython"]).with_name("hserver.exe" if result["hython"].endswith(".exe") else "hserver")
    if hserver.exists():
        try:
            hs = subprocess.run([str(hserver), "-l"], capture_output=True, text=True, timeout=30)
            result["hserver_l"] = hs.stdout[-2000:]
        except subprocess.TimeoutExpired:
            result["hserver_l"] = "timeout"
    result["status"] = "PASS"
    return result


# ----------------------------------------------------------------------------- CLI

def _print_errors(label: str, errors: list[str]) -> int:
    if errors:
        print(f"FAIL {label}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"PASS {label}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    rc = 0
    for path in args.paths:
        data = load_json(Path(path))
        errors = validate_request(data) if data.get("schema") == REQUEST_SCHEMA else validate_recipe(data)
        rc |= _print_errors(str(path), errors)
    return rc


def cmd_plan(args: argparse.Namespace) -> int:
    recipe = load_json(Path(args.recipe))
    errors = validate_recipe(recipe)
    if errors:
        return _print_errors(args.recipe, errors)
    text = json.dumps(build_plan(recipe), indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    return _print_errors(args.manifest, verify_manifest(Path(args.manifest)))


def cmd_probe(args: argparse.Namespace) -> int:
    result = probe(args.timeout)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["status"] == "PASS" else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate", help="validate recipes / bake requests")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=cmd_validate)
    p = sub.add_parser("plan", help="deterministic output/tile plan for one recipe")
    p.add_argument("recipe")
    p.add_argument("--out")
    p.set_defaults(func=cmd_plan)
    p = sub.add_parser("verify", help="re-derive hashes of a bake manifest")
    p.add_argument("manifest")
    p.set_defaults(func=cmd_verify)
    p = sub.add_parser("probe", help="hython/license probe with a hard timeout")
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--out")
    p.set_defaults(func=cmd_probe)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
