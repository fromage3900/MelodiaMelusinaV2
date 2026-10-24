#!/usr/bin/env python3
"""Recipe-driven parameters for the Poitou house terrain HDA.

Convergence seam (World Compiler option 1): bind a ``world_recipe.v1``
``terrain.kind == "house_hda"`` block to the house terrain HDA's seed/param
surface so the World Compiler -- not a parallel tool -- decides the authored
identity. Same recipe + same compiler version => byte-identical param manifest
and sha (the convergence invariant in Docs/Houdini/MELODIA_HOUDINI_STUDIO_CONVERGENCE_2026-10-07.md).

The HDA itself (``Tools/Houdini/build_house_terrain_hda.py``) keeps its own
defaults; this module only maps the params a recipe chooses to drive. The Houdini
lane applies the manifest to the live HDA (Hython / editor cook) -- that cook is
the owner step, never this offline module. Offline-safe: pure stdlib, no ``hou``,
no ``unreal`` (contract section 8).

Wire: ``stage_terrain`` in ``Tools/world_compiler.py`` (``kind == "house_hda"``)
returns this manifest as the stage info, so it auto-lands as ``terrain.json`` in
the bundle. Contract: Docs/WorldGen/WORLD_COMPILER_CONTRACT.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "Tools"), str(ROOT / "Content" / "Python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import resonant_world_generator as rwg  # noqa: E402  (shared identity source, reused)

MANIFEST_SCHEMA = "melodia.house_terrain_params.v1"
DEFAULT_HDA = "Tools/Houdini/build_house_terrain_hda.py"
COMPILER_VERSION = "world_compiler_v1.0"

# The five named seed params the HDA reads (see build_house_terrain_hda.py
# addParmTemplate calls). A recipe derives each from world_seed unless it names it
# explicitly; the rest of the HDA keeps its own authored defaults.
SEED_PARAMS = ("ridge_seed", "path_seed", "cave_seed", "pass_seed", "myc_seed")
SEED_RANGE = 100_000  # HDA seed parms are IntParmTemplate min=0 max=99999


def _num(value: Any) -> Any:
    """Coerce an override value to int/float, preserving integral-ness."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    text = str(value).strip()
    try:
        return int(text)
    except ValueError:
        return float(text)


def derive_seed(world_seed: int, name: str) -> int:
    """Deterministic 0..99999 seed for one HDA seed parm from the world seed.

    Uses the SAME sub-seeding source as the rest of the compiler
    (``resonant_world_generator.stable_int``) so the whole bundle shares one
    identity function -- the convergence invariant, not five ad-hoc hashes.
    """
    return rwg.stable_int(int(world_seed), "house_hda", name) % SEED_RANGE


def resolve(recipe: dict[str, Any]) -> dict[str, Any]:
    """Resolve a recipe's ``terrain`` block into a deterministic HDA param manifest."""
    terrain = recipe.get("terrain") or {}
    if terrain.get("kind") != "house_hda":
        raise ValueError("terrain.kind must be 'house_hda'")

    world_seed = int(recipe["world_seed"])
    explicit = {str(k): int(v) for k, v in (terrain.get("seeds") or {}).items()}
    unknown = set(explicit) - set(SEED_PARAMS)
    if unknown:
        raise ValueError(f"unknown seed params: {sorted(unknown)} (allowed: {list(SEED_PARAMS)})")

    seeds: dict[str, int] = {}
    provenance: dict[str, str] = {}
    for name in SEED_PARAMS:
        if name in explicit:
            seeds[name] = explicit[name]
            provenance[name] = "explicit"
        else:
            seeds[name] = derive_seed(world_seed, name)
            provenance[name] = "derived"

    overrides = {str(k): _num(v) for k, v in (terrain.get("overrides") or {}).items()}
    params = {**seeds, **overrides}

    manifest: dict[str, Any] = {
        "schema": MANIFEST_SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "recipe_id": recipe["recipe_id"],
        "world_seed": world_seed,
        "hda": terrain.get("hda") or DEFAULT_HDA,
        "level": (recipe.get("place") or {}).get("level", ""),
        "seeds": seeds,
        "seed_provenance": provenance,
        "overrides": overrides,
        "params": params,
    }
    manifest["manifest_sha256"] = sha_of(manifest)
    return manifest


def sha_of(manifest: dict[str, Any]) -> str:
    """Canonical sha of everything except the sha field itself (order-independent)."""
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _load_recipe(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _coerce_seed(recipe: dict[str, Any], seed: int) -> dict[str, Any]:
    """Return a shallow copy of the recipe with world_seed swapped (for diff-seed)."""
    out = dict(recipe)
    out["terrain"] = dict(recipe.get("terrain") or {})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_res = sub.add_parser("resolve", help="print the HDA param manifest for a recipe")
    p_res.add_argument("recipe")
    p_res.add_argument("--write", help="also write terrain.json into this dir")
    p_ver = sub.add_parser("verify", help="prove the manifest is deterministic (byte-identical re-derive)")
    p_ver.add_argument("recipe")
    p_diff = sub.add_parser("diff-seed", help="show which HDA params change between two world seeds")
    p_diff.add_argument("recipe")
    p_diff.add_argument("seed_a", type=int)
    p_diff.add_argument("seed_b", type=int)
    args = ap.parse_args(argv)

    recipe = _load_recipe(Path(args.recipe).resolve() if "recipe" in args else Path("."))

    if args.cmd == "resolve":
        manifest = resolve(recipe)
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        if args.write:
            out = Path(args.write)
            out.mkdir(parents=True, exist_ok=True)
            (out / "terrain.json").write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            print(f"wrote {(out / 'terrain.json').resolve()}", file=sys.stderr)
        return 0

    if args.cmd == "verify":
        a = resolve(recipe)
        b = resolve(_load_recipe(Path(args.recipe).resolve()))
        # round-trip through JSON to prove no hidden non-determinism
        c = resolve(json.loads(json.dumps(recipe)))
        ok = a["manifest_sha256"] == b["manifest_sha256"] == c["manifest_sha256"]
        print(f"manifest_sha256 {a['manifest_sha256']}  deterministic={ok}")
        return 0 if ok else 1

    if args.cmd == "diff-seed":
        ra = dict(recipe); ra["world_seed"] = args.seed_a
        rb = dict(recipe); rb["world_seed"] = args.seed_b
        ma = resolve(ra)["params"]
        mb = resolve(rb)["params"]
        changed = [k for k in ma if ma[k] != mb.get(k)]
        print(f"seed {args.seed_a} -> {args.seed_b}: {len(changed)} param(s) change")
        for k in sorted(ma):
            flag = "  <-- changed" if ma[k] != mb.get(k) else ""
            print(f"  {k:16} {ma[k]!s:>10} -> {mb.get(k)!s:>10}{flag}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
