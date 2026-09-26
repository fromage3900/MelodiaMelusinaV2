"""World Compiler UE lane -- editor-only consumer of a compiled bundle.

Contract: Docs/WorldGen/WORLD_COMPILER_CONTRACT.md section 6.
Runs INSIDE the editor (Monolith editor.run_python, mode execute_file, with args),
one step per call so every step lands on a real frame boundary:

    world_compiler_ue.py <bundle_dir> preflight
    world_compiler_ue.py <bundle_dir> cleanup          # delete tagged actors + known husks
    world_compiler_ue.py <bundle_dir> materials        # verify/forge the 7 band MIs (BaseTint only)
    world_compiler_ue.py <bundle_dir> table            # fill DT_<recipe>_Points from points.csv
    world_compiler_ue.py <bundle_dir> volume           # place the bounded PCG volume with the template graph
    world_compiler_ue.py <bundle_dir> generate         # comp.generate(force) -- returns immediately
    world_compiler_ue.py <bundle_dir> count            # per-band ISM counts (poll until stable)
    world_compiler_ue.py <bundle_dir> save             # save level + WorldCompiler folder, unattended
    world_compiler_ue.py <bundle_dir> fx_systems       # duplicate named EnvSandbox NS/M parents into Melodia children
    world_compiler_ue.py <bundle_dir> fx_materials     # forge FX MIs from the four hero parents (if they exist)
    world_compiler_ue.py <bundle_dir> fx_place         # place tagged NiagaraActors from fx_anchors.csv
    world_compiler_ue.py <bundle_dir> fx_audit         # effect type / bounds / shadow gates per NS_Morning_*
    world_compiler_ue.py <bundle_dir> hide_houdini_overlays
    world_compiler_ue.py <bundle_dir> lookdev_cameras  # recipe JSON cameras; hides Houdini overlays
    world_compiler_ue.py <bundle_dir> lookdev_capture  # SceneCapture stills; frozen PPV left as-is
    world_compiler_ue.py <bundle_dir> bookmark         # fill DA_MorningRainbowBloom
    world_compiler_ue.py <bundle_dir> ensure_euw       # EUW_WorldCompiler apply console (compile stays CLI)

Every step writes <bundle_dir>/ue/<step>.json and prints nothing (Monolith swallows
stdout); the driver Tools/world_compiler_ue_driver.py sequences steps and assembles
Saved/Audit/world_compiler_<recipe>_proof_<date>.json.

Rules honoured here: never add/remove PCG edges or nodes; never edit a material
master; never write an MPC parameter; never load_level from this script (the
driver does the reload via Monolith after save); never time.sleep.
"""
from __future__ import annotations

import csv
import json
import math
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import unreal

AL = unreal.EditorAssetLibrary
ELL = unreal.EditorLevelLibrary
MEL = unreal.MaterialEditingLibrary
ROOT = Path(__file__).resolve().parents[2]

GHOSTLOTUS_TEXTURES = (
    ("Albedo", "/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Albedo"),
    ("EmissiveMap", "/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Emissive"),
    ("Normal", "/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Normal"),
)
KNOWN_HUSK_LABELS = ("PCG_RainbowBloom_Field", "RainbowBloom_TestVol", "RainbowBloom_Field")
KNOWN_HUSK_LABEL_PREFIXES = ("PetalTemplate_", "RainbowBloom_")
KNOWN_HUSK_ASSETS = ("/Game/EnvSandbox/PCG/House/PCG_RainbowBloom_Test",)
HOUDINI_OVERLAY_LABELS = ("Houdini_RainbowBloom_3900", "HoudiniEngine_RainbowBloom_3900")
LOOKDEV_TAG = "WorldCompiler.lookdev"
DA_BOOKMARK_PATH = "/Game/Melodia/WorldCompiler/DA_MorningRainbowBloom"
COMPILE_CLI_HINT = "python Tools/world_compiler.py compile recipes/<id>.v1.json && python Tools/world_compiler_ue_driver.py Saved/WorldCompiler/<id>_<seed>"
# Load Data Table column -> PCG point-property selector. Shared with the driver (it reads this list back
# from the template_scaffold step record).
MAPPING_TARGETS = (("Position", "$Position"), ("Rotation", "$Rotation"), ("Scale3D", "$Scale"))


# ----------------------------------------------------------------------------- io

def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_bundle(bundle_dir: Path) -> dict:
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    dressing = json.loads((bundle_dir / "dressing_table.json").read_text(encoding="utf-8"))
    return {"manifest": manifest, "dressing": dressing, "dir": bundle_dir}


def _rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write(bundle_dir: Path, step: str, payload: dict) -> None:
    out = bundle_dir / "ue"
    out.mkdir(parents=True, exist_ok=True)
    payload.setdefault("step", step)
    payload.setdefault("recorded_at_utc", _now())
    (out / f"{step}.json").write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def _actors():
    svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    return svc, list(svc.get_all_level_actors())


def _label(actor) -> str:
    try:
        return actor.get_actor_label()
    except Exception:
        return ""


def _tagged(actors, tag: str):
    out = []
    for a in actors:
        try:
            if a.actor_has_tag(tag):
                out.append(a)
        except Exception:
            pass
    return out


def _vec(row: dict, key_x="x", key_y="y", key_z="z") -> unreal.Vector:
    return unreal.Vector(float(row[key_x]), float(row[key_y]), float(row[key_z]))


# ----------------------------------------------------------------------------- steps

def step_preflight(b: dict) -> dict:
    m = b["manifest"]
    world = ELL.get_editor_world()
    level_path = world.get_path_name().split(".")[0] if world else None
    ue = m["ue_lane"]
    checks = {
        "level_open_matches_recipe": level_path == m["place"]["level"],
        "level_open": level_path,
        "template_graph_exists": AL.does_asset_exist(ue["pcg_template_graph"]),
        "row_struct_exists": AL.does_asset_exist(ue.get("row_struct", "")),
        "data_table_exists": AL.does_asset_exist(ue["data_table"]),
        "parent_master_exists": AL.does_asset_exist(b["dressing"]["parent_master"]),
        "species_mesh_exists": {s["species_id"]: AL.does_asset_exist(s["mesh"]) for s in b["dressing"]["species"]},
        "band_mi_exists": {r["label"]: AL.does_asset_exist(r["material_instance"]) for r in b["dressing"]["bands"]},
        "husks_present": [],
        "tagged_actors_present": 0,
    }
    _, actors = _actors()
    for a in actors:
        lbl = _label(a)
        if lbl in KNOWN_HUSK_LABELS or lbl.startswith(KNOWN_HUSK_LABEL_PREFIXES):
            checks["husks_present"].append(lbl)
    checks["tagged_actors_present"] = len(_tagged(actors, ue["actor_tag"]))
    checks["husk_assets_present"] = [p for p in KNOWN_HUSK_ASSETS if AL.does_asset_exist(p)]
    checks["ok_to_proceed"] = bool(checks["level_open_matches_recipe"] and checks["parent_master_exists"] and all(checks["species_mesh_exists"].values()))
    checks["blocked_on_template"] = not checks["template_graph_exists"]
    return checks


def step_cleanup(b: dict) -> dict:
    ue = b["manifest"]["ue_lane"]
    svc, actors = _actors()
    destroyed = []
    for a in actors:
        lbl = _label(a)
        is_husk = lbl in KNOWN_HUSK_LABELS or lbl.startswith(KNOWN_HUSK_LABEL_PREFIXES)
        try:
            is_tagged = a.actor_has_tag(ue["actor_tag"])
        except Exception:
            is_tagged = False
        if is_husk or is_tagged:
            if svc.destroy_actor(a):
                destroyed.append(lbl)
    deleted_assets = []
    for p in KNOWN_HUSK_ASSETS:
        if AL.does_asset_exist(p):
            if AL.delete_asset(p):
                deleted_assets.append(p)
    return {"destroyed_actors": destroyed, "deleted_assets": deleted_assets}


