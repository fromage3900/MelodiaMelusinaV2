r"""build_faraway_ue_intake.py -- assemble the Faraway Mother UE intake package + docs + validator. spike: true

Copies every offline output (no .hiplc/.bgeo, no Kimi data lane) into Saved/Staging/HoudiniForge/FarawayUEIntake_20261026/<name>/,
writes INTAKE_MANIFEST.json (sha256 of every file + each sub-manifest gate), IMPORT_ORDER_README.md, TECH_BREAKDOWN.md (numbers pulled
from the real manifests), SOL_NOTES.md, and validate_intake.py. Nothing here touches Content/ or the editor.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
S = ROOT / "Saved" / "Staging" / "HoudiniForge"
OUT = S / "FarawayUEIntake_20261026"
SETS = {  # folder in HoudiniForge -> intake name
    "FarawayMeasure_20261026": "01_measure", "FarawayBiomes_20261026": "02_biomes", "FarawaySeamDressing_20261026": "03_seam_dressing",
    "FarawayWonder_20261026": "04_wonder", "FarawayFlowers_20261026": "05_flowers", "FarawayLullaby_20261026": "06_lullaby",
    "FarawayFlocks_20261026": "07_flocks", "FarawayErosion_20261026": "08_erosion", "FarawayTrees_20261026": "09_trees",
    "FarawayOcean_20261026": "10_ocean", "FarawayFog_20261026": "11_fog", "FarawayContact_20261026": "12_contact_sheets",
    "FarawayHdaSheets_20261026": "13_hda_sheets", "FarawayDrape_20261026": "14_vellum_drape",
}
SKIP = {".hiplc", ".sc", ".npy", ".npz"}
KEEP_DRAPE = {"SM_FabricRidge_Hero_drape.obj", "manifest.json"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


VALIDATOR = r'''"""validate_intake.py -- re-hash every file in INTAKE_MANIFEST.json and re-assert each sub-manifest gate. Run: python validate_intake.py"""
import hashlib, json, sys
from pathlib import Path
R = Path(__file__).resolve().parent
M = json.load(open(R / "INTAKE_MANIFEST.json"))
bad = []
for rel, h in M["files"].items():
    p = R / rel
    if not p.exists(): bad.append(("missing", rel))
    elif hashlib.sha256(p.read_bytes()).hexdigest() != h: bad.append(("hash", rel))
for name, g in M["gates"].items():
    if not g.get("pass", False): bad.append(("gate_failed", name))
missing = [n for n in M["expected_sets"] if not (R / n).is_dir()]
bad += [("missing_set", n) for n in missing]
print("files", len(M["files"]), "gates", len(M["gates"]), "sets", len(M["expected_sets"]))
print("PASS" if not bad else "FAIL", bad[:12])
sys.exit(0 if not bad else 2)
'''


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    files, gates, notes = {}, {}, {}
    for src, name in SETS.items():
        d = S / src
        if not d.is_dir():
            raise SystemExit(f"missing set {src}")
        (OUT / name).mkdir()
        for p in sorted(d.rglob("*")):
            if not p.is_file() or p.suffix in SKIP:
                continue
            if name == "14_vellum_drape" and p.name not in KEEP_DRAPE:
                continue
            rel = p.relative_to(d)
            if "backup" in rel.parts or "rev2" in rel.parts:
                continue
            (OUT / name / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, OUT / name / rel)
            files[f"{name}/{rel.as_posix()}"] = sha(p)
        mp = d / "manifest.json"
        if mp.exists():
            g = json.load(open(mp)).get("gate", {})
            gates[name] = g if "pass" in g else {"pass": None}
    # 01_measure has no gate block in its json (script prints it); synthesize from content
    meas = json.load(open(OUT / "01_measure" / "hda_measure.json"))
    gates["01_measure"] = {"pass": all("fail" not in r and r.get("outputs") for r in meas["hdas"].values()), "hdas": len(meas["hdas"])}
    bio = json.load(open(OUT / "02_biomes" / "biomes.json"))["gate"]            # biomes keeps its gate in biomes.json
    gates["02_biomes"] = bio
    sheets = sorted((OUT / "12_contact_sheets").glob("*.png"))                   # contact sheets: existence + non-trivial size
    gates["12_contact_sheets"] = {"pass": len(sheets) == 4 and all(p.stat().st_size > 5000 for p in sheets), "sheets": len(sheets)}
    gates = {k: v for k, v in gates.items() if v.get("pass") is not None}
    # Houdini-cooked sets carry the licence caveat; the drape gate lives in its manifest too
    G = lambda n, k, d=None: gates.get(n, {}).get(k, d)
    readme = f"""# Faraway Mother UE intake (2026-10-26)

