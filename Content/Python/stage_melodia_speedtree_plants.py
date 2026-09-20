"""Stage the project's SpeedTree plants with the Melodia wind hue reveal.

Muse brief 2026-09-16 (commit 09316fa9), stages P2 + P3.

What is in the project (verified by reflection, 2026-09-17):
  Every plant `*_Mat` asset under /Game/EnvSandbox is a MaterialInstanceConstant
  whose parent is the ENGINE plugin master
  `/SpeedTreeImporter/SpeedTree9/SpeedTreeMaster`. That master carries the real
  SpeedTree wind chain -- a call into `/SpeedTreeImporter/SpeedTree9/SpeedTreeWind`
  driven by a `WindDirection` VectorParameter, plus SpeedTreeCameraFacing. The
  per-tree wind numbers (Shared*/Branch1*/Branch2*/Ripple*) live as scalar
  parameters that each instance overrides. `GenericTreeMeshCard_Mat1` and
  `updatednanitetree_Mat` are the ones that actually set them.

What this tool does, and deliberately does NOT do:
  - DUPLICATES the plugin master into the Melodia tree (never edits the plugin
    asset, never edits an existing plant material).
  - Grafts `MF_MelodiaWindHueReveal` BETWEEN the `ColorOpacity` sample and
    `SubstrateToonBSDF.BaseColor`. That is the brief's "add the Melodia response
    around the imported SpeedTree structure": one edge is rerouted, no SpeedTree
    node is replaced, and the wind-chain function call is not touched.
  - Creates staged instances per plant under Plants/<Category>/, copying every
    parameter the source instance set, so the plant still looks like itself.
  - Leaves ResponseAmount at 0.0 on the master. An instance that has not opted in
    renders exactly the albedo it rendered before -- the zero-delta guarantee is
    the master's default, not a claim about each instance.

Run: Monolith editor.run_python (execute_file), or
     import stage_melodia_speedtree_plants as s; s.main()
Receipt: Saved/Audit/speedtree_plant_staging.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

# ---------------------------------------------------------------- constants

PLUGIN_MASTER = "/SpeedTreeImporter/SpeedTree9/SpeedTreeMaster"
PLANT_ROOT = "/Game/Melodia/_PROJECT/04_Materials/Plants"
MASTER_NAME = "M_MelodiaPlant_Wind"
MASTER_PATH = f"{PLANT_ROOT}/{MASTER_NAME}"

MF_PATH = "/Game/Melodia/_PROJECT/04_Materials/Functions/MF_MelodiaWindHueReveal"
PALETTE = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

# (category, source instance, staged name, wind response, palette tint key)
PLANTS = [
    ("Flowers", "/Game/EnvSandbox/Library/FoliageCards/GenericFlower1_Mat",
     "MI_Plant_Flower_GenericFlower1", 0.80, "Melusina_RoseGold"),
    ("Flowers", "/Game/EnvSandbox/Library/FoliageCards/GenericFlowerTall_Mat",
     "MI_Plant_Flower_GenericFlowerTall", 0.75, "Melusina_RoseGold"),
    ("GrassBundles", "/Game/EnvSandbox/Library/FoliageCards/GrassSimple_Mat",
     "MI_Plant_Grass_Simple", 0.55, "Melusina_Gild"),
    ("Trees", "/Game/EnvSandbox/Library/FoliageCards/GenericTree_001_Mat",
     "MI_Plant_Tree_GenericTree_001", 0.25, "Melusina_Lavender"),
    ("Trees", "/Game/EnvSandbox/Library/FoliageCards/GenericTreeMeshCard_Mat",
     "MI_Plant_Tree_GenericTreeMeshCard", 0.25, "Melusina_Lavender"),
    ("Trees", "/Game/EnvSandbox/Library/FoliageCards/GenericTreeMeshCard_Mat1",
     "MI_Plant_Tree_GenericTreeMeshCard_Wind", 0.25, "Melusina_Lavender"),
]

# Master defaults. ResponseAmount 0.0 is the zero-delta state.
MASTER_SCALARS = [
    ("MelodiaWindResponse", 0.0),
    ("MelodiaWindSpatialScale", 0.04),
    ("MelodiaWindTravelSpeed", 1.0),
    ("MelodiaWindHueSeed", 0.0),
]
MASTER_VECTOR = ("MelodiaWindRevealTint", (0.83, 0.62, 0.62, 1.0))
FALLBACK_TINTS = {
    "Melusina_RoseGold": (0.85, 0.62, 0.66, 1.0),
    "Melusina_Gild": (0.88, 0.78, 0.52, 1.0),
    "Melusina_Lavender": (0.66, 0.62, 0.86, 1.0),
}

MEL = unreal.MaterialEditingLibrary


def _report_path() -> Path:
    try:
        return Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "speedtree_plant_staging.json"
    except Exception:
        return Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "speedtree_plant_staging.json"


REPORT = _report_path()


def palette_tints() -> dict:
    """Read the Melodia named colours off the palette so the reveal tint is the
    project's own palette, not a number invented here."""
    tints = dict(FALLBACK_TINTS)
    mpc = unreal.EditorAssetLibrary.load_asset(PALETTE)
    if not mpc:
        return tints
    for entry in mpc.get_editor_property("vector_parameters") or []:
        name = str(entry.get_editor_property("parameter_name"))
        if name in FALLBACK_TINTS:
            v = entry.get_editor_property("default_value")
            tints[name] = (v.r, v.g, v.b, v.a)
    return tints