def step_materials(b: dict) -> dict:
    d = b["dressing"]
    if d.get("active_lane") == "wind" and d.get("wind_lane"):
        return {"parent": (d.get("wind_lane") or {}).get("parent"), "band_mis": [], "active_lane": "wind",
                "wind_lane": _forge_wind_lane(d["wind_lane"]), "skipped_static_kit": True}
    parent = AL.load_asset(d["parent_master"])
    if not parent:
        return {"error": f"parent master missing: {d['parent_master']}"}
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tint_param = d.get("tint_parameter", "BaseTint")
    results = []
    for band in d["bands"]:
        path = band["material_instance"]
        folder, name = path.rsplit("/", 1)
        rec = {"band": band["band"], "mi": path}
        try:
            if AL.does_asset_exist(path):
                rec["existed"] = True
                mi = AL.load_asset(path)
            else:
                if not AL.does_directory_exist(folder):
                    AL.make_directory(folder)
                mi = tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                rec["created"] = True
            current_parent = mi.get_editor_property("parent")
            if not current_parent or current_parent.get_path_name().split(".")[0] != d["parent_master"]:
                mi.set_editor_property("parent", parent)
                rec["parent_set"] = True
            r, g, bl = band["tint"]
            MEL.set_material_instance_vector_parameter_value(mi, tint_param, unreal.LinearColor(r, g, bl, 1.0))
            rec["tint"] = [r, g, bl]
            for tex_param, tex_path in GHOSTLOTUS_TEXTURES:
                tex = AL.load_asset(tex_path)
                if tex:
                    MEL.set_material_instance_texture_parameter_value(mi, tex_param, tex)
            MEL.update_material_instance(mi)
            rec["saved"] = AL.save_asset(path, only_if_is_dirty=True)
        except Exception as exc:
            rec["error"] = str(exc)[:300]
        results.append(rec)
    # Species may declare distinct band_mi_prefix families (e.g. GlassgardenCoral +
    # GlassgardenKelp). Forge any MI path that points.csv references but dressing.bands missed.
    seen = {r["mi"] for r in results}
    extra = []
    points = b["dir"] / "points.csv"
    if points.is_file():
        for row in _rows(points):
            path = (row.get("material") or "").strip().split(".")[0]
            if not path or path in seen:
                continue
            seen.add(path)
            folder, name = path.rsplit("/", 1)
            # Prefer band tint from dressing.bands when band index matches.
            try:
                band_i = int(row.get("band", 0))
            except Exception:
                band_i = 0
            tint = next((bd["tint"] for bd in d["bands"] if int(bd["band"]) == band_i), None)
            if tint is None and d["bands"]:
                tint = d["bands"][0]["tint"]
            if tint is None:
                tint = [1.0, 1.0, 1.0]
            rec = {"band": band_i, "mi": path, "from_points": True}
            try:
                if AL.does_asset_exist(path):
                    rec["existed"] = True
                    mi = AL.load_asset(path)
                else:
                    if not AL.does_directory_exist(folder):
                        AL.make_directory(folder)
                    mi = tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                    rec["created"] = True
                current_parent = mi.get_editor_property("parent")
                if not current_parent or current_parent.get_path_name().split(".")[0] != d["parent_master"]:
                    mi.set_editor_property("parent", parent)
                    rec["parent_set"] = True
                r, g, bl = tint
                MEL.set_material_instance_vector_parameter_value(mi, tint_param, unreal.LinearColor(r, g, bl, 1.0))
                rec["tint"] = [r, g, bl]
                MEL.update_material_instance(mi)
                rec["saved"] = AL.save_asset(path, only_if_is_dirty=True)
            except Exception as exc:
                rec["error"] = str(exc)[:300]
            extra.append(rec)
            results.append(rec)
    out = {"parent": d["parent_master"], "band_mis": results, "active_lane": d.get("active_lane", "static"),
           "extra_from_points": len(extra)}
    if d.get("wind_lane"):
        out["wind_lane"] = _forge_wind_lane(d["wind_lane"])
    return out


def _forge_wind_lane(w: dict) -> dict:
    """Forge the wind hue-reveal band family under a parent that already binds MF_MelodiaWindHueReveal.

    The compiler never edits the parent (the MF call, the palette Wind* collection reads and the
    Substrate Toon BSDF all live there); it only sets per-band tint / hue seed / response, switches
    off SpeedTree wind branches that need vertex data the flower kit lacks, and swaps textures.
    """
    parent = AL.load_asset(w["parent"])
    if not parent:
        return {"error": f"wind parent missing: {w['parent']}"}
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for band in w["bands"]:
        path = band["material_instance"]
        folder, name = path.rsplit("/", 1)
        rec = {"band": band["band"], "mi": path}
        try:
            if AL.does_asset_exist(path):
                mi = AL.load_asset(path)
                rec["existed"] = True
            else:
                if not AL.does_directory_exist(folder):
                    AL.make_directory(folder)
                mi = tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                rec["created"] = True
            cur = mi.get_editor_property("parent")
            if not cur or cur.get_path_name().split(".")[0] != w["parent"]:
                mi.set_editor_property("parent", parent)
            r, g, bl = band["tint"]
            MEL.set_material_instance_vector_parameter_value(mi, w["tint_parameter"], unreal.LinearColor(r, g, bl, 1.0))
            MEL.set_material_instance_scalar_parameter_value(mi, w["hue_seed_parameter"], float(band["hue_seed"]))
            # Lookdev-legal ceiling: never raise above 0.5 (recipe may already be 0.5).
            MEL.set_material_instance_scalar_parameter_value(mi, w["response_parameter"], min(0.5, float(w["response"])))
            for k, v in (w.get("scalar_overrides") or {}).items():
                MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
            for sw in w.get("static_switches_off") or []:
                MEL.set_material_instance_static_switch_parameter_value(mi, sw, False)
            for k, tex_path in (w.get("texture_overrides") or {}).items():
                tex = AL.load_asset(tex_path)
                if tex:
                    MEL.set_material_instance_texture_parameter_value(mi, k, tex)
                else:
                    rec.setdefault("missing_textures", []).append(tex_path)
            MEL.update_material_instance(mi)
            rec["saved"] = AL.save_asset(path, only_if_is_dirty=True)
        except Exception as exc:
            rec["error"] = str(exc)[:300]
        made.append(rec)
    return {"parent": w["parent"], "band_mis": made,
            "binds": {"material_function": "MF_MelodiaWindHueReveal (called by the parent)",
                      "reads": ["MPC_Melodia_Palette.WindDirX", "MPC_Melodia_Palette.WindDirY", "MPC_Melodia_Palette.WindStrength"]}}


def step_table(b: dict) -> dict:
    m = b["manifest"]
    ue = m["ue_lane"]
    dt_path = ue["data_table"]
    struct_path = ue.get("row_struct", "")
    if not AL.does_asset_exist(struct_path):
        return {"error": f"row struct missing: {struct_path}; create via Monolith blueprint.create_user_defined_struct", "blocked": True}
    rows = _rows(b["dir"] / "points.csv")
    if not rows:
        return {"error": "points.csv empty"}
    columns = list(rows[0].keys())
    # DataTable CSV import uses the first column as the row name.
    lines = [",".join(["---"] + columns)]
    for r in rows:
        lines.append(",".join([f"p{r['point_id']}"] + [_csv_escape(r[c]) for c in columns]))
    csv_text = "\n".join(lines) + "\n"
    dt = AL.load_asset(dt_path) if AL.does_asset_exist(dt_path) else None
    created = False
    if dt is None:
        folder, name = dt_path.rsplit("/", 1)
        if not AL.does_directory_exist(folder):
            AL.make_directory(folder)
        factory = unreal.DataTableFactory()
        factory.set_editor_property("struct", AL.load_asset(struct_path))
        dt = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.DataTable, factory)
        created = dt is not None
    if dt is None:
        return {"error": "could not create DataTable", "blocked": True}
    ok = unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(dt, csv_text)
    names = list(unreal.DataTableFunctionLibrary.get_data_table_row_names(dt))
    # Column drift: the CSV importer silently drops columns the row struct does not have (it only
    # logs "Cannot find Property for column"), so read every column back and report the misses.
    missing = []
    for col in columns:
        try:
            vals = list(unreal.DataTableFunctionLibrary.get_data_table_column_as_string(dt, unreal.Name(col)))
        except Exception:
            vals = []
        if len(vals) != len(names):
            missing.append(col)
    saved = AL.save_asset(dt_path, only_if_is_dirty=False)
    return {"data_table": dt_path, "created": created, "fill_ok": bool(ok), "rows_in_csv": len(rows), "rows_in_table": len(names),
            "columns": columns, "missing_columns": missing, "saved": saved,
            "match": len(names) == len(rows) and not missing,
            "struct_drift": bool(missing)}


def _csv_escape(value: str) -> str:
    if any(ch in value for ch in (",", '"', "\n")):
        return '"' + value.replace('"', '""') + '"'
    return value