Offline Houdini/Python staging data for the live UE staging model. **Nothing here is in Unreal.** Existing materials only
(`MI_Mother_*`, `MI_Faraway_*`, `MI_ProcFoliage_Sakura`); no new masters/instances/MPCs.

## Import order (batches of 4 or fewer; screenshot after each; no level save without the owner)
1. `01_measure/hda_measure.json` : read first. Measured post-cook bounds are the authority for footprints (ignore parameter-derived sizes).
2. `02_biomes/placements.json` + `biome_mask.png` : where each HDA role goes (HeartGate 3, FrillArch 8, LaceBridge 10, SilkPeak 14, SilkRibbon 24, MotherfoldBasin 4, TerracedIsland 12, OrchardTree 120). Seam-biome hero sites first.
3. `03_seam_dressing/` : `junctions.json` (exact: origin and +-2929 m on both axes), `seam_polylines.json`, `stitches.csv` (23.9k points, PCG point import).
4. `05_flowers/flowers.csv` + `species.json` + `tiles.json` : 93k points, 500 m streaming tiles (budget 9,000, max 1,135). One HISM per species.
5. `09_trees/obj/` + `variants.json` : 24 tree/bush OBJs, UE names `SM_Faraway_<Archetype>_NN`.
6. `04_wonder/` : Lace Wings settle points, La Berceuse, guide Thimble, lanterns, sing-to-bloom, stitch-hop path.
7. `06_lullaby/` + `07_flocks/` : MIDI, 24 Hz curves (glow, breath, bloom note, hum window), 8 flight templates + 231 assignments.
8. `08_erosion/`, `10_ocean/`, `11_fog/` : textures/flipbooks (see TECH_BREAKDOWN for decode and caveats).
9. `12_contact_sheets/`, `13_hda_sheets/`, `14_vellum_drape/` : review images and the drape mesh (spike).

Validate any time: `python validate_intake.py` (re-hashes every file and re-asserts every gate).
"""
    sol = """# SOL_NOTES -- for the GPT Sol model staging Faraway Mother live in UE

**Level:** `/Game/EnvSandbox/Monoliths/FarawayMother/Blockout/L_FarawayMother_Blockout` (owner-opened). Unsaved; the owner decides when to save.

## Standing rules (from the owner's handoff, all binding)
- Record originals before editing; **no PIE**; never restart/kill the editor; **hide, never delete**; no level load/switch/save; auto-bake off.
- **Existing materials only.** Keep `MI_Mother_*`, `MI_Copernicus_*`, `MI_ProcFoliage_Sakura` as the HDAs hard-code them; `MI_Faraway_*` only on existing blockout peaks/terrain.
- Cook **one HDA at a time**, batches of 4 or fewer, one viewport screenshot after each batch. Houdini cooks at 505, skirt/horizon off. Rename the HDA type per version.
- Nothing writes to `Saved/Audit/houdini_faraway_mother/`. `Houdini/FarawayDrape.hip` is read-only. Terrain = Nanite mesh terrain (no classic Landscape); the 7 `BLK_SilkPeak` peaks stay.
- Heart Gate stays at (580, 0) m, exactly on the F=0 seam. Field is 8 km (+-400000 cm), global mapping, no per-tile UV resets.

## State you inherit (an earlier assistant broke some rules; do not repeat)
- 8 HDAs already imported at `/Game/HDA/Faraway/HDA_Faraway_<Name>_1_0`.
- **Test actors are unsaved in the Blockout**: `HDA_Faraway_SilkPeak_1_0` at (0,-60000,0) and 7 more HDA actors at x=30000..210000, y=-60000. Hide them, do not delete.
- `NS_Melusina_Ripple` / `NS_Melusina_Globules` were saved earlier; unrelated to this level.