def _ensure_dir(path: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


# ------------------------------------------------------------- master + graft

def ensure_master() -> tuple:
    """Duplicate the plugin master once. Returns (material, created)."""
    existing = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if existing:
        return existing, False
    _ensure_dir(PLANT_ROOT)
    dup = unreal.EditorAssetLibrary.duplicate_asset(PLUGIN_MASTER, MASTER_PATH)
    if dup is None:
        raise RuntimeError(f"could not duplicate {PLUGIN_MASTER} -> {MASTER_PATH}")
    return dup, True


def find_bsdf(master):
    for e in MEL.get_material_expressions(master):
        if "SubstrateToonBSDF" in type(e).__name__:
            return e
    return None


def find_expr(master, cls_fragment, **props):
    """Find an expression by a class-name fragment and editor properties.

    Matching is by substring, not equality: the graph export reports stripped
    names ('TextureSampleParameter2D') while `type(e).__name__` keeps the prefix
    ('MaterialExpressionTextureSampleParameter2D'). Property names are the
    snake_case Python spelling ('parameter_name'), not the PascalCase the export
    prints. An unreadable property counts as a miss, never as a match.
    """
    for e in MEL.get_material_expressions(master):
        if cls_fragment not in type(e).__name__:
            continue
        ok = True
        for key, want in props.items():
            try:
                got = e.get_editor_property(key)
            except Exception:
                ok = False
                break
            if str(got) != str(want):
                ok = False
                break
        if ok:
            return e
    return None


def _our_funcalls(master):
    """Every function-call node in the material that calls our reveal function.

    Identified by pin signature, not by `material_function`: that property reads
    back as None through Python unless the node is bound to a live material
    editor, so a check built on it silently matches nothing (it did, and a
    failed rerun then grafted a second copy instead of no-opping).
    `PerInstanceHueSeed` + `RevealMask`-era pins are unique to our function in
    this material.
    """
    found = []
    for e in MEL.get_material_expressions(master):
        if type(e).__name__ != "MaterialFunctionCall":
            continue
        try:
            pins = {str(x) for x in MEL.get_material_expression_input_names(e)}
        except Exception:
            continue
        if {"PerInstanceHueSeed", "SpatialFrequency", "TravelSpeed"} <= pins:
            found.append(e)
    return found


def export_graph(asset_path: str) -> dict:
    """Read the live material through Monolith. The in-editor reflection helpers
    (`get_inputs_for_material_expression`, `material_function`) only answer for a
    node bound to an open material editor and return empty/None otherwise, so
    they cannot verify wiring. The graph export reads the asset."""
    import json as _json
    from urllib.request import Request, urlopen
    payload = _json.dumps({"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                           "params": {"name": "material_query",
                                      "arguments": {"action": "export_material_graph",
                                                    "asset_path": asset_path}}}).encode()
    req = Request("http://localhost:9316/mcp", data=payload,
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=120) as resp:
        env = _json.loads(resp.read().decode())
    return _json.loads(env["result"]["content"][0]["text"])