def _volume_pose(m: dict) -> tuple:
    ax, ay, az = m["place"]["anchor_cm"]
    walk = (m.get("terrain") or {}).get("walkable_z_cm") or [az - 400.0, az + 400.0]
    z_lo, z_hi = float(walk[0]), float(walk[1])
    _, actors = _actors()
    islands = [a for a in actors if _label(a).startswith("BrushifyIsland_")]
    if islands:
        xs, ys, zs = [], [], []
        for a in islands:
            o, b = a.get_actor_bounds(False)
            xs += [o.x - b.x, o.x + b.x]
            ys += [o.y - b.y, o.y + b.y]
            zs += [o.z - b.z, o.z + b.z]
        cx, cy, cz = 0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)), 0.5 * (min(zs) + max(zs))
        ex = max(400.0, 0.5 * (max(xs) - min(xs)) + 150.0)
        ey = max(400.0, 0.5 * (max(ys) - min(ys)) + 150.0)
        ez = max(600.0, 0.5 * (max(zs) - min(zs)) + 200.0)
        return unreal.Vector(cx, cy, cz), unreal.Vector(ex / 100.0, ey / 100.0, ez / 100.0), z_lo, z_hi
    outer = float(m["place"]["outer_radius_cm"])
    half = outer + 200.0
    scale_xy = (half * 2.0) / 200.0
    z_mid = 0.5 * (z_lo + z_hi)
    height = max(1200.0, (z_hi - z_lo) + 900.0)
    scale_z = height / 200.0
    return unreal.Vector(ax, ay, z_mid), unreal.Vector(scale_xy, scale_xy, scale_z), z_lo, z_hi


def step_volume(b: dict) -> dict:
    m = b["manifest"]
    ue = m["ue_lane"]
    if not AL.does_asset_exist(ue["pcg_template_graph"]):
        return {"error": f"template graph missing: {ue['pcg_template_graph']} (owner wires it once in the editor)", "blocked": True}
    graph = AL.load_asset(ue["pcg_template_graph"])
    loc, scale, z_lo, z_hi = _volume_pose(m)
    vol = ELL.spawn_actor_from_class(unreal.PCGVolume, loc, unreal.Rotator(0, 0, 0))
    if vol is None:
        return {"error": "spawn PCGVolume failed"}
    vol.set_actor_label(ue["pcg_volume_label"])
    vol.set_actor_location(loc, False, False)
    vol.set_actor_scale3d(scale)
    tags = list(vol.get_editor_property("tags"))
    tags.append(unreal.Name(ue["actor_tag"]))
    vol.set_editor_property("tags", tags)
    comp = vol.get_component_by_class(unreal.PCGComponent)
    comp.set_graph(graph)
    try:
        comp.set_editor_property("generation_trigger", unreal.PCGComponentGenerationTrigger.GENERATE_ON_DEMAND)
    except Exception:
        pass
    try:
        comp.set_editor_property("seed", int(m["identity"]["chunk_stable_seed"]) & 0x7FFFFFFF)
    except Exception:
        pass
    return {"volume": ue["pcg_volume_label"], "location": [loc.x, loc.y, loc.z], "scale": [scale.x, scale.y, scale.z],
            "walkable_z_cm": [z_lo, z_hi], "graph": graph.get_path_name(), "tag": ue["actor_tag"]}


def _find_volume(b: dict):
    ue = b["manifest"]["ue_lane"]
    _, actors = _actors()
    for a in actors:
        if _label(a) == ue["pcg_volume_label"]:
            return a
    tagged = [a for a in _tagged(actors, ue["actor_tag"]) if a.get_class().get_name() == "PCGVolume"]
    return tagged[0] if tagged else None


def step_generate(b: dict) -> dict:
    vol = _find_volume(b)
    if vol is None:
        return {"error": "volume not found; run 'volume' first"}
    comp = vol.get_component_by_class(unreal.PCGComponent)
    # PCG caches Load Data Table output keyed on the asset, not its rows: after refilling the DataTable
    # the graph would re-spawn the previous compile's points. Flush before every generate.
    flushed = False
    try:
        unreal.SystemLibrary.execute_console_command(ELL.get_editor_world(), "pcg.FlushCache")
        flushed = True
    except Exception:
        pass
    loc, scale, _, _ = _volume_pose(b["manifest"])
    vol.set_actor_location(loc, False, False)
    vol.set_actor_scale3d(scale)
    comp.generate(True)
    # PCG generate can snap the volume onto a sibling dressing box; pin the island field pose.
    vol.set_actor_location(loc, False, False)
    vol.set_actor_scale3d(scale)
    live = vol.get_actor_location()
    live_s = vol.get_actor_scale3d()
    return {"volume": _label(vol), "generate_requested": True, "cache_flushed": flushed,
            "location": [live.x, live.y, live.z], "scale": [live_s.x, live_s.y, live_s.z]}


def step_count(b: dict) -> dict:
    vol = _find_volume(b)
    if vol is None:
        return {"error": "volume not found"}
    comp = vol.get_component_by_class(unreal.PCGComponent)
    generated = bool(comp.get_editor_property("generated"))
    m = b["manifest"]
    band_by_mi = {r["material_instance"].split("/")[-1]: r["band"] for r in b["dressing"]["bands"]}
    for r in (b["dressing"].get("wind_lane") or {}).get("bands", []):
        band_by_mi[r["material_instance"].split("/")[-1]] = r["band"]
    rows = _rows(b["dir"] / "points.csv")
    # The flower kit has one band MI per mesh variant. Include suffixes such as
    # _Tall from the compiled rows so the count covers the entire flower field.
    for r in rows:
        mat = (r.get("material") or "").strip()
        if not mat:
            continue
        mi_name = mat.split(".")[0].split("/")[-1]
        # Flower kit + dressing families (GlassgardenCoral/Kelp, glitter, etc.)
        band_by_mi[mi_name] = int(r["band"])
    flower_per_band: dict[str, int] = {}
    dressing_by_mi: dict[str, int] = {}
    comps = 0
    total = 0
    flower_total = 0
    dressing_total = 0
    _, actors = _actors()
    candidates = [vol] + [a for a in actors if a.get_class().get_name() in ("PCGPartitionActor",)]
    for a in candidates:
        for c in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
            mesh = c.get_editor_property("static_mesh")
            if not mesh:
                continue
            n = c.get_instance_count()
            if n == 0:
                continue
            # Petal slot is 1 on the flower kit; stem slot 0 is often a band MI too (stem_material __band__).
            slot_names = [c.get_material(i).get_name() if c.get_material(i) else "none" for i in range(c.get_num_materials())]
            flower_slot = next((s for s in slot_names if s in band_by_mi), None)
            comps += 1
            total += n
            if flower_slot is not None:
                band = str(band_by_mi[flower_slot])
                flower_per_band[band] = flower_per_band.get(band, 0) + n
                flower_total += n
            else:
                key = slot_names[0] if slot_names else "none"
                dressing_by_mi[key] = dressing_by_mi.get(key, 0) + n
                dressing_total += n
    expected_flowers = {}
    expected_dressing = 0
    for r in rows:
        mat = (r.get("material") or "").strip()
        if "MI_RainbowSpeedTree_" in mat:
            expected_flowers[str(r["band"])] = expected_flowers.get(str(r["band"]), 0) + 1
        else:
            expected_dressing += 1
    tolerance = 0.95 if (m.get("terrain") or {}).get("kind") == "ground_probe" else 1.0
    expected_total = m["counts"]["points_total"]
    if expected_flowers:
        expected_per_band = expected_flowers
        flower_ok = {
            k: flower_per_band.get(k, 0) >= int(v * tolerance)
            for k, v in expected_per_band.items()
        }
        match = bool(expected_per_band) and all(flower_ok.values())
    else:
        # Dressing-only recipes (Glassgarden etc.): band MIs are matched via band_by_mi
        # and counted in flower_per_band (historical flower-kit field name).
        expected_per_band = {}
        for r in rows:
            expected_per_band[str(r["band"])] = expected_per_band.get(str(r["band"]), 0) + 1
        flower_ok = {
            k: flower_per_band.get(k, 0) >= int(v * tolerance)
            for k, v in expected_per_band.items()
        }
        match = (
            bool(expected_per_band)
            and all(flower_ok.values())
            and total >= int(expected_total * tolerance)
        )
    return {
        "generated": generated, "ism_components": comps, "instances_total": total,
        "per_band": flower_per_band, "expected_per_band": expected_per_band,
        "dressing_by_mi": dressing_by_mi, "dressing_instances": dressing_total,
        "expected_dressing": expected_dressing, "flower_instances": flower_total,
        "expected_total": expected_total,
        "tolerance": tolerance, "per_band_ok": flower_ok,
        "match": match,
    }


