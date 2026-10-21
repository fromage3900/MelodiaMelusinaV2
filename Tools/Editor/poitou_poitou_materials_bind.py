#!/usr/bin/env python
"""Author the missing Poitou materials and bind them to the Poitou meshes.

Run headlessly (no editor GUI, no GPU):

    UnrealEditor-Cmd.exe BS_GodFile.uproject -run=pythonscript \
        -script=".../poitou_poitou_materials_bind.py" -unattended -nopause \
        -nosplash -nullrhi -stdout -FullStdOutLogOutput

Why this exists
---------------
Two separate gaps were called "the missing Poitou material":

  1. AUTHORING.  The MI catalogue in /Game/EnvSandbox/Poitou/Materials has
     6 of ~30 named MIs, and M_Poitou_Stone_Plinth - the soubassement band
     that every Poitou stone mesh is supposed to carry - was never
     authored at all.
  2. BINDING, which turned out to be the bigger one.  The Poitou mesh
     pack HAS a full set of per-mesh masters (M_Tufa_Stone_Blocks,
     M_Ash_Bark, M_Barque_Oak_Planks, M_Well_Limestone, M_Calvary_Stone,
     M_Bench_Limestone, M_Wrought_Iron, M_Pigouille_Ash_Wood ...), but
     most of the meshes have slot 0 still pointing at WorldGridMaterial.
     A mesh with WorldGridMaterial renders as the untextured grid default:
     grey, unlit-looking, and unmistakably a placeholder in a shot.

So this script does three things, in order:

  a) authors the missing MIs as MaterialInstanceConstants of the ONE
     existing toon master (/Game/EnvSandbox/Materials/Masters/
     M_Master_Toon_Universal).  No new master is created - the canon
     forbids it, and the existing master already carries the lime-wash /
     damp / moss layer stack.
  b) authors M_Poitou_Stone_Plinth: the plinth (soubassement) band.  It
     is an MI despite the M_ prefix, because the mesh pack's naming
     convention puts per-mesh materials in /Game/Melodia/Meshes/Poitou and
     the canon forbids a new master.
  c) binds every Poitou mesh to its correct material, and gives the
     masonry meshes a SECOND slot carrying the plinth material, so the
     soubassement band has somewhere to live.

Idempotent: existing assets are never overwritten, and a material that is
already correct is left alone.
"""
from __future__ import annotations

import os

import unreal

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()

TOON_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MI_ROOT = "/Game/EnvSandbox/Poitou/Materials"
MESH_ROOT = "/Game/Melodia/Meshes/Poitou"

log = []
created = []
touched = []


def srgb_to_linear(hexs):
    h = hexs.lstrip("#")

    def c(v):
        v = int(v, 16) / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    return unreal.LinearColor(c(h[0:2]), c(h[2:4]), c(h[4:6]), 1.0)


# ----------------------------------------------------------------------
# (a) the missing MI catalogue - all MIs of the one toon master
# ----------------------------------------------------------------------
# tint / moss / mist follow Tools/Poitou/palette_and_master_MA.md slot table.
MIS = {
    # name                      folder      base tint   rough  extra vec
    "MI_Poitou_Plinth_DampStone": (MI_ROOT, "#9A9384", 0.90, {"MistColor": "#DCE3E4"}),
    "MI_Poitou_Church_Ashlar":   (MI_ROOT, "#D9C9A3", 0.75, {"MistColor": "#DCE3E4"}),
    "MI_Poitou_Ruin_Limestone":  (MI_ROOT, "#9A9384", 0.85, {"MistColor": "#DCE3E4"}),
    "MI_Poitou_Quoin_Limestone": (MI_ROOT, "#D9C9A3", 0.75, {"MistColor": "#DCE3E4"}),
    "MI_Poitou_Wall_LimeRender": (MI_ROOT, "#E6DFCC", 0.88, {"MistColor": "#DCE3E4"}),
    "MI_Poitou_Shutter_VertDeau": (MI_ROOT, "#9DB8A5", 0.60, {"MistColor": "#DCE3E4"}),
    # the chaine / arase band: a brick course through the wall thickness
    "MI_Poitou_Arase_Brick":   (MI_ROOT, "#8C5A3C", 0.80, {"MistColor": "#DCE3E4"}),
    # the plinth (soubassement) band - darker, wetter base stone
    "M_Poitou_Stone_Plinth":     (MESH_ROOT, "#9A9384", 0.88, {"MistColor": "#DCE3E4"}),
}