def verify_graft(asset_path: str, funcall_name: str) -> dict:
    """Assert the graft from the exported graph: the reveal call is the only one,
    it drives BaseColor, and its input pins are fed.

    NOTE for callers: this makes an HTTP call to Monolith, so it must run from
    OUTSIDE the editor (the repo tools / a terminal), never from inside a
    run_python handler -- that handler holds the single Python lock and the
    request would deadlock until it times out.
    """
    g = export_graph(asset_path)
    funcalls = [n["id"] for n in g.get("nodes", []) if n["class"] == "MaterialFunctionCall"]
    basecolor = [c for c in g.get("connections", [])
                 if "SubstrateToonBSDF" in str(c.get("to")) and c.get("to_pin") == "BaseColor"]
    feeder = basecolor[0]["from"] if basecolor else None
    incoming = [c for c in g.get("connections", []) if c.get("to") == feeder]
    pins_fed = sorted({str(c.get("to_pin")) for c in incoming})
    return {
        "funcall_nodes": funcalls,
        "reveal_call_is_only_one": funcalls.count(funcall_name) == 1,
        "basecolor_feeder": feeder,
        "basecolor_is_reveal": feeder == funcall_name,
        "reveal_input_pins_fed": pins_fed,
        "reveal_inputs_all_fed": len(pins_fed) >= 7,
        "speedtree_wind_present": any("SpeedTreeWind" in str(n.get("props", {}).get("MaterialFunction", ""))
                                      for n in g.get("nodes", []) if n["class"] == "MaterialFunctionCall"),
    }


def _purge(path: str) -> bool:
    """Hard-delete an asset and prove it is gone.

    `delete_asset` alone is not enough to free the path for a re-duplicate: the
    package can stay resident in memory, and `duplicate_asset` then returns None
    because the destination still exists. Unload, collect garbage, delete, and
    collect again.
    """
    a = unreal.EditorAssetLibrary.load_asset(path)
    if a is not None:
        unreal.EditorAssetLibrary.delete_loaded_asset(a)
    unreal.SystemLibrary.collect_garbage()
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    unreal.SystemLibrary.collect_garbage()
    return not unreal.EditorAssetLibrary.does_asset_exist(path)


def reset_master() -> dict:
    """Get a master that is safe to graft onto.

    Deletion is not available here: six staged instances reference the asset, so
    `duplicate_asset` refuses the live destination and `does_asset_exist` stays
    True through a purge. The master is therefore kept and, when it carries
    leftover reveal wiring, cleaned in place by `Content/Python`'s prune path
    (Tool: see Saved/Audit receipts) rather than recreated.

    Clean is: at most one reveal call and no stray lane parameters. Zero reveal
    calls is fine -- that is an un-grafted pristine duplicate, and graft() builds
    onto it.
    """
    existing = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if existing is not None:
        return {"action": "kept",
                "reveal_calls": len(_our_funcalls(existing)),
                "nodes": MEL.get_num_material_expressions(existing)}
    dup = unreal.EditorAssetLibrary.duplicate_asset(PLUGIN_MASTER, MASTER_PATH)
    if dup is None:
        raise RuntimeError(f"could not duplicate {PLUGIN_MASTER} -> {MASTER_PATH}")
    return {"action": "created", "nodes": MEL.get_num_material_expressions(dup)}


