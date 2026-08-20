# Dress v22 background with existing GN builders as in-game geometry prototypes.
# Does not save the stage. Does not add new builders.
import json
from pathlib import Path

import bpy
from mathutils import Vector

AUDIT = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\gn_bg_prototype_2026-08-12.json")
COLL_NAME = "GN_BG_Prototype"

# Behind Melusina / Studio_Backdrop (Cam_Beauty looks +Y toward origin).
PLACEMENTS = [
    {
        "id": "nave_rose",
        "tree": "MEL_ornament_radial",
        "preset": None,
        "loc": (-2.6, 6.4, 1.5),
        "scale": 0.85,
        "game": "KaleidoNave ornament / rose analog",
    },
    {
        "id": "nave_frame",
        "tree": "MEL_ornament_frame",
        "preset": None,
        "loc": (2.5, 6.6, 1.3),
        "scale": 0.75,
        "game": "KaleidoNave frame / tracery analog",
    },
    {
        "id": "nave_vine",
        "tree": "MEL_ornament_vine",
        "preset": None,
        "loc": (-4.4, 5.5, 0.9),
        "scale": 0.65,
        "game": "KaleidoNave vine / nouveau analog",
    },
    {
        "id": "portal_arch",
        "tree": "MEL_arch",
        "preset": None,
        "loc": (0.0, 7.8, 0.0),
        "scale": 1.15,
        "game": "Morning / nave portal analog",
    },
    {
        "id": "nave_window",
        "tree": "MEL_castle_gothic_window",
        "preset": None,
        "loc": (4.0, 7.0, 1.4),
        "scale": 0.8,
        "game": "KaleidoNave gothic window analog",
    },
    {
        "id": "col_L",
        "tree": "MEL_column",
        "preset": "DORIC_SOBER",
        "loc": (-1.7, 5.9, 0.0),
        "scale": 1.0,
        "game": "nave / greybox column",
    },
    {
        "id": "col_R",
        "tree": "MEL_column",
        "preset": "FLUTED_IONIC",
        "loc": (1.7, 5.9, 0.0),
        "scale": 1.0,
        "game": "nave / greybox column",
    },
    {
        "id": "zen_lamp_R",
        "tree": "MEL_env_lantern_post",
        "preset": None,
        "loc": (4.6, 4.1, 0.0),
        "scale": 0.7,
        "game": "ZenForest StreetLamp / lantern proto",
    },
    {
        "id": "zen_lamp_L",
        "tree": "MEL_env_lantern_post",
        "preset": None,
        "loc": (-4.9, 3.9, 0.0),
        "scale": 0.7,
        "game": "ZenForest lantern proto",
    },
    {
        "id": "filigree",
        "tree": "MEL_filigree_spiral",
        "preset": "NOUVEAU_VOLUTE",
        "loc": (-3.1, 7.3, 2.3),
        "scale": 0.55,
        "game": "ZenTrim / filigree language",
    },
    {
        "id": "crest",
        "tree": "MEL_filigree_wreath_ring",
        "preset": None,
        "loc": (3.1, 7.2, 2.5),
        "scale": 0.5,
        "game": "crest / ornament analog",
    },
    {
        "id": "pavilion",
        "tree": "MEL_gazebo",
        "preset": "GARDEN_GAZEBO",
        "loc": (-6.2, 8.4, 0.0),
        "scale": 0.45,
        "game": "ZenForest tea-house / gazebo greybox analog",
    },
]


def _ensure_coll():
    coll = bpy.data.collections.get(COLL_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLL_NAME)
        bpy.context.scene.collection.children.link(coll)
    coll.hide_viewport = False
    coll.hide_render = False
    return coll


def _to_coll(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def _delete_smoke():
    o = bpy.data.objects.get("MEL_Smoke_EffectMagic_LIQUID")
    if not o:
        return False
    bpy.data.objects.remove(o, do_unlink=True)
    return True


def _place(spec, coll) -> dict:
    row = {"id": spec["id"], "tree": spec["tree"], "game": spec["game"], "ok": False}
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(size=0.25, location=spec["loc"])
    obj = bpy.context.active_object
    if obj is None:
        row["error"] = "no_active"
        return row
    obj.name = f"GN_BG_{spec['id']}"
    s = float(spec["scale"])
    obj.scale = (s, s, s)
    _to_coll(obj, coll)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    add = bpy.ops.mel_gn.stack_add(tree_name=spec["tree"])
    row["stack_add"] = str(add)
    if spec.get("preset"):
        apply = bpy.ops.mel_gn.apply_preset(tree_name=spec["tree"], preset_name=spec["preset"])
        row["preset"] = spec["preset"]
        row["apply"] = str(apply)
    mods = [m.name for m in obj.modifiers]
    row["modifiers"] = mods
    row["ok"] = "FINISHED" in str(add)
    row["loc"] = list(obj.location)
    return row


def main() -> dict:
    out = {
        "filepath": bpy.data.filepath,
        "collection": COLL_NAME,
        "removed_smoke": _delete_smoke(),
        "placed": [],
    }
    coll = _ensure_coll()
    # Clear prior dress of same names
    for spec in PLACEMENTS:
        old = bpy.data.objects.get(f"GN_BG_{spec['id']}")
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
    for spec in PLACEMENTS:
        try:
            out["placed"].append(_place(spec, coll))
        except Exception as exc:
            out["placed"].append({"id": spec["id"], "tree": spec["tree"], "ok": False, "error": str(exc)})
    out["ok_count"] = sum(1 for p in out["placed"] if p.get("ok"))
    out["fail_count"] = len(out["placed"]) - out["ok_count"]
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("GN_BG_JSON " + json.dumps(out, default=str))
    return out


main()