def step_probe_ground(b: dict) -> dict:
    """Line-trace a grid over the field footprint and write the ground probe the compiler's terrain stage reads.

    Output: recipe.terrain.probe (tracked under recipes/ground/). Cells record hit z + actor label/class, or null
    where nothing blocks (water bodies here have no collision, so the pond reads as void). Deterministic for a
    given level state; re-run after moving hero props.
    """
    m = b["manifest"]
    terrain = m.get("terrain") or {}
    rel = terrain.get("probe") or f"recipes/ground/{m['recipe_id']}_ground_probe.json"
    ax, ay, az = m["place"]["anchor_cm"]
    radius = float(terrain.get("probe_radius_cm") or (m["place"]["outer_radius_cm"] + 400.0))
    step = float(terrain.get("probe_step_cm") or 100.0)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    n = int(2 * radius / step) + 1
    rows = []
    classes: dict[str, int] = {}
    for i in range(n):
        x = ax - radius + i * step
        for j in range(n):
            y = ay - radius + j * step
            hit = unreal.SystemLibrary.line_trace_single(
                world, unreal.Vector(x, y, az + 4000.0), unreal.Vector(x, y, az - 2500.0),
                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True,
                unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
            t = hit.to_tuple() if hit else None
            if t and t[0]:
                actor = t[9]
                label = actor.get_actor_label() if actor else None
                cls = actor.get_class().get_name() if actor else None
                classes[cls] = classes.get(cls, 0) + 1
                # Record z for BrushifyIsland_* crowns and WC_EscherWalk_* decks.
                # Bedroom boards, Sphere3D stand-ins, and WC_DellFloor are never plantable.
                # Species allowlists in GroundMask decide who may use walk vs island hits.
                lab = (label or "")
                never = (
                    lab.startswith("WC_DellFloor")
                    or "classic_arch" in lab.lower()
                    or "Sphere3D" in lab
                    or lab.startswith("SM_PM3D")
                )
                record = lab.startswith("BrushifyIsland_") or lab.startswith("WC_EscherWalk_")
                if never or not record:
                    rows.append([round(x, 1), round(y, 1), None, label, cls])
                else:
                    rows.append([round(x, 1), round(y, 1), round(t[4].z, 1), label, cls])
            else:
                rows.append([round(x, 1), round(y, 1), None, None, None])
    out = {"schema": "melodia.world_compiler_ground_probe.v1", "level": m["place"]["level"],
           "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "center_cm": [ax, ay], "radius_cm": radius,
           "step_cm": step, "columns": ["x", "y", "z", "actor_label", "actor_class"], "classes": classes, "rows": rows}
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    hits = sum(1 for r in rows if r[2] is not None)
    return {"probe": rel, "cells": len(rows), "hits": hits, "classes": classes}


def step_reset_table(b: dict) -> dict:
    """Delete DT + row struct so the driver can recreate them after a column-contract change."""
    ue = b["manifest"]["ue_lane"]
    out = {}
    for key in ("data_table", "row_struct"):
        p = ue.get(key, "")
        if p and AL.does_asset_exist(p):
            out[key] = AL.delete_asset(p)
    return out


def _node_settings(node):
    try:
        return node.get_settings()
    except Exception:
        return node.get_editor_property("settings_interface")


def step_template_scaffold(b: dict) -> dict:
    """Create PCG_WorldCompiler_PointField with configured nodes, then TRY the two edges and VERIFY them.

    Edges are the one thing the 09-15 scratch scripts could not trust (add_edge into Output
    silently no-op'd). Every edge attempted here is checked against graph.get_all_edges();
    anything unverified is reported for the owner to wire by hand. Nodes/settings are safe.
    """
    m = b["manifest"]
    ue = m["ue_lane"]
    graph_path = ue["pcg_template_graph"]
    rec: dict = {"graph": graph_path}
    if AL.does_asset_exist(graph_path):
        rec["existed"] = True
        graph = AL.load_asset(graph_path)
    else:
        folder, name = graph_path.rsplit("/", 1)
        if not AL.does_directory_exist(folder):
            AL.make_directory(folder)
        graph = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.PCGGraph, unreal.PCGGraphFactory())
        rec["created"] = graph is not None
    if graph is None:
        return {"error": "could not create PCGGraph"}
    existing = {str(n.get_path_name()).split(":")[-1]: n for n in graph.get_editor_property("nodes")}
    rec["existing_nodes"] = sorted(existing)

    # --- Load Data Table node
    load_node = next((n for k, n in existing.items() if "LoadDataTable" in k), None)
    if load_node is None:
        load_node = graph.add_node_of_type(unreal.PCGLoadDataTableSettings)[0]
        rec["load_node_created"] = True
    ls = _node_settings(load_node)
    dt = AL.load_asset(ue["data_table"])
    notes = []
    try:
        ls.set_editor_property("data_table", dt)
        notes.append("data_table set")
    except Exception as exc:
        notes.append(f"data_table ERR {str(exc)[:120]}")
    # Attribute mapping Position/Rotation/Scale3D -> $Position/$Rotation/$Scale.
    # Python can only create the map KEYS: FPCGAttributePropertyInputSelector's members are protected and
    # the blueprint helpers (set_point_property / import_text) mutate a by-value copy, so every selector
    # stays "@Last". The driver finishes the job through Monolith blueprint.set_property_at_path
    # (C++ ImportText) using rec["load_settings_path"]; MAPPING_TARGETS is the shared truth.
    try:
        mapping = ls.get_editor_property("attribute_mapping")
        rec["attribute_mapping_type"] = type(mapping).__name__
        new_map = {src: unreal.PCGAttributePropertyInputSelector() for src, _dst in MAPPING_TARGETS}
        ls.set_editor_property("attribute_mapping", new_map)
        readback = ls.get_editor_property("attribute_mapping")
        rec["attribute_mapping_keys"] = sorted(str(k) for k in dict(readback).keys()) if readback is not None else None
        rec["attribute_mapping_values"] = {str(k): str(v.export_text()) for k, v in dict(readback).items()}
        rec["load_settings_path"] = str(ls.get_path_name())
        rec["mapping_targets"] = [{"column": s, "selector": d, "import_text": f"PCGBegin({d})PCGEnd"} for s, d in MAPPING_TARGETS]
        notes.append("attribute_mapping keys set (selectors written by driver via Monolith set_property_at_path)")
    except Exception as exc:
        notes.append(f"attribute_mapping ERR {str(exc)[:160]} (owner maps Position/Rotation/Scale3D by hand)")
    rec["load_notes"] = notes

    # --- Static Mesh Spawner node
    spawner = next((n for k, n in existing.items() if "StaticMeshSpawner" in k), None)
    if spawner is None:
        spawner = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)[0]
        rec["spawner_created"] = True
    ss = _node_settings(spawner)
    snotes = []
    try:
        ss.set_mesh_selector_type(unreal.PCGMeshSelectorByAttribute)
        sel = ss.get_editor_property("mesh_selector_parameters")
        sel.set_editor_property("attribute_name", unreal.Name("mesh"))
        snotes.append("mesh selector = ByAttribute(mesh)")
        try:
            override_attrs = list(ue.get("material_override_attributes") or ["material"])
            sel.set_editor_property("use_attribute_material_overrides", True)
            sel.set_editor_property("material_override_attributes", [unreal.Name(a) for a in override_attrs])
            snotes.append(f"material override = ByAttribute({override_attrs}) (index == material slot)")
        except Exception as exc:
            snotes.append(f"material override ERR {str(exc)[:120]}")
    except Exception as exc:
        snotes.append(f"mesh selector ERR {str(exc)[:140]}")
    try:
        ss.set_instance_packer_type(unreal.PCGInstanceDataPackerByAttribute)
        packer = ss.get_editor_property("instance_data_packer_parameters")
        packer.set_editor_property("attribute_names", [unreal.Name(n) for n in b["dressing"]["packer_attributes"]])
        snotes.append(f"packer = ByAttribute{b['dressing']['packer_attributes']}")
    except Exception as exc:
        snotes.append(f"packer ERR {str(exc)[:140]}")
    for prop, val in (("apply_mesh_bounds_to_points", False),):
        try:
            ss.set_editor_property(prop, val)
        except Exception:
            pass
    rec["spawner_notes"] = snotes

    # --- Ground projection: Get World Ray Hit (surface) + Projection (positions only).
    # The compiler has no heightfield offline (recipe.terrain is null for Morning), so the table's z is the
    # anchor plane; PCG drops every point onto whatever the world actually has there (rocks, deck, soil)
    # and discards points that project onto nothing (keep_zero_density_points = False).
    rayhit = next((n for k, n in existing.items() if "WorldRayHit" in k), None)
    if rayhit is None:
        rayhit = graph.add_node_of_type(unreal.PCGWorldRayHitSettings)[0]
        rec["rayhit_created"] = True
    pnotes = []
    try:
        qp = _node_settings(rayhit).get_editor_property("query_params")
        for prop, val in (("ignore_pcg_hits", True), ("ignore_self_hits", True), ("trace_complex", False)):
            qp.set_editor_property(prop, val)
        _node_settings(rayhit).set_editor_property("query_params", qp)
        pnotes.append("rayhit: ignore_pcg_hits, ignore_self_hits")
    except Exception as exc:
        pnotes.append(f"rayhit params ERR {str(exc)[:120]}")
    projection = next((n for k, n in existing.items() if "Projection" in k and "Spawner" not in k), None)
    if projection is None:
        projection = graph.add_node_of_type(unreal.PCGProjectionSettings)[0]
        rec["projection_created"] = True
    try:
        ps = _node_settings(projection)
        pp = ps.get_editor_property("projection_params")
        for prop, val in (("project_positions", True), ("project_rotations", False), ("project_scales", False)):
            pp.set_editor_property(prop, val)
        ps.set_editor_property("projection_params", pp)
        ps.set_editor_property("keep_zero_density_points", False)
        pnotes.append("projection: positions only, drop misses")
    except Exception as exc:
        pnotes.append(f"projection params ERR {str(exc)[:120]}")
    rec["projection_notes"] = pnotes

    # --- edges: declarative, attempt + verify
    # ROOT CAUSE of the 09-15 "silent no-op": the graph Output node's INPUT pin is labelled
    # "Out" (it mirrors the graph's output pin), not "In". add_edge(..., out_node, "In")
    # returns True and creates nothing. Read the real label instead of guessing.
    out_node = graph.get_output_node()
    def _pin_labels(node, prop):
        try:
            return [str(p.get_editor_property("properties").get_editor_property("label")) for p in node.get_editor_property(prop)]
        except Exception:
            return []
    def _pin(node, prop, label):
        for pin in node.get_editor_property(prop):
            if str(pin.get_editor_property("properties").get_editor_property("label")) == label:
                return pin
        return None
    def _pin_edge_count(node, prop, label):
        pin = _pin(node, prop, label)
        if pin is None:
            return None
        return len(list(pin.get_editor_property("edges")))
    out_in_label = (_pin_labels(out_node, "input_pins") or ["Out"])[0]
    proj_target_label = next((l for l in _pin_labels(projection, "input_pins") if "Target" in l), "Projection Target")
    edges_wanted = [
        (load_node, "Out", projection, "In", "LoadDataTable.Out -> Projection.In"),
        (rayhit, "Out", projection, proj_target_label, f"WorldRayHit.Out -> Projection.{proj_target_label}"),
        (projection, "Out", spawner, "In", "Projection.Out -> Spawner.In"),
        (spawner, "Out", out_node, out_in_label, f"Spawner.Out -> Output.{out_in_label}"),
    ]
    # remove the pre-projection edge if an earlier scaffold left it (Load -> Spawner directly)
    stale = []
    try:
        if graph.remove_edge(load_node, "Out", spawner, "In"):
            stale.append("LoadDataTable.Out -> Spawner.In")
    except Exception:
        pass
    rec["stale_edges_removed"] = stale
    edge_report = []
    for src, sp, dst, dp, label in edges_wanted:
        before = _pin_edge_count(dst, "input_pins", dp)
        if before:
            edge_report.append({"edge": label, "already_present": True})
            continue
        ok = None
        try:
            ok = bool(graph.add_edge(src, sp, dst, dp))
        except Exception as exc:
            ok = f"ERR {str(exc)[:120]}"
        edge_report.append({"edge": label, "add_edge_returned": ok, "verified_edges_after": _pin_edge_count(dst, "input_pins", dp)})
    try:
        verified = [str(e.get_path_name()).split(":")[-1] for e in graph.get_all_edges()]
    except Exception as exc:
        verified = [f"get_all_edges ERR {str(exc)[:120]}"]
    rec["output_input_pin_label"] = out_in_label
    rec["edge_attempts"] = edge_report
    rec["edge_counts"] = {
        "load.out": _pin_edge_count(load_node, "output_pins", "Out"),
        "projection.in": _pin_edge_count(projection, "input_pins", "In"),
        "projection.target": _pin_edge_count(projection, "input_pins", proj_target_label),
        "spawner.in": _pin_edge_count(spawner, "input_pins", "In"),
        "spawner.out": _pin_edge_count(spawner, "output_pins", "Out"),
        "output.in": _pin_edge_count(out_node, "input_pins", out_in_label),
    }
    rec["edges_verified"] = all(bool(rec["edge_counts"].get(k)) for k in ("projection.in", "projection.target", "spawner.in", "output.in"))
    rec["all_edges"] = verified[:10]
    # tidy layout: left-to-right, 400 units apart
    try:
        for i, n in enumerate((load_node, rayhit, projection, spawner, out_node)):
            n.set_editor_property("position_x", i * 400)
            n.set_editor_property("position_y", 300 if n is rayhit else 0)
    except Exception:
        pass
    rec["saved"] = AL.save_asset(graph_path, only_if_is_dirty=False)
    rec["owner_todo"] = [] if rec["edges_verified"] else ["wire the unverified edge(s) in the PCG editor, then re-run the driver"]
    if not any("attribute_mapping set" in n for n in notes):
        rec["owner_todo"].append("Load Data Table: map Position->$Position, Rotation->$Rotation, Scale3D->$Scale")
    return rec