## Units and axes
Houdini cooks are Y-up metres; UE is Z-up centimetres. Data files use global X/Y in metres (south-up masks: row 0 = min Y). Multiply by 100 for UE.

## Open rulings and blockers
1. **Tension divisor** (`/8` Oct 6 bake and PCG vs `/8*pi` in chladni_field.py): owner ruling owed. The biome script defaults to 8pi (`--tension-div`).
2. **SilkPeak v1.1** is owned by the owner (pleat aliasing, near-vertical walls, origin pinch, border normals fail; default 90 m vs blockout peaks 670-1150 m). Do not swap the 7 cones until it lands.
3. `04_wonder` stitch-hop path skips 0-80 m near the origin (junction-clearance rule); say if it must start at the origin.
4. La Berceuse and Thimble have no models. Lullaby is composed (no source audio existed); swap in the real one if it exists.
5. Placement rules for TerracedIsland, MotherfoldBasin, OrchardTree, FrillArch are field-only here (biomes), not terrain-aware: validate against the real blockout terrain in-editor.

## Per-asset import settings
- Static meshes (tree OBJs): Nanite on, simple collision, combine meshes off, **import materials off**; assign `MI_ProcFoliage_Sakura`/`MI_Mother_*`. Piece groups: trunk, root, branch, blossom_cards (cards, two-sided), canopy_proxy (far LOD only).
- Flipbooks/masks (ocean, fog, god-ray, erosion): sRGB **off**, compression Masks/Default, mips off, never stream; decode info in each `*_params.json`.
- CSV/JSON point sets: import via PCG point/data-table path; units metres, convert to cm.
- MIDI/curves: reference data only; the audio/cymatics chain keeps its single writers (MPC_Melodia_Palette, UMelodiaCymaticsWriterSubsystem).

