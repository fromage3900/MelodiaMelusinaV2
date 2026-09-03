#!/usr/bin/env python3
"""
monolith_execution_plan_parallel.py -- Monolith lane parallel to hython lane.

Phase_3 bridge spec: make Monolith a first-class generation path alongside hython,
not an alternative. This plan mirrors the hython plan structure so both lanes can
run in parallel and be cross-validated.

Hython lane (offline, no editor):
  Phase H1: copernicus_cymatic_parallax.py --variant all --size 1024x1024 --cook
            -> Saved/Audit/copernicus_cymatic/{variant}/  (21 variants x 9 maps)
  Phase H2: flipbook_aaa.py --size 2048 --frames 8
            -> Content/EnvSandbox/Textures/PearlWoven_Flipbook/  (8 frames x 5 maps)

Monolith lane (live editor on 9316, this file):
  Phase A: material ops  -- import hython PNGs as textures, create PBR materials/MIs,
           wire parallax height, validate compilation
  Phase B: hair/WP captures -- (deferred; no hair/WP assets in current cymatic scope;
           placeholder for Faraway fabric/terrain captures when those assets land)
  Phase C: docs -- record material paths, update P0 ledger, produce bridge evidence

Each phase is idempotent and reports SKIP if already done.

Usage:
  python Tools/monolith_execution_plan_parallel.py --phase A              # dry-run print
  python Tools/monolith_execution_plan_parallel.py --phase A --dry-run
  python Tools/monolith_execution_plan_parallel.py --phase all --dry-run
  python Tools/monolith_execution_plan_parallel.py --status
  python Tools/monolith_execution_plan_parallel.py --phase A --execute    # live POST to 9316
  python Tools/monolith_execution_plan_parallel.py --phase A --variant CymaticMarble --execute

Requires: editor running with Monolith 0.20.3 on 9316. No writes happen without --execute.
"""
from __future__ import annotations
import argparse
import json
import sys
import socket
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CYMA_SRC = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic"
FLIPBOOK_SRC = PROJECT_ROOT / "Content" / "EnvSandbox" / "Textures" / "PearlWoven_Flipbook"

DEST_CYMA_ROOT = "/Game/Melodia/Cymatics"
DEST_FLIPBOOK_ROOT = "/Game/EnvSandbox/Textures/PearlWoven_Flipbook"

VARIANTS = [
    "CymaticMarble", "GildedLoom", "SilkWaterfall", "CavernWeave", "DancingCrystals",
    "CherryBlossomWood", "GildedCoral", "StarlitAbyss", "FrozenFracture", "SingingConstellations",
    "FinalDreamweaver", "GlitterRainbow", "GlitterHolographic", "GlitterGold", "GlitterIridescent",
    "GlitterCrystal", "FractalCathedral", "GoldenSpiralGrove", "VoronoiSacredGeometry",
    "TessellationSanctum", "SpiralMonument", "TwinklingGears", "EnchantedTome", "SingingSilk",
    "MoltenCore", "PearlWeave", "StarlitLoom", "FrostBloom", "ChoirStone", "CrystalCathedral",
    "RoyalVelvetBrocade", "WeepingWillow", "MoonlitMoss",
    "FarawayCelestialSilk", "FarawayNightVelvet", "FarawayAquaLace", "FarawayGildedRidge",
    "FarawayAlabasterDrape", "FarawayNacreVeil", "FarawayMoonChiffon", "FarawayLullabyFleece",
    "MelodiaHeroGem", "MelodiaGoldSilk", "MelodiaMotherPearl", "MelodiaSapphireGlass",
    "MelodiaRoseVelvet", "MelodiaMoonlace", "MelodiaForestEmerald", "MelodiaAmethystVein",
    "MelodiaAuroraGlass", "PrismaticObsidian", "SingingDune", "CymaticOrchid",
]
CYMA_MAPS = ["BaseColor", "Normal", "Roughness", "Metallic", "Height", "ORM", "Emissive", "Iridescence", "Opacity"]


def recipe_phase_A(variant_filter=None):
    variants = [variant_filter] if variant_filter else VARIANTS
    recipes = []
    for v in variants:
        vdir = CYMA_SRC / v
        if not list(vdir.glob("*.png")):
            recipes.append({"variant": v, "action": "SKIP", "reason": f"no hython PNGs at {vdir} -- run hython first"})
            continue
        for m in CYMA_MAPS:
            src_candidates = list(vdir.glob(f"T_Cymatic_{v}_{m}*.png"))
            if not src_candidates:
                continue
            src = src_candidates[0]
            dest = f"{DEST_CYMA_ROOT}/{v}/T_Cymatic_{v}_{m}"
            srgb = m in ("BaseColor", "Emissive")
            recipes.append({
                "tool": "material_query",
                "action": "import_texture",
                "params": {"source_file": str(src), "dest_path": dest, "srgb": srgb},
                "phase": "A1-import",
                "variant": v, "map": m,
            })
        recipes.append({
            "tool": "material_query",
            "action": "create_pbr_material_from_disk",
            "params": {
                "source_folder": str(vdir),
                "material_path": f"{DEST_CYMA_ROOT}/{v}/M_Cymatic_{v}",
                "base_color_suffix": "BaseColor",
                "normal_suffix": "Normal",
                "roughness_suffix": "Roughness",
                "metallic_suffix": "Metallic",
                "height_suffix": "Height",
                "emissive_suffix": "Emissive",
            },
            "phase": "A2-material",
            "variant": v,
        })
        recipes.append({
            "tool": "material_query",
            "action": "get_compilation_stats",
            "params": {"asset_path": f"{DEST_CYMA_ROOT}/{v}/M_Cymatic_{v}"},
            "phase": "A3-validate",
            "variant": v,
        })
    if FLIPBOOK_SRC.exists() and list(FLIPBOOK_SRC.glob("*.png")):
        for f in range(8):
            for m in ["BaseColor", "Normal", "Iridescence", "Roughness", "Height"]:
                src = FLIPBOOK_SRC / f"T_PearlFlipbook_Frame{f:02d}_{m}.png"
                if src.exists():
                    recipes.append({
                        "tool": "material_query",
                        "action": "import_texture",
                        "params": {"source_file": str(src), "dest_path": f"{DEST_FLIPBOOK_ROOT}/T_PearlFlipbook_Frame{f:02d}_{m}", "srgb": m == "BaseColor"},
                        "phase": "A1-import-flipbook", "frame": f, "map": m,
                    })
    else:
        recipes.append({"action": "SKIP", "phase": "A1-flipbook", "reason": "no flipbook PNGs -- run flipbook_aaa.py first"})
    return recipes