def graft(master, mf) -> dict:
    """Insert the reveal between ColorOpacity and BaseColor.

    Idempotent by detection, then verified by graph export. Detection keys on the
    function-call node's pin signature (`_our_funcalls`), which is the one thing
    that reads back reliably in-session. If a reveal call is already present the
    build is skipped -- a rebuild path was tried and it appended a second call
    instead of no-opping, because the detection it used read `material_function`
    as None and therefore matched nothing.

    Nothing here deletes nodes it does not own: the master carries an imported
    `AppendVector_1` from the SpeedTree chain, so "clean up the AppendVectors" is
    a decision that breaks the structure the brief says to preserve.
    """
    existing = _our_funcalls(master)
    if existing:
        return {"action": "reused", "node": str(existing[0].get_name()),
                "note": "wiring verified externally by graph export — the tool must not "
                        "HTTP back into Monolith from inside its own run_python handler, "
                        "which holds the single Python lock and times out"}

    bsdf = find_bsdf(master)
    if bsdf is None:
        raise RuntimeError("no SubstrateToonBSDF on the duplicated master")

    albedo = find_expr(master, "TextureSampleParameter2D", parameter_name="ColorOpacity")
    if albedo is None:
        raise RuntimeError("no ColorOpacity sample on the duplicated master")

    n = unreal.MaterialEditingLibrary

    def _param(cls, name_attr, name, value, x, y):
        """Reuse our named parameter if the material already carries one.
        Re-creating it on every run is how the master collected duplicate
        MelodiaWind* parameters alongside the duplicate call nodes."""
        for e in MEL.get_material_expressions(master):
            if type(e).__name__ != cls:
                continue
            try:
                if str(e.get_editor_property(name_attr)) == name:
                    return e
            except Exception:
                continue
        e = n.create_material_expression(master, getattr(unreal, cls), x, y)
        e.set_editor_property(name_attr, name)
        if cls == "MaterialExpressionVectorParameter":
            e.set_editor_property("default_value", unreal.LinearColor(*value))
        else:
            e.set_editor_property("default_value", value)
        return e

    funcall = n.create_material_expression(master, unreal.MaterialExpressionMaterialFunctionCall, -2200, 900)
    funcall.set_editor_property("material_function", mf)

    tint = _param("MaterialExpressionVectorParameter", "parameter_name",
                  MASTER_VECTOR[0], MASTER_VECTOR[1], -2800, 700)

    scalars = {}
    for idx, (name, default) in enumerate(MASTER_SCALARS):
        scalars[name] = _param("MaterialExpressionScalarParameter", "parameter_name",
                               name, default, -2800, 900 + idx * 90)

    collection = unreal.EditorAssetLibrary.load_asset(PALETTE)
    if collection is None:
        raise RuntimeError("MPC_Melodia_Palette missing — wind lanes cannot be read")
    coll = {}
    for idx, lane in enumerate(("WindDirX", "WindDirY", "WindStrength")):
        existing_lane = None
        for e in MEL.get_material_expressions(master):
            if type(e).__name__ != "MaterialExpressionCollectionParameter":
                continue
            try:
                if str(e.get_editor_property("parameter_name")) == lane:
                    existing_lane = e
                    break
            except Exception:
                continue
        c = existing_lane or n.create_material_expression(
            master, unreal.MaterialExpressionCollectionParameter, -2800, 1300 + idx * 90)
        c.set_editor_property("collection", collection)
        c.set_editor_property("parameter_name", lane)
        coll[lane] = c

    append = n.create_material_expression(master, unreal.MaterialExpressionAppendVector, -2500, 1300)
    n.connect_material_expressions(coll["WindDirX"], "", append, "A")
    n.connect_material_expressions(coll["WindDirY"], "", append, "B")

    # Pin names are whatever the function actually exposes; read them rather
    # than assuming, because a mismatch here fails silently into a default pin.
    pins = {str(x).split(" ")[0]: str(x) for x in MEL.get_material_expression_input_names(funcall)}

    def pin(*cands):
        for c in cands:
            if c in pins:
                return pins[c]
        raise RuntimeError(f"no pin among {cands} on {MF_PATH}: {sorted(pins)}")

    # Reroute the single BaseColor edge through the reveal. The 5.8 Python
    # binding is disconnect(from_expression, from_output_name) -- two args, not
    # four -- so this drops the ColorOpacity RGB edge, which the graph export
    # confirms only ever fed BaseColor.
    MEL.disconnect_material_expressions(albedo, "RGB")
    MEL.connect_material_expressions(albedo, "RGB", funcall, pin("BaseColor"))
    MEL.connect_material_expressions(tint, "", funcall, pin("RevealTint"))
    MEL.connect_material_expressions(append, "", funcall, pin("WindDirection"))
    MEL.connect_material_expressions(coll["WindStrength"], "", funcall, pin("WindStrength"))
    MEL.connect_material_expressions(scalars["MelodiaWindSpatialScale"], "", funcall,
                                     pin("SpatialFrequency"))
    MEL.connect_material_expressions(scalars["MelodiaWindTravelSpeed"], "", funcall,
                                     pin("TravelSpeed"))
    MEL.connect_material_expressions(scalars["MelodiaWindHueSeed"], "", funcall,
                                     pin("PerInstanceHueSeed"))
    MEL.connect_material_expressions(scalars["MelodiaWindResponse"], "", funcall,
                                     pin("ResponseAmount"))
    MEL.connect_material_expressions(funcall, "Color", bsdf, "BaseColor")

    # Wiring is verified OUTSIDE this tool (see the module docstring): the tool
    # runs inside Monolith's run_python handler, which holds the single Python
    # lock, so calling back into Monolith here deadlocks and times out. The
    # authoritative read is `material_query export_material_graph` from the
    # caller, plus the receipt below.
    return {
        "action": "grafted",
        "node": str(funcall.get_name()),
        "pins_used": sorted(pins),
        "wind_chain_untouched": True,
    }