def step_save(b: dict) -> dict:
    m = b["manifest"]
    world = ELL.get_editor_world()
    saved_level = unreal.EditorLoadingAndSavingUtils.save_map(world, m["place"]["level"]) if world else False
    folder = m["ue_lane"]["data_table"].rsplit("/", 1)[0]
    saved_assets = AL.save_directory(folder, only_if_is_dirty=True, recursive=True)
    return {"level_saved": bool(saved_level), "world_compiler_folder_saved": bool(saved_assets), "folder": folder}


# ----------------------------------------------------------------------------- fx

def _fx_pack(b: dict) -> dict | None:
    rel = b["manifest"]["ue_lane"].get("fx_pack")
    if not rel:
        return None
    p = ROOT / rel
    return json.loads(p.read_text(encoding="utf-8-sig")) if p.exists() else None


# CSV column stays spawn_multiplier; instance override uses pack User.* names.
_FX_SPAWN_USER_BY_KIND = {
    "petal": "PetalSpawnMultiplier",
    "pollen": "MoteSpawnMultiplier",
    "mist": "MistDensity",
    "windfront": "WindFrontVisible",
    "wind": "WindFrontVisible",
    "dust": "MoteSpawnMultiplier",
    "dustshafts": "MoteSpawnMultiplier",
}
_FX_SPAWN_USER_BY_SYSTEM = {
    "NS_Morning_PetalDrift": "PetalSpawnMultiplier",
    "NS_Morning_PollenSparkle": "MoteSpawnMultiplier",
    "NS_Morning_PondMist": "MistDensity",
    "NS_Morning_WindFront": "WindFrontVisible",
    "NS_Morning_DustShafts": "MoteSpawnMultiplier",
}
_FX_SPAWN_USER_PACK_KEYS = (
    "PetalSpawnMultiplier",
    "MoteSpawnMultiplier",
    "MistDensity",
    "WindFrontVisible",
)


def _fx_system_basename(sys_path: str) -> str:
    base = (sys_path or "").rstrip("/").rsplit("/", 1)[-1]
    return base.split(".", 1)[0] if base else ""


def _fx_spawn_user_param(kind: str, sys_path: str, pack: dict | None) -> str | None:
    """Map fx_kind / NS path to the pack User float WC should set on the actor."""
    kind_l = (kind or "").strip().lower()
    if kind_l in _FX_SPAWN_USER_BY_KIND:
        return _FX_SPAWN_USER_BY_KIND[kind_l]
    base = _fx_system_basename(sys_path)
    if base in _FX_SPAWN_USER_BY_SYSTEM:
        return _FX_SPAWN_USER_BY_SYSTEM[base]
    if not pack:
        return None
    rec = None
    for system in pack.get("systems") or []:
        if system.get("id") == kind_l:
            rec = system
            break
        tgt = _fx_system_basename(system.get("target") or "")
        if tgt and tgt == base:
            rec = system
            break
    if not rec:
        return None
    ups = rec.get("user_params") or {}
    for key in _FX_SPAWN_USER_PACK_KEYS:
        if key in ups:
            return key
    return None


def _duplicate_named(src: str, dst: str) -> tuple[object | None, dict]:
    rec = {"src": src, "dst": dst}
    if not src or src.startswith("material_of:"):
        rec["error"] = "unresolved source"
        return None, rec
    if not AL.does_asset_exist(src):
        rec["error"] = f"source missing: {src}"
        return None, rec
    if AL.does_asset_exist(dst):
        rec["existed"] = True
        return AL.load_asset(dst), rec
    folder, _name = dst.rsplit("/", 1)
    if not AL.does_directory_exist(folder):
        AL.make_directory(folder)
    dup = AL.duplicate_asset(src, dst)
    rec["created"] = bool(dup)
    if not dup:
        rec["error"] = "duplicate_asset returned None"
        return None, rec
    return dup, rec


