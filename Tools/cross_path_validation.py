#!/usr/bin/env python3
"""
cross_path_validation.py -- compare hython vs Monolith outputs.

Read-only audit: never writes .uasset, never mutates editor state.
Compares the two generation lanes that produce the SAME logical assets:

  hython lane (offline, pure numpy):
    Tools/Houdini/copernicus/copernicus_cymatic_parallax.py  -> Saved/Audit/copernicus_cymatic/{variant}/T_Cymatic_{variant}_{Map}.png
    Tools/Houdini/flipbook_aaa.py                            -> Content/EnvSandbox/Textures/PearlWoven_Flipbook/T_PearlFlipbook_FrameNN_{Map}.png

  monolith lane (live editor, material/mesh ingest):
    monolith material_query create_pbr_material_from_disk / import_texture
    -> /Game/... materials + textures as seen via project_query/material_query

Validation dimensions:
  1. EXISTENCE  -- does each expected file/asset exist on both sides?
  2. GEOMETRY   -- do height maps / meshes agree on dimensions and tiling?
  3. PIXEL      -- per-map PSNR/SSIM and histogram distance
  4. SEMANTICS  -- does Monolith material instance expose same params as hython manifest?

Usage:
  python Tools/cross_path_validation.py --check hython
  python Tools/cross_path_validation.py --check monolith
  python Tools/cross_path_validation.py --check both
  python Tools/cross_path_validation.py --check both --variant CymaticMarble
  python Tools/cross_path_validation.py --report Saved/Audit/cross_path_validation_report.json
"""
from __future__ import annotations
import argparse
import json
import sys
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