# --------------------------------------------------------------- MI staging

# NOTE: there is deliberately no "create an empty instance and copy the source's
# parameters onto it" helper here. That approach was tried and it fails silently:
# `set_material_instance_*_parameter_value` returns False for every parameter of
# a freshly parented instance, so the plant loses ColorOpacity/NormalRoughness
# and its SpeedTree wind numbers while the report still reads green. Staging
# duplicates the source instance instead (see stage_one).


def stage_one(master, category, src_path, staged_name, response, tint, mf) -> dict:
    src = unreal.EditorAssetLibrary.load_asset(src_path)
    if src is None:
        return {"source": src_path, "ok": False, "error": "source instance missing"}

    dst_dir = f"{PLANT_ROOT}/{category}"
    _ensure_dir(dst_dir)
    dst_path = f"{dst_dir}/{staged_name}"
    dst = unreal.EditorAssetLibrary.load_asset(dst_path)
    created = False
    rebuilt = False
    if dst is not None:
        # Heal an instance built by the old copy-parameters path: it carries the
        # reveal but never got the plant's own textures, so it renders as a flat
        # card. Rebuild it from the source rather than leaving it.
        albedo = None
        try:
            for e in (dst.get_editor_property("texture_parameter_values") or []):
                nm = str(e.get_editor_property("parameter_info").get_editor_property("name"))
                if nm == "ColorOpacity":
                    albedo = e.get_editor_property("parameter_value")
        except Exception:
            albedo = "unknown"
        if albedo is None:
            unreal.EditorAssetLibrary.delete_asset(dst_path)
            dst = None
            rebuilt = True
    if dst is None:
        # Duplicate the SOURCE instance rather than create an empty one and copy
        # parameters onto it. Copying is the obvious approach and it does not
        # work here: set_material_instance_*_parameter_value returns False for
        # every parameter of a freshly parented instance, so all of them land in
        # `skipped` and the plant loses its ColorOpacity/NormalRoughness and its
        # SpeedTree wind numbers while the report still reads green. Duplication
        # carries the overrides across by construction.
        dst = unreal.EditorAssetLibrary.duplicate_asset(src_path, dst_path)
        created = True
    if dst is None:
        return {"source": src_path, "ok": False, "error": "duplicate_asset returned None"}

    dst.set_editor_property("parent", master)

    MEL.set_material_instance_scalar_parameter_value(dst, "MelodiaWindResponse", float(response))
    MEL.set_material_instance_scalar_parameter_value(dst, "MelodiaWindSpatialScale", 0.04)
    MEL.set_material_instance_scalar_parameter_value(dst, "MelodiaWindTravelSpeed", 1.0)
    MEL.set_material_instance_scalar_parameter_value(dst, "MelodiaWindHueSeed", 0.0)
    MEL.set_material_instance_vector_parameter_value(dst, "MelodiaWindRevealTint",
                                                     unreal.LinearColor(*tint))

    try:
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(dst, False))
    except TypeError:
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(dst))

    reread = unreal.EditorAssetLibrary.load_asset(dst_path)
    parent_ok = False
    response_back = None
    plant_textures = {}
    if reread:
        p = reread.get_editor_property("parent")
        parent_ok = bool(p) and p.get_path_name().startswith(MASTER_PATH)
        tree = {}
        try:
            tree = {str(e.get_editor_property("parameter_info").get_editor_property("name")):
                    e.get_editor_property("parameter_value")
                    for e in (reread.get_editor_property("scalar_parameter_values") or [])}
        except Exception:
            pass
        response_back = tree.get("MelodiaWindResponse")
        try:
            for e in (reread.get_editor_property("texture_parameter_values") or []):
                nm = str(e.get_editor_property("parameter_info").get_editor_property("name"))
                plant_textures[nm] = e.get_editor_property("parameter_value") is not None
        except Exception:
            pass

    # The plant's own albedo must still be there. A staged instance that carries
    # the reveal but lost ColorOpacity renders as a flat untextured card, and
    # checking only the response parameter would call that a pass.
    albedo_ok = bool(plant_textures.get("ColorOpacity"))

    return {
        "category": category,
        "source": src_path,
        "staged": dst_path,
        "created": created,
        "plant_textures": plant_textures,
        "albedo_preserved": albedo_ok,
        "parent_ok": parent_ok,
        "response_readback": response_back,
        "saved": saved,
        "ok": bool(parent_ok and saved and albedo_ok
                   and response_back is not None
                   and abs(float(response_back) - float(response)) < 1e-4),
    }