def _material_of_niagara(ns_path: str) -> str | None:
    fallback = "/Game/EnvSandbox/VFX/Materials/MI_Niagara_Sparkle"
    if AL.does_asset_exist(fallback):
        # Prefer a dependency of the named system when Asset Registry can see it.
        try:
            ar = unreal.AssetRegistryHelpers.get_asset_registry()
            opts = unreal.AssetRegistryDependencyOptions()
            for key in ("include_soft_package_references", "include_hard_management_references",
                        "include_direct_soft_references", "include_searchable_names"):
                try:
                    opts.set_editor_property(key, False)
                except Exception:
                    pass
            try:
                opts.set_editor_property("include_soft_package_references", True)
            except Exception:
                pass
            deps = list(ar.get_dependencies(unreal.Name(ns_path), opts) or [])
            for d in deps:
                p = str(d)
                if "/Materials/" in p or "Niagara" in p:
                    if AL.does_asset_exist(p):
                        asset = AL.load_asset(p)
                        if asset and "Material" in asset.get_class().get_name():
                            return p.split(".")[0]
        except Exception:
            pass
        if AL.does_asset_exist(fallback):
            return fallback
    candidates = (
        "/Game/EnvSandbox/VFX/Materials/MI_Niagara_Sparkle",
        "/Game/EnvSandbox/VFX/Materials/M_Niagara_Sparkle",
        "/Game/EnvSandbox/VFX/Materials/M_NiagaraPetal_Loop_Candidate",
    )
    for c in candidates:
        if AL.does_asset_exist(c):
            return c
    return None


def _resolve_mat_src(spec: dict) -> str | None:
    src = spec.get("duplicate_from") or ""
    if src.startswith("material_of:"):
        return _material_of_niagara(src.split(":", 1)[1])
    return src or None


def step_fx_systems(b: dict) -> dict:
    """Duplicate the four named EnvSandbox parents into Melodia children. Never edit the sources."""
    pack = _fx_pack(b)
    if not pack:
        return {"error": "fx pack missing", "blocked": True}
    et_path = pack["rules"]["effect_type"]
    et = AL.load_asset(et_path) if AL.does_asset_exist(et_path) else None
    mats, systems = [], []
    for spec in pack["materials"]:
        src = _resolve_mat_src(spec)
        asset, rec = _duplicate_named(src or "", spec["target"])
        rec["id"] = spec["id"]
        rec["resolved_src"] = src
        mats.append(rec)
    for spec in pack["systems"]:
        src = spec.get("child_of") or ""
        asset, rec = _duplicate_named(src, spec["target"])
        rec["id"] = spec["id"]
        if asset is not None:
            try:
                if et:
                    asset.set_editor_property("effect_type", et)
                    rec["effect_type"] = et_path
            except Exception as exc:
                rec["effect_type_err"] = str(exc)[:160]
            try:
                cm = float(spec.get("fixed_bounds_cm") or pack["rules"]["fixed_bounds_cm"][0])
                half = cm * 0.5
                box = unreal.Box()
                box.min = unreal.Vector(-half, -half, -half)
                box.max = unreal.Vector(half, half, half)
                asset.set_editor_property("fixed_bounds", box)
                rec["fixed_bounds_cm"] = cm
            except Exception as exc:
                rec["bounds_err"] = str(exc)[:160]
            for prop, val in (("cast_shadow", False), ("b_cast_shadows", False), ("cast_shadows", False)):
                try:
                    asset.set_editor_property(prop, val)
                    rec["cast_shadow"] = 0
                    break
                except Exception:
                    pass
            AL.save_asset(spec["target"], only_if_is_dirty=True)
        systems.append(rec)
    return {
        "materials": mats, "systems": systems,
        "forged": all("error" not in r for r in mats + systems),
        "sources_untouched": True,
    }