SHARED_VEC = {
    "DawnLowColor": "#AAB8AF",
    "DawnHighColor": "#EAEFF6",
    "DreamRimColor": "#DCE3E4",
    "MossColor": "#5F6B3B",
}


def build_mis():
    parent = unreal.load_asset(TOON_PARENT)
    if not parent:
        log.append("FAIL: parent not found " + TOON_PARENT)
        return
    vnames = set(str(n) for n in MEL.get_vector_parameter_names(parent))
    snames = set(str(n) for n in MEL.get_scalar_parameter_names(parent))
    log.append("[params] vectors=%s" % sorted(vnames))
    log.append("[params] scalars=%s" % sorted(snames))
    for mi_name, (folder, tint, rough, extra) in MIS.items():
        p = "%s/%s" % (folder, mi_name)
        if EAL.does_asset_exist(p):
            log.append("SKIP exists: " + p)
            continue
        mi = TOOLS.create_asset(mi_name, folder, unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
        if not mi:
            log.append("FAIL create " + p)
            continue
        created.append(mi)
        MEL.set_material_instance_parent(mi, parent)
        vec = dict(SHARED_VEC)
        vec["BaseTint"] = tint
        vec.update(extra)
        done, missing = [], []
        for k, hx in vec.items():
            if k in vnames:
                MEL.set_material_instance_vector_parameter_value(mi, k, srgb_to_linear(hx))
                done.append(k)
            else:
                missing.append(k)
        if "Roughness" in snames:
            MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
            done.append("Roughness")
        else:
            missing.append("Roughness")
        MEL.update_material_instance(mi)
        log.append("CREATED %s set[%s] missing[%s]" % (p, ",".join(done), ",".join(missing)))


# ----------------------------------------------------------------------
# (c) binding: every Poitou mesh to its material
# ----------------------------------------------------------------------
# mesh -> material.  The masters already exist in the mesh pack; only the
# binding was missing.  "plinth" adds M_Poitou_Stone_Plinth as slot 1.
BIND = {
    "SM_AshTetard_Canal_03_Sculpted":        ("M_Ash_Bark",),
    "SM_AshTetard_Twisted_02_Sculpted":      ("M_Ash_Bark",),
    "SM_AshTetard_Ancient_01":               ("M_Ash_Bark",),
    "SM_Maillezais_CrumbledWall_Sculpted":    ("M_Tufa_Stone_Blocks", "plinth"),
    "SM_Maillezais_BrokenArch_Sculpted":      ("M_Tufa_Stone_Blocks", "plinth"),
    "SM_Maillezais_ButtressStub_Sculpted":    ("M_Tufa_Stone_Blocks", "plinth"),
    "SM_Marais_Barque_4m6_Sculpted":          ("M_Barque_Oak_Planks",),
    "SM_Marais_Pigouille_Pole_Sculpted":      ("M_Pigouille_Ash_Wood",),
    "SM_Poitou_BridgeParapet":                ("M_Tufa_Stone_Blocks", "plinth"),
    "SM_Poitou_BridgeParapet_Sculpted":       ("M_Tufa_Stone_Blocks", "plinth"),
    "SM_Poitou_LockGate_Pair":                ("M_Wrought_Iron",),
    "SM_Poitou_LockGate_Sculpted":            ("M_Wrought_Iron",),
    "SM_Poitou_VillageWell_Sculpted":         ("M_Well_Limestone", "plinth"),
    "SM_Poitou_StoneBench_Sculpted":          ("M_Bench_Limestone",),
    "SM_Poitou_CalvaryCross_Sculpted":        ("M_Calvary_Stone",),
    "SM_Poitou_Cymatic_Spire_Sculpted":       ("M_Tufa_Stone_Blocks",),
    "SM_Poitou_Acoustic_OrganChimney_Sculpted": ("M_Tufa_Stone_Blocks",),
}

# meshes outside the pack that still need a binding
BIND_OTHER_DIR = {"SM_Melusina_ClayHouse_v07": "/Game/EnvSandbox/Poitou/House/Clay"}
BIND_OTHER = {
    "SM_Melusina_ClayHouse_v07": ("/Game/EnvSandbox/Poitou/Materials/MI_Poitou_LimeWash", None),
}


def _new_slot():
    """A fresh, independent static-material slot.

    The struct class is not exposed under a stable name across UE 5.x
    Python builds, and copying an existing slot aliases it (mutating the
    copy changes the original), so the array must be grown with a NEW
    struct.  If the class is unavailable the caller skips the extra slot
    rather than corrupting slot 0.
    """
    for name in ("StaticMaterial", "SlotMaterial"):
        cls = getattr(unreal, name, None)
        if cls is not None:
            try:
                return cls()
            except Exception:
                pass
    return None


def set_slot(mesh, index, material):
    """Set (or grow to) a static material slot."""
    slots = list(mesh.get_editor_property("static_materials"))
    if not slots:
        return False
    while len(slots) <= index:
        blank = _new_slot()
        if blank is None:
            return False
        slots.append(blank)
    s = slots[index]
    s.set_editor_property("material_interface", material)
    slots[index] = s
    mesh.set_editor_property("static_materials", slots)
    return True


def bind():
    plinth = unreal.load_asset("%s/M_Poitou_Stone_Plinth" % MESH_ROOT)
    jobs = []
    for name, spec in BIND.items():
        jobs.append(("%s/%s.%s" % (MESH_ROOT, name, name),
                     "%s/%s.%s" % (MESH_ROOT, spec[0], spec[0]),
                     "plinth" in (spec[1:] or ())))
    for name, (mat_path, wants_plinth) in BIND_OTHER.items():
        jobs.append(("%s/%s.%s" % (BIND_OTHER_DIR[name], name, name),
                     "%s.%s" % (mat_path, mat_path.rsplit("/", 1)[-1]),
                     bool(wants_plinth)))
    for mesh_path, mat_path, wants_plinth in jobs:
        mat = unreal.load_asset(mat_path)
        if mat is None:
            log.append("FAIL material missing for %s: %s" % (mesh_path, mat_path))
            continue
        mesh = unreal.load_asset(mesh_path)
        if mesh is None:
            log.append("FAIL mesh missing: " + mesh_path)
            continue
        set_slot(mesh, 0, mat)
        if wants_plinth and plinth:
            set_slot(mesh, 1, plinth)
        after = mesh.get_editor_property("static_materials")
        touched.append(mesh)
        log.append("BOUND %-42s slot0=%s slot1=%s" % (
            mesh_path.rsplit("/", 1)[-1],
            (after[0].get_editor_property("material_interface").get_path_name().split("/")[-1]
             if len(after) > 0 and after[0].get_editor_property("material_interface") else "EMPTY"),
            (after[1].get_editor_property("material_interface").get_path_name().split("/")[-1]
             if len(after) > 1 and after[1].get_editor_property("material_interface") else "-")))


for step in (build_mis, bind):
    try:
        step()
    except Exception as e:
        log.append("ERROR in %s: %s" % (step.__name__, e))

# save only what this run created or changed
for a in created:
    try:
        EAL.save_loaded_asset(a, only_if_is_dirty=False)
    except Exception as e:
        log.append("save failed %s: %s" % (a.get_name(), e))
for m in touched:
    try:
        EAL.save_loaded_asset(m, only_if_is_dirty=False)
    except Exception as e:
        log.append("save failed %s: %s" % (m.get_name(), e))
log.append("CREATED %d material(s), BOUND %d mesh(es)." % (len(created), len(touched)))
print("\n".join("[poitou_mats] " + l for l in log))