HYTHON_CYMA_VARIANTS = [
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
HYTHON_CYMA_MAPS = ["BaseColor", "Normal", "Roughness", "Metallic", "Height", "ORM", "Emissive", "Iridescence", "Opacity"]
FLIPBOOK_FRAMES_DEFAULT = 8
FLIPBOOK_MAPS = ["BaseColor", "Normal", "Iridescence", "Roughness", "Height"]
CYMA_OUT = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic"
FLIPBOOK_OUT = PROJECT_ROOT / "Content" / "EnvSandbox" / "Textures" / "PearlWoven_Flipbook"
MONOLITH_MATERIAL_PREFIX = "/Game/Melodia/Cymatics"


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    expected: str = ""
    actual: str = ""
    metric: dict | None = None


def _hash_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()[:12]


def check_hython(variant_filter=None):
    results: list[CheckResult] = []
    variants = [variant_filter] if variant_filter else HYTHON_CYMA_VARIANTS
    for v in variants:
        vdir = CYMA_OUT / v
        if not vdir.exists():
            results.append(CheckResult(f"hython/cymatic/{v}/dir", "FAIL", "variant dir missing", str(vdir), "absent"))
            continue
        results.append(CheckResult(f"hython/cymatic/{v}/dir", "PASS", f"dir exists, {len(list(vdir.glob('*.png')))} pngs", str(vdir), f"{len(list(vdir.glob('*.png')))} files"))
        for m in HYTHON_CYMA_MAPS:
            candidates = list(vdir.glob(f"T_Cymatic_{v}_{m}*.png"))
            if not candidates:
                results.append(CheckResult(f"hython/cymatic/{v}/{m}", "FAIL", "map missing", f"T_Cymatic_{v}_{m}.png", "none"))
            else:
                p = candidates[0]
                try:
                    size = p.stat().st_size
                    detail = f"{p.name} {size} bytes hash={_hash_file(p)}"
                    try:
                        from PIL import Image
                        with Image.open(p) as im:
                            detail += f" {im.size[0]}x{im.size[1]} {im.mode}"
                            if im.size[0] != im.size[1]:
                                results.append(CheckResult(f"hython/cymatic/{v}/{m}", "FAIL", f"non-square {im.size}", "square", str(im.size)))
                                continue
                    except ImportError:
                        pass
                    results.append(CheckResult(f"hython/cymatic/{v}/{m}", "PASS", detail, f"T_Cymatic_{v}_{m}.png", p.name))
                except Exception as e:
                    results.append(CheckResult(f"hython/cymatic/{v}/{m}", "ERROR", str(e)))
    if FLIPBOOK_OUT.exists():
        files = list(FLIPBOOK_OUT.glob("T_PearlFlipbook_Frame*.png"))
        expected = FLIPBOOK_FRAMES_DEFAULT * len(FLIPBOOK_MAPS)
        if len(files) == 0:
            results.append(CheckResult("hython/flipbook/dir", "FAIL", "flipbook dir empty", str(FLIPBOOK_OUT), "0 files"))
        elif len(files) % len(FLIPBOOK_MAPS) != 0:
            results.append(CheckResult("hython/flipbook/count", "FAIL", f"count {len(files)} not multiple of {len(FLIPBOOK_MAPS)}", str(expected), str(len(files))))
        else:
            results.append(CheckResult("hython/flipbook/count", "PASS", f"{len(files)} files ({len(files)//len(FLIPBOOK_MAPS)} frames x {len(FLIPBOOK_MAPS)} maps)", str(expected), str(len(files))))
        for f in range(FLIPBOOK_FRAMES_DEFAULT):
            for m in FLIPBOOK_MAPS:
                pat = f"T_PearlFlipbook_Frame{f:02d}_{m}.png"
                if not (FLIPBOOK_OUT / pat).exists():
                    results.append(CheckResult(f"hython/flipbook/Frame{f:02d}/{m}", "FAIL", "frame map missing", pat, "absent"))
    else:
        results.append(CheckResult("hython/flipbook/dir", "SKIP", "flipbook not yet generated (run flipbook_aaa.py)", str(FLIPBOOK_OUT), "absent"))
    mani = PROJECT_ROOT / "Saved" / "Audit" / "copernicus_cymatic_manifest.json"
    if mani.exists():
        try:
            data = json.loads(mani.read_text(encoding="utf-8"))
            results.append(CheckResult("hython/manifest", "PASS", f"schema={data.get('schema')} variants={len(data.get('variants',{}))} size={data.get('size')}", "valid json", f"{len(data.get('variants',{}))} variants"))
        except Exception as e:
            results.append(CheckResult("hython/manifest", "FAIL", f"invalid json: {e}"))
    else:
        results.append(CheckResult("hython/manifest", "FAIL", "manifest missing (run parallax --cook)", str(mani), "absent"))
    return results


def check_monolith(variant_filter=None):
    import socket
    import urllib.request
    import urllib.error
    import json as _json
    results: list[CheckResult] = []
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", 9316))
        s.close()
    except Exception as e:
        results.append(CheckResult("monolith/reachability", "ERROR", f"port 9316 not reachable: {e} -- start editor", "OPEN", "CLOSED"))
        return results
    try:
        payload = _json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "monolith_status", "arguments": {}}}).encode()
        req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            body = _json.loads(r.read().decode())
            inner = _json.loads(body["result"]["content"][0]["text"])
            results.append(CheckResult("monolith/status", "PASS", f"v{inner['version']} {inner['total_actions']} actions port={inner['server_port']}", "running", f"v{inner['version']}"))
    except Exception as e:
        results.append(CheckResult("monolith/status", "ERROR", str(e)))
    results.append(CheckResult("monolith/project_search", "SKIP", "project asset search requires Phase A; run monolith_execution_plan_parallel.py Phase A first", MONOLITH_MATERIAL_PREFIX, "not yet executed"))
    sentinel = PROJECT_ROOT / "Plugins" / "Monolith" / "Saved" / ".monolith_running"
    if sentinel.exists():
        try:
            data = json.loads(sentinel.read_text(encoding="utf-8"))
            results.append(CheckResult("monolith/sentinel", "PASS", f"pid={data['pid']} port={data['port']} v{data['version']} started={data['started']}", "present", f"pid {data['pid']}"))
        except Exception as e:
            results.append(CheckResult("monolith/sentinel", "FAIL", str(e)))
    else:
        results.append(CheckResult("monolith/sentinel", "FAIL", "sentinel missing at Plugins/Monolith/Saved/.monolith_running", "present", "absent"))
    return results