def step_fx_materials(b: dict) -> dict:
    pack = _fx_pack(b)
    if not pack:
        return {"error": "fx pack missing", "blocked": True}
    mats = {x["id"]: x for x in pack["materials"]}
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    results = []
    bands = b["dressing"]["bands"]
    for system in pack["systems"]:
        parent_path = mats[system["material_id"]]["target"]
        rec = {"system": system["id"], "parent": parent_path}
        if not AL.does_asset_exist(parent_path):
            rec["blocked"] = f"hero parent not created yet (P7 owner step): {parent_path}"
            results.append(rec)
            continue
        parent = AL.load_asset(parent_path)
        targets = []
        if system.get("per_band"):
            for band in bands:
                targets.append((f"{system['material_instance_prefix']}{band['band']}", band["tint"], (band["band"] + 0.5) / len(bands)))
        else:
            targets.append((system["material_instance"], [1.0, 1.0, 1.0], 0.0))
        made = []
        for path, tint, hue in targets:
            folder, name = path.rsplit("/", 1)
            try:
                if not AL.does_asset_exist(path):
                    if not AL.does_directory_exist(folder):
                        AL.make_directory(folder)
                    mi = tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                    mi.set_editor_property("parent", parent)
                else:
                    mi = AL.load_asset(path)
                MEL.set_material_instance_vector_parameter_value(mi, "BandHue", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
                MEL.set_material_instance_scalar_parameter_value(mi, "HueSeed", float(hue))
                MEL.update_material_instance(mi)
                AL.save_asset(path, only_if_is_dirty=True)
                made.append(path)
            except Exception as exc:
                made.append(f"ERR {path}: {str(exc)[:160]}")
        rec["material_instances"] = made
        results.append(rec)
    return {"results": results}


def step_glitter_materials(b: dict) -> dict:
    """Forge the glitter tint family (one MI per band) under the glitter master.

    Lane mirror of _forge_wind_lane for the palette.glitter block: the compiler
    only names MIs and tint values; the parent (layer colors, scalars, switches)
    is never edited and no collection parameter is written.
    """
    lane = (b["dressing"] or {}).get("glitter_lane")
    if not lane:
        return {"skipped": True, "note": "no palette.glitter in recipe"}
    parent_path = lane["parent"]
    parent = AL.load_asset(parent_path)
    if not parent:
        return {"error": f"glitter parent missing: {parent_path}", "blocked": True}
    params = list(lane.get("tint_parameters") or [])
    shades = list(lane.get("shade_steps") or [1.0])
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    made = []
    for band in lane["bands"]:
        path = band["material_instance"]
        folder, name = path.rsplit("/", 1)
        rec = {"band": band["band"], "mi": path}
        try:
            if AL.does_asset_exist(path):
                mi = AL.load_asset(path)
                rec["existed"] = True
            else:
                if not AL.does_directory_exist(folder):
                    AL.make_directory(folder)
                mi = tools.create_asset(name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
                mi.set_editor_property("parent", parent)
                rec["created"] = True
            cur = mi.get_editor_property("parent")
            if not cur or cur.get_path_name().split(".")[0] != parent_path:
                mi.set_editor_property("parent", parent)
                rec["parent_set"] = True
            r, g, bl = (float(band["tint"][0]), float(band["tint"][1]), float(band["tint"][2]))
            set_params = []
            for idx, param in enumerate(params):
                step = float(shades[idx % len(shades)]) if shades else 1.0
                MEL.set_material_instance_vector_parameter_value(
                    mi, param, unreal.LinearColor(min(4.0, r * step), min(4.0, g * step), min(4.0, bl * step), 1.0))
                set_params.append(param)
            rec["tint_params"] = set_params
            for k, v in ((lane.get("scalar_overrides") or {}).items()):
                MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
            rec["scalar_overrides"] = dict(lane.get("scalar_overrides") or {})
            MEL.update_material_instance(mi)
            rec["saved"] = AL.save_asset(path, only_if_is_dirty=True)
        except Exception as exc:
            rec["error"] = str(exc)[:300]
        made.append(rec)
    return {"parent": parent_path, "band_mis": made,
            "all_ok": all("error" not in r for r in made) and len(made) == 7}


def step_fx_place(b: dict) -> dict:
    ue = b["manifest"]["ue_lane"]
    rows = _rows(b["dir"] / "fx_anchors.csv")
    pack = _fx_pack(b)
    svc, actors = _actors()
    removed = 0
    for a in _tagged(actors, ue["actor_tag"]):
        if a.get_class().get_name() == "NiagaraActor":
            if svc.destroy_actor(a):
                removed += 1
    placed, blocked = [], []
    for r in rows:
        sys_path = r["system"]
        if not sys_path or not AL.does_asset_exist(sys_path):
            blocked.append({"anchor": r["anchor_id"], "system_missing": sys_path})
            continue
        system = AL.load_asset(sys_path)
        actor = ELL.spawn_actor_from_class(unreal.NiagaraActor, _vec(r), unreal.Rotator(0, 0, 0))
        kind = r["fx_kind"]
        actor.set_actor_label(f"WC_NS_Morning_{kind}_{r['anchor_id']}")
        tags = list(actor.get_editor_property("tags"))
        tags.append(unreal.Name(ue["actor_tag"]))
        tags.append(unreal.Name(f"WorldCompiler.fx.{kind}"))
        actor.set_editor_property("tags", tags)
        comp = actor.get_component_by_class(unreal.NiagaraComponent)
        if comp is None:
            try:
                comp = actor.get_editor_property("niagara_component")
            except Exception:
                comp = None
        if comp is None:
            blocked.append({"anchor": r["anchor_id"], "error": "no_niagara_component"})
            continue
        comp.set_asset(system)
        for prop in ("cast_shadow", "cast_shadows"):
            try:
                comp.set_editor_property(prop, False)
            except Exception:
                pass
        spawn_param = _fx_spawn_user_param(kind, sys_path, pack)
        try:
            band = int(r["band"])
            if band >= 0:
                tint = b["dressing"]["bands"][band]["tint"]
                comp.set_variable_linear_color("BandHue", unreal.LinearColor(tint[0], tint[1], tint[2], 1.0))
            comp.set_variable_float("HueSeed", float(r["hue_seed"]))
            if spawn_param:
                # Pack User.* identity (PetalSpawnMultiplier / MoteSpawnMultiplier / MistDensity / WindFrontVisible).
                # CSV column remains spawn_multiplier. Never write SpawnMultiplier or an MPC.
                comp.set_variable_float(spawn_param, float(r["spawn_multiplier"]))
        except Exception:
            pass
        placed.append({
            "anchor": r["anchor_id"], "label": actor.get_actor_label(), "system": sys_path,
            "loc": [float(r["x"]), float(r["y"]), float(r["z"])], "cast_shadow": 0,
            "spawn_user_param": spawn_param,
        })
    return {"removed_previous": removed, "placed": placed, "blocked": blocked, "anchors_in_csv": len(rows)}


def _recipe_json(b: dict) -> dict:
    rid = b["manifest"]["recipe_id"]
    path = ROOT / "recipes" / f"{rid}.v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


BEAUTY_HIDE_LABELS = ("FX_Morning_Mist", "FX_Morning_Bed_PollenSparkle")
BEAUTY_HIDE_PREFIXES = ("WC_EscherWalk_", "Houdini_Rainbow", "HoudiniEngine_Rainbow")


def step_hide_houdini_overlays(b: dict) -> dict:
    svc, actors = _actors()
    hidden = []
    missing = list(HOUDINI_OVERLAY_LABELS)
    for a in actors:
        lbl = _label(a)
        hide = (
            lbl in HOUDINI_OVERLAY_LABELS
            or lbl in BEAUTY_HIDE_LABELS
            or lbl.startswith(BEAUTY_HIDE_PREFIXES)
            or ("Houdini" in lbl and "Rainbow" in lbl)
        )
        if hide:
            a.set_is_temporarily_hidden_in_editor(True)
            a.set_actor_hidden_in_game(True)
            hidden.append(lbl)
            if lbl in missing:
                missing.remove(lbl)
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.SystemLibrary.execute_console_command(world, "stat none", None)
        unreal.SystemLibrary.execute_console_command(world, "DisableAllScreenMessages", None)
    except Exception:
        pass
    return {"hidden": hidden, "missing": missing}


def _level_look_at(loc: unreal.Vector, look: unreal.Vector) -> unreal.Rotator:
    """Look-at with roll forced to 0. Straight-down targets gimbal find_look_at_rotation."""
    dx = look.x - loc.x
    dy = look.y - loc.y
    if abs(dx) < 1.0 and abs(dy) < 1.0:
        look = unreal.Vector(look.x + 8.0, look.y + 8.0, look.z)
    rot = unreal.MathLibrary.find_look_at_rotation(loc, look)
    # Positional unreal.Rotator(a,b,c) is (roll, pitch, yaw); set named fields.
    fixed = unreal.Rotator()
    fixed.pitch = rot.pitch
    fixed.yaw = rot.yaw
    fixed.roll = 0.0
    return fixed


def step_lookdev_cameras(b: dict) -> dict:
    hide = step_hide_houdini_overlays(b)
    cameras = (_recipe_json(b).get("lookdev") or {}).get("cameras") or []
    svc, actors = _actors()
    destroyed = []
    for a in list(actors):
        try:
            tagged = a.actor_has_tag(LOOKDEV_TAG)
        except Exception:
            tagged = False
        if tagged or _label(a).startswith("WC_Lookdev_"):
            if svc.destroy_actor(a):
                destroyed.append(_label(a))
    spawned = []
    for cam in cameras:
        loc = unreal.Vector(*cam["loc_cm"])
        look = unreal.Vector(*cam["look_cm"])
        rot = _level_look_at(loc, look)
        actor = svc.spawn_actor_from_class(unreal.CameraActor, loc, rot)
        name = cam["name"]
        actor.set_actor_label(f"WC_Lookdev_{name}")
        actor.tags = [LOOKDEV_TAG]
        try:
            cine = actor.get_cine_camera_component() if hasattr(actor, "get_cine_camera_component") else None
        except Exception:
            cine = None
        cam_comp = actor.camera_component if hasattr(actor, "camera_component") else actor.get_component_by_class(unreal.CameraComponent)
        if cam_comp:
            cam_comp.set_editor_property("field_of_view", float(cam.get("fov", 70)))
        spawned.append({"name": name, "label": f"WC_Lookdev_{name}", "loc_cm": cam["loc_cm"]})
    hide["destroyed_prior"] = destroyed
    hide["spawned"] = spawned
    hide["compile_stays_cli"] = COMPILE_CLI_HINT
    return hide


def step_lookdev_capture(b: dict) -> dict:
    hide = step_hide_houdini_overlays(b)
    cameras = (_recipe_json(b).get("lookdev") or {}).get("cameras") or []
    rid = b["manifest"]["recipe_id"]
    out_dir = ROOT / "Saved" / "Audit" / "Screens"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).date().isoformat()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0, 0, 0, 1), False
    )
    svc, _ = _actors()
    cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0))
    shots = []
    try:
        comp = cap.get_editor_property("capture_component2d")
        comp.set_editor_property("texture_target", rt)
        comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        comp.set_editor_property("capture_every_frame", False)
        for cam in cameras:
            loc = unreal.Vector(*cam["loc_cm"])
            look = unreal.Vector(*cam["look_cm"])
            rot = _level_look_at(loc, look)
            cap.set_actor_location_and_rotation(loc, rot, False, False)
            fov = float(cam.get("fov", 70))
            comp.set_editor_property("fov_angle", fov)
            bias = float(cam.get("exposure_bias") or 0.0)
            try:
                pps = comp.get_editor_property("post_process_settings")
                pps.set_editor_property("override_auto_exposure_bias", bool(bias))
                pps.set_editor_property("auto_exposure_bias", bias)
                try:
                    pps.set_editor_property("override_bloom_method", False)
                    pps.set_editor_property("override_bloom_intensity", False)
                except Exception:
                    pass
                comp.set_editor_property("post_process_settings", pps)
                comp.set_editor_property("post_process_blend_weight", 1.0 if bias else 0.0)
            except Exception:
                pass
            for _ in range(3):
                comp.capture_scene()
            fn = out_dir / f"wc_{rid}_{cam['name']}_{stamp}.png"
            opts = unreal.ImageWriteOptions()
            opts.set_editor_property("format", unreal.DesiredImageFormat.PNG)
            opts.set_editor_property("overwrite_file", True)
            opts.set_editor_property("async_", False)
            unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace("\\", "/"), opts)
            shots.append({"name": cam["name"], "file": str(fn).replace("\\", "/"), "bytes": fn.stat().st_size if fn.exists() else 0})
    finally:
        cap.destroy_actor()
    bookmark = step_bookmark(b)
    return {"hidden_houdini": hide, "shots": shots, "ppv": "frozen stack left in level; capture does not add bloom", "bookmark": bookmark}


def step_bookmark(b: dict) -> dict:
    if not hasattr(unreal, "WorldRecipe"):
        return {"skipped": "UWorldRecipe not reflected (rebuild editor)"}
    m = b["manifest"]
    dest_dir = "/Game/Melodia/WorldCompiler"
    if not AL.does_directory_exist(dest_dir):
        AL.make_directory(dest_dir)
    rid = m["recipe_id"]
    seed = int(m["world_seed"])
    bundle_rel = str(b["dir"].relative_to(ROOT)).replace("\\", "/")
    recipe_rel = f"recipes/{rid}.v1.json"
    asset = None
    if AL.does_asset_exist(DA_BOOKMARK_PATH):
        asset = AL.load_asset(DA_BOOKMARK_PATH)
    else:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.WorldRecipe.static_class())
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "DA_MorningRainbowBloom", dest_dir, unreal.WorldRecipe, factory
        )
    if asset is None:
        return {"error": "failed to create or load DA_MorningRainbowBloom"}
    asset.set_editor_property("recipe_id", rid)
    asset.set_editor_property("world_seed", seed)
    asset.set_editor_property("recipe_rel_path", recipe_rel)
    # LastBundleRelPath / LastProofRelPath are VisibleAnywhere (read-only in editor).
    rec_level_err = None
    level_path = m["place"]["level"]
    try:
        loaded = AL.load_asset(level_path)
        if loaded:
            asset.set_editor_property("level", loaded)
    except Exception as exc:
        rec_level_err = str(exc)[:160]
    AL.save_asset(DA_BOOKMARK_PATH)
    return {
        "asset": DA_BOOKMARK_PATH,
        "recipe_rel_path": recipe_rel,
        "last_bundle_rel_path": bundle_rel,
        "last_paths_readonly": True,
        "level_err": rec_level_err,
    }