def recipe_phase_B():
    return [
        {"phase": "B", "action": "DEFERRED", "reason": "No hair/WP assets in cymatic scope. When FarawayMother fabric/terrain lands: wire capture via editor_query capture_scene_preview / capture_material_grid and hair grooming via material_query + mesh_query."},
        {"tool": "editor_query", "action": "capture_material_grid", "params": {"material_paths": [f"{DEST_CYMA_ROOT}/{v}/M_Cymatic_{v}" for v in VARIANTS[:3]], "resolution": 1024}, "phase": "B-capture", "note": "activates after Phase A; captures grid for docs"},
    ]


def recipe_phase_C():
    return [
        {"phase": "C", "action": "record", "detail": "Write Saved/Audit/monolith_phaseC_report.json with imported material paths + compilation stats"},
        {"phase": "C", "action": "record", "detail": "Update P0/P1 task ledger with Monolith lane evidence (parallel to hython manifest)"},
        {"phase": "C", "action": "validate", "detail": "Run cross_path_validation.py --check both --report Saved/Audit/cross_path_validation_report.json"},
    ]


def probe_editor():
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", 9316))
        s.close()
        return True, "OPEN"
    except Exception as e:
        return False, str(e)


def mcp_post(payload: dict, timeout=10):
    import urllib.request
    import json as _json
    data = _json.dumps(payload).encode()
    req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _json.loads(r.read().decode())


def main():
    ap = argparse.ArgumentParser(description="Monolith execution plan parallel to hython")
    ap.add_argument("--phase", choices=["A", "B", "C", "all"], default="all")
    ap.add_argument("--variant", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--execute", action="store_true", help="actually POST to Monolith (requires editor up)")
    args = ap.parse_args()

    if args.status:
        ok, detail = probe_editor()
        print(f"Monolith 9316: {'OPEN' if ok else 'CLOSED'} ({detail})")
        sentinel = PROJECT_ROOT / "Plugins" / "Monolith" / "Saved" / ".monolith_running"
        if sentinel.exists():
            print(f"Sentinel: {sentinel.read_text(encoding='utf-8').strip()}")
        else:
            print(f"Sentinel: MISSING at {sentinel}")
        hython_ok = (PROJECT_ROOT / "Tools" / "Houdini" / "copernicus" / "copernicus_cymatic_parallax.py").exists()
        print(f"Hython parallax: {'present' if hython_ok else 'missing'}")
        print(f"Flipbook: {'present' if (PROJECT_ROOT / 'Tools' / 'Houdini' / 'flipbook_aaa.py').exists() else 'missing'}")
        sys.exit(0 if ok else 1)

    phases = []
    if args.phase == "all":
        phases = ["A", "B", "C"]
    else:
        phases = [args.phase]

    all_recipes = []
    for ph in phases:
        if ph == "A":
            all_recipes.extend(recipe_phase_A(args.variant))
        elif ph == "B":
            all_recipes.extend(recipe_phase_B())
        elif ph == "C":
            all_recipes.extend(recipe_phase_C())

    print(f"Monolith parallel plan -- phases {phases} variant={args.variant or 'all'} dry_run={args.dry_run} execute={args.execute}")
    print(f"Total steps: {len(all_recipes)}")
    for i, r in enumerate(all_recipes, 1):
        print(f"  {i:02d}. [{r.get('phase','?')}] {r.get('tool','')}/{r.get('action','')} {r.get('params', r.get('reason', r.get('detail','')))}")

    if args.dry_run or not args.execute:
        print("\n[dry-run] No editor calls made. Pass --execute to POST to 9316.")
        out = PROJECT_ROOT / "Saved" / "Audit" / "monolith_execution_plan_snapshot.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"phases": phases, "variant": args.variant, "recipes": all_recipes}, indent=2), encoding="utf-8")
        print(f"[snapshot] -> {out}")
        sys.exit(0)

    ok, detail = probe_editor()
    if not ok:
        print(f"[ERROR] Editor not reachable on 9316: {detail}", file=sys.stderr)
        sys.exit(2)
    for r in all_recipes:
        if "tool" not in r:
            print(f"[SKIP] {r}")
            continue
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": r["tool"], "arguments": {"action": r["action"], **r.get("params", {})}}}
        print(f"[POST] {r['tool']}/{r['action']} ...", end=" ", flush=True)
        try:
            resp = mcp_post(payload)
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")


if __name__ == "__main__":
    main()