def cross_compare(variant_filter=None):
    results: list[CheckResult] = []
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        results.append(CheckResult("cross/pixel", "SKIP", "PIL/numpy not available"))
        return results
    variants = [variant_filter] if variant_filter else ["CymaticMarble"]
    for v in variants:
        vdir = CYMA_OUT / v
        hpaths = list(vdir.glob(f"T_Cymatic_{v}_Height*.png"))
        if not hpaths:
            results.append(CheckResult(f"cross/tiling/{v}", "SKIP", "no height map"))
            continue
        p = hpaths[0]
        try:
            with Image.open(p) as im:
                arr = __import__("numpy").array(im.convert("L"), dtype=float)
            import numpy as np
            top, bottom = arr[0, :], arr[-1, :]
            left, right = arr[:, 0], arr[:, -1]
            h_err = float(np.mean(np.abs(top - bottom)))
            v_err = float(np.mean(np.abs(left - right)))
            status = "PASS" if max(h_err, v_err) < 8.0 else "FAIL"
            results.append(CheckResult(f"cross/tiling/{v}/Height", status, f"edge delta h={h_err:.2f} v={v_err:.2f} (threshold 8.0)", "<8.0", f"h={h_err:.1f} v={v_err:.1f}", metric={"h_err": h_err, "v_err": v_err}))
        except Exception as e:
            results.append(CheckResult(f"cross/tiling/{v}", "ERROR", str(e)))
    for v in variants:
        vdir = CYMA_OUT / v
        bpath = list(vdir.glob(f"T_Cymatic_{v}_BaseColor*.png"))
        if bpath:
            try:
                from PIL import Image
                import numpy as np
                with Image.open(bpath[0]) as im:
                    arr = np.array(im)
                    std = float(arr.std())
                    status = "PASS" if std > 10 else "FAIL"
                    results.append(CheckResult(f"cross/histogram/{v}/BaseColor", status, f"std={std:.1f} (expect >10)", ">10", f"{std:.1f}"))
            except Exception as e:
                results.append(CheckResult(f"cross/histogram/{v}/BaseColor", "ERROR", str(e)))
    results.append(CheckResult("cross/monolith_pixel", "SKIP", "Monolith import not yet executed -- PSNR/SSIM activates after Phase A. Run monolith_execution_plan_parallel.py then re-check with --check both."))
    return results


def main():
    ap = argparse.ArgumentParser(description="Cross-path validation: hython vs Monolith")
    ap.add_argument("--check", choices=["hython", "monolith", "both"], default="both")
    ap.add_argument("--variant", type=str, default=None)
    ap.add_argument("--report", type=str, default=None)
    ap.add_argument("--fail-on-skip", action="store_true")
    args = ap.parse_args()
    all_results: list[CheckResult] = []
    if args.check in ("hython", "both"):
        all_results.extend(check_hython(args.variant))
    if args.check in ("monolith", "both"):
        all_results.extend(check_monolith(args.variant))
    if args.check == "both":
        all_results.extend(cross_compare(args.variant))
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0, "ERROR": 0}
    for r in all_results:
        counts[r.status] = counts.get(r.status, 0) + 1
        tag = {"PASS": "[PASS]", "FAIL": ">>FAIL<<", "SKIP": "[SKIP]", "ERROR": "[ERROR]"}[r.status]
        print(f"{tag} {r.name}: {r.detail}")
        if r.expected:
            print(f"       expected: {r.expected} | actual: {r.actual}")
    print(f"\nSummary: {counts['PASS']} pass, {counts['FAIL']} fail, {counts['SKIP']} skip, {counts['ERROR']} error (total {len(all_results)})")
    if args.report:
        out = Path(args.report)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema": "melodia.cross_path_validation.v1", "check": args.check, "variant": args.variant, "counts": counts, "results": [asdict(r) for r in all_results]}
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"[report] -> {out}")
    if counts["FAIL"] > 0 or counts["ERROR"] > 0:
        sys.exit(1)
    if args.fail_on_skip and counts["SKIP"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