def step_ensure_euw(b: dict) -> dict:
    path = "/Game/Melodia/WorldCompiler/EUW_WorldCompiler"
    rec = {"path": path, "compile_stays_cli": COMPILE_CLI_HINT}
    if AL.does_asset_exist(path):
        rec["existed"] = True
        return rec
    dest = "/Game/Melodia/WorldCompiler"
    if not AL.does_directory_exist(dest):
        AL.make_directory(dest)
    factory = unreal.EditorUtilityWidgetBlueprintFactory()
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "EUW_WorldCompiler", dest, unreal.EditorUtilityWidgetBlueprint, factory
    )
    rec["created"] = bool(asset)
    rec["note"] = "Buttons call Content/Python/world_compiler_panel.py apply/cleanup/capture. Compile remains Tools/world_compiler.py + world_compiler_ue_driver.py."
    if asset:
        AL.save_asset(path)
    return rec


def step_fx_audit(b: dict) -> dict:
    pack = _fx_pack(b)
    if not pack:
        return {"error": "fx pack missing"}
    et_path = pack["rules"]["effect_type"]
    lo, hi = pack["rules"]["fixed_bounds_cm"]
    out = []
    for system in pack["systems"]:
        path = system["target"]
        rec = {"system": path, "exists": AL.does_asset_exist(path)}
        if rec["exists"]:
            ns = AL.load_asset(path)
            try:
                et = ns.get_editor_property("effect_type")
                rec["effect_type"] = et.get_path_name().split(".")[0] if et else None
                rec["effect_type_ok"] = rec["effect_type"] == et_path
            except Exception as exc:
                rec["effect_type_err"] = str(exc)[:120]
            try:
                fb = ns.get_editor_property("fixed_bounds")
                ext = fb.get_editor_property("max") - fb.get_editor_property("min")
                rec["fixed_bounds_extent_cm"] = [ext.x, ext.y, ext.z]
                rec["fixed_bounds_ok"] = all(lo <= v <= hi * 2 for v in (ext.x, ext.y, ext.z))
            except Exception as exc:
                rec["fixed_bounds_err"] = str(exc)[:120]
        out.append(rec)
    return {"effect_type_required": et_path, "systems": out, "all_exist": all(r["exists"] for r in out)}


def _soft_asset(path: str):
    return unreal.load_asset(path.split(".")[0]) if path else None


def _add_instance_component(actor, cls, name: str):
    """Add a component to a placed actor instance (add_component_by_class is not exposed)."""
    sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sub.k2_gather_subobject_data_for_instance(actor)
    params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=cls, blueprint_context=None)
    handle, fail = sub.add_new_subobject(params)
    if not fail.is_empty():
        raise RuntimeError(f"add {cls.__name__} to {_label(actor)}: {fail}")
    sub.rename_subobject(handle, unreal.Text(name))
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle))


def _ground_z(world, x: float, y: float, ignore: list) -> float | None:
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, 50000.0), unreal.Vector(x, y, -50000.0),
                                                 unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore,
                                                 unreal.DrawDebugTrace.NONE, True)
    return hit.to_tuple()[4].z if hit else None


GROUND_SNAPPED_CURVE_KINDS = ("phyllotaxis",)  # ground cover; lissajous/catenary keep authored height


def step_structures_place(b: dict) -> dict:
    """Stage the recipe `structures` on one BP_MelodiaPCGControl host: slots -> baked kit meshes,
    decor curves -> one ISM per curve. Layout changes = recompile + rerun (event-driven);
    per-frame motion lives in the kit MIs reading the MPC. The PCG template stays owner-authored."""
    ue = b["manifest"]["ue_lane"]
    st = ue.get("structures")
    if not st:
        return {"skipped": "bundle has no structures"}
    recipe = _recipe_json(b)
    cx, cy, cz = recipe["structures"]["layout"]["center_cm"]
    svc, actors = _actors()
    host_label = f"WC_{b['manifest']['recipe_id']}_Structures"
    removed = [(_label(a), svc.destroy_actor(a))[0] for a in actors if _label(a).startswith(host_label)]
    host_cls = unreal.load_class(None, st["control_actor_class"] + "." + st["control_actor_class"].rsplit("/", 1)[-1] + "_C")
    host = svc.spawn_actor_from_class(host_cls, unreal.Vector(cx, cy, cz))
    host.set_actor_label(host_label)
    host.set_folder_path("WorldCompiler/Structures")
    host.tags = [unreal.Name(ue["actor_tag"]), unreal.Name("WorldCompiler.Structures")]

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    spawned = [host]
    placed_slots = []
    for row in _rows(b["dir"] / "structure_slots.csv"):
        gz = _ground_z(world, float(row["x"]), float(row["y"]), spawned)
        if gz is not None:
            row["z"] = str(gz)
        mesh = _soft_asset(row["mesh"])
        if mesh is None:
            placed_slots.append({"slot_uid": row["slot_uid"], "error": f"missing mesh {row['mesh']}"})
            continue
        a = svc.spawn_actor_from_object(mesh, _vec(row), unreal.Rotator(0.0, 0.0, float(row["yaw"])))
        spawned.append(a)
        a.set_actor_label(f"{host_label}_{row['slot_uid']}_{row['slot_id']}")
        a.set_folder_path("WorldCompiler/Structures")
        a.tags = [unreal.Name(ue["actor_tag"]), unreal.Name("WorldCompiler.Structures")]
        if row["material"]:
            a.static_mesh_component.set_material(0, _soft_asset(row["material"]))
        a.attach_to_actor(host, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
        placed_slots.append({"slot_uid": row["slot_uid"], "label": _label(a)})

    curves: dict[str, list[dict]] = {}
    for row in _rows(b["dir"] / "structure_curves.csv"):
        curves.setdefault(row["curve_id"], []).append(row)
    placed_curves = {}
    for cid, rows in curves.items():
        mesh = _soft_asset(rows[0]["mesh"])
        if mesh is None:
            placed_curves[cid] = "no mesh (path only)"
            continue
        ism = _add_instance_component(host, unreal.InstancedStaticMeshComponent, f"ISM_{cid}")
        ism.set_static_mesh(mesh)
        if rows[0]["material"]:
            ism.set_material(ism.get_num_materials() - 1, _soft_asset(rows[0]["material"]))
        ism.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        base = unreal.Transform(unreal.Vector(cx, cy, cz))
        for r in rows:
            if r["kind"] in GROUND_SNAPPED_CURVE_KINDS:
                gz = _ground_z(world, float(r["x"]), float(r["y"]), spawned)
                if gz is not None:
                    r["z"] = str(gz)
            s = float(r["scale"])
            xf = unreal.Transform(_vec(r), unreal.Rotator(0.0, 0.0, float(r["yaw"])), unreal.Vector(s, s, s))
            ism.add_instance(xf, True)
        placed_curves[cid] = ism.get_instance_count()
    return {"host": host_label, "removed_previous": removed, "slots": placed_slots, "curves": placed_curves}


STEPS = {
    "preflight": step_preflight,
    "structures_place": step_structures_place,
    "cleanup": step_cleanup,
    "materials": step_materials,
    "glitter_materials": step_glitter_materials,
    "table": step_table,
    "volume": step_volume,
    "generate": step_generate,
    "count": step_count,
    "save": step_save,
    "reset_table": step_reset_table,
    "template_scaffold": step_template_scaffold,
    "fx_systems": step_fx_systems,
    "fx_materials": step_fx_materials,
    "fx_place": step_fx_place,
    "fx_audit": step_fx_audit,
    "probe_ground": step_probe_ground,
    "hide_houdini_overlays": step_hide_houdini_overlays,
    "lookdev_cameras": step_lookdev_cameras,
    "lookdev_capture": step_lookdev_capture,
    "bookmark": step_bookmark,
    "ensure_euw": step_ensure_euw,
}


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        raise SystemExit("usage: world_compiler_ue.py <bundle_dir> <step>")
    bundle_dir = Path(argv[0])
    step = argv[1]
    b = _load_bundle(bundle_dir)
    try:
        payload = STEPS[step](b)
    except Exception as exc:
        payload = {"error": str(exc), "traceback": traceback.format_exc()[-2000:]}
    _write(bundle_dir, step, payload)


if __name__ == "__main__":
    main(sys.argv[1:])