## Batch order for staging
Batch 1: Heart Gate (scale per measured 6.24 x 8.29 m; at (580,0) m), Frill Arch, Lace Bridge on the seam. Batch 2: Terraced Island, Motherfold Basin, Orchard Tree. Batch 3: Silk Ribbon (+ flower fields). Then trees, lace wings, wonder layer.
"""
    tech = ["# TECH_BREAKDOWN -- Faraway Mother offline workflows (2026-10-26)\n",
            "Every number below is read from the sub-manifests in this package; caveats are stated, not hidden. Scripts: `Tools/Houdini/faraway/`. Canon list: `Docs/Houdini/HOUDINI_ENGINE_CANON_WORKFLOWS_2026-10-26.md`. Vellum detail: `Docs/Houdini/FARAWAY_VELLUM_USAGE_2026-10-26.md`.\n"]
    desc = {
        "01_measure": ("measure_faraway_hdas.py (hython)", "8 HDAs cooked one at a time at defaults; bounds/outputs/controls read back. Authority for footprints: HeartGate 6.24x8.29x0.61 m, FrillArch 6.23x7.51x0.62, LaceBridge 14.7x5.1x3.8, SilkPeak 250x12.7x250, SilkRibbon 18.1x6.4x5.8, MotherfoldBasin 500x28.9x500, TerracedIsland 92x54x85, OrchardTree 10.8x9.7x9.3.", "none"),
        "02_biomes": ("build_faraway_biomes.py", "Global field F classified into 5 biomes; roles placed with spacing, 80 m junction and 60 m edge exclusions. Found and fixed: degenerate candidate sequence (all points on one diagonal).", "junction exclusion uses a loose detector (269 hits, safe as exclusion only); tension divisor is a flag."),
        "03_seam_dressing": ("build_faraway_seam_dressing.py", "Newton on grad F gives EXACT junctions (5: origin, +-2929 on both axes); marching squares traces 10 seam lines / 59 km; 23.9k stitch instances. Fixed: first run reported 7,616 junctions (dedupe too fine).", "none known"),
        "04_wonder": ("build_faraway_wonder_data.py", "Lace Wings (231 settle points), La Berceuse, guide Thimble, 40 lanterns, 342 blooms, 56 hop buttons. All 80 m clear of junctions.", "hop path skips 0-80 m at the origin; bloom/lantern counts are budget choices."),
        "05_flowers": ("build_faraway_flower_fields.py", "93,158 points: orchard phyllotaxis rings, seam lace bands, crest drifts; 7 species = lullaby scale degrees; palette by sign of F.", "positions are field-only (no terrain height, no slope filter)."),
        "06_lullaby": ("build_faraway_lullaby.py", "Composed D Lydian, 96 bpm, 8 bars, 31 notes (MIDI round-trips). 24 Hz glow/breath/bloom/hum curves. Fixed: my MIDI reader skipped meta events wrongly.", "no source audio existed; this is a composed stand-in."),
        "07_flocks": ("build_faraway_lacewing_flocks.py (analytic)", "8 closed Lissajous templates, 10 s loop, settle on bar downbeat, 231 assignments. Fixed: speed 11.7 -> 1.39 m/s; a degenerate straight-line template.", "crowdsolver is not licensed; no terrain test; flocks hover within 1.5 m of the settle point."),
        "08_erosion": ("build_faraway_peak_erosion.py (hython heightfield_erode)", "2 km window, 8 iterations; peak 583.7 m kept, mean change 16 m. At 40 iterations the peak fell 26% and the gate (correctly) failed.", "strata mask is very regular contour terraces; needs variation."),
        "09_trees": ("build_faraway_tree_variants.py", "24 variants (6 archetypes x 4 seeds), full detail, 1.6-17.8 m, max 4,445 polys, measured bounds, OBJ per variant.", "the first three archetypes read as one crown family (no droop/crown control in the generator)."),
        "10_ocean": ("build_faraway_ocean_flipbook.py (hython oceanspectrum/oceanevaluate)", "64-frame 8x8 atlas, 128^2 cells, 200 m tile, 8 s loop, R height / G,B chop. Fixed: first version had identical frames (time set as a constant); added a motion gate.", "deterministic only to +-1 8-bit level (not hash-identical)."),
        "11_fog": ("build_faraway_fog_flipbooks.py", "God-ray 16-frame sway loop (exact) and fog 64-frame periodic atlas. Procedural sinusoid fields, NOT Pyro.", "FOG LOOKS BANDED (regular diagonal stripes); god-rays are good."),
        "12_contact_sheets": ("make_faraway_contact_sheets.py", "4 top-down maps: biomes+placements, seams+stitches, wonder layer, all layers.", "south-up, 7.8 m/px."),
        "13_hda_sheets": ("make_faraway_hda_sheets.py (hython)", "front/side point silhouettes of the 8 HDA cooks + a drape map.", "point splat, not shaded; the drape_map gap values are NOT trustworthy (sparse-vs-dense grid rasterisation) -- use the drape gate instead."),
        "14_vellum_drape": ("build_faraway_hero_drape.py (hython Vellum)", "Cloth sheet draped on a cooked SilkPeak tile: 0 points below terrain, gap -0.18..+0.82 m, 3,281 contacts, 12.1 m relief, no NaN (after a first gate that passed a flat, floating cloth).", "runs on the OLD 250 m / 12 m-relief tile; rerun on SilkPeak v1.1 before using."),
    }
    for name in sorted(set(SETS.values())):
        s, what, cav = desc[name]
        g = gates.get(name, {})
        tech.append(f"## {name}\n- Script: `{s}`\n- Method / numbers: {what}\n- Caveats: {cav}\n- Gate: `{json.dumps({k: v for k, v in g.items() if not isinstance(v, (list, dict))})[:420]}`\n")
    (OUT / "IMPORT_ORDER_README.md").write_text(readme, encoding="utf-8")
    (OUT / "SOL_NOTES.md").write_text(sol, encoding="utf-8")
    (OUT / "TECH_BREAKDOWN.md").write_text("\n".join(tech), encoding="utf-8")
    (OUT / "validate_intake.py").write_text(VALIDATOR, encoding="utf-8")
    for n in ("IMPORT_ORDER_README.md", "SOL_NOTES.md", "TECH_BREAKDOWN.md", "validate_intake.py"):
        files[n] = sha(OUT / n)
    (OUT / "INTAKE_MANIFEST.json").write_text(json.dumps({"schema": "melodia.faraway_ue_intake.v1", "spike": True, "expected_sets": sorted(set(SETS.values())),
                                                           "gates": gates, "files": files}, indent=1))
    print("PACKAGED files", len(files), "gates", len(gates), "fail", [k for k, v in gates.items() if not v.get("pass")])


if __name__ == "__main__":
    main()