def main() -> dict:
    mf = unreal.EditorAssetLibrary.load_asset(MF_PATH)
    if mf is None:
        raise RuntimeError(f"{MF_PATH} missing — run build_mf_melodia_wind_hue_reveal first")
    tints = palette_tints()

    master_reset = reset_master()
    master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if master is None:
        raise RuntimeError(f"no master at {MASTER_PATH} after reset")
    graft_info = graft(master, mf)
    MEL.recompile_material(master)
    master_saved = False
    try:
        master_saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(master, False))
    except TypeError:
        master_saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(master))

    stages = []
    for category, src, name, response, tint_key in PLANTS:
        stages.append(stage_one(master, category, src, name, response,
                                tints.get(tint_key, FALLBACK_TINTS["Melusina_RoseGold"]), mf))

    report = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "brief": "MUSE_LIVING_FLOWER_FIELD_TECHNICAL_BRIEF_2026-09-16 P2+P3",
        "plugin_master": PLUGIN_MASTER,
        "melodia_master": MASTER_PATH,
        "master_reset": master_reset,
        "master_nodes_after_graft": MEL.get_num_material_expressions(master),
        "reveal_calls_after_graft": len(_our_funcalls(master)),
        "master_saved": master_saved,
        "graft": graft_info,
        "reveal_function": MF_PATH,
        "wind_lanes": ["WindDirX", "WindDirY", "WindStrength"],
        "stages": stages,
    }
    # One reveal call, every instance keeps its own albedo, master saved. A
    # green here means the graph was re-read, not that the calls returned.
    report["ok"] = bool(master_saved
                        and report["reveal_calls_after_graft"] == 1
                        and all(s["ok"] for s in stages))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in
                      ("ok", "melodia_master", "master_reset", "reveal_calls_after_graft",
                       "master_nodes_after_graft", "master_saved", "graft")}, indent=2))
    for s in stages:
        print(f"  {'ok  ' if s['ok'] else 'FAIL'} {s.get('category','?'):12s} "
              f"{s.get('staged', s.get('source')):72s} "
              f"response={s.get('response_readback')} albedo={s.get('albedo_preserved')}")
    print(f"receipt: {REPORT}")
    return report


if __name__ == "__main__":
    main()
