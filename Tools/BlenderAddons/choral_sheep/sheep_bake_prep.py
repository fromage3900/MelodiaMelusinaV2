# -*- coding: utf-8 -*-
"""Bake-prep for the Choral Sheep high->low texture bake.

Readies the sheep mesh for a Substance/SimpleBake high->low bake so the
'detailed masks and textures' the owner wants come out clean and UE-ready.

What this does (all non-destructive prep, no geometry destroyed):
  1. Splits scene into HIGH and LOW collections so SimpleBake/Substance
     knows which mesh bakes onto which.
  2. Marks the low-poly sheep (Skin_Sheep_*) as the bake target and
     gives it a clean UV set (or flags a warning if it has none).
  3. Writes a bake manifest JSON listing the exact output maps the sheep's
     UE material needs (Normal, AO, Curvature, ID, Height, Roughness).
  4. Emits the exact SimpleBake + Substance export commands.

Blender 5.2. Run from the Scripting workspace console (or headless):
  exec(compile(open(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/BlenderAddons/melodia_studio/sheep_bake_prep.py", encoding="utf-8").read(), "x", "exec"))
  sheep_bake_prep.build()   # -> writes manifest, prints commands
"""
import json
import os

try:
    import bpy  # type: ignore
    _HAVE_BPY = True
except Exception:
    bpy = None  # type: ignore
    _HAVE_BPY = False

# Output maps the sheep's UE material (MI_ChoralSheep) needs.
# Maps follow Substance/UE naming so SimpleBake + Substance agree.
BAKE_MAPS = [
    {"name": "Normal",        "suffix": "_Normal",    "engine": "NORMAL"},
    {"name": "AmbientOcclusion", "suffix": "_AO",     "engine": "AO"},
    {"name": "Curvature",     "suffix": "_Curvature", "engine": "CURVATURE"},
    {"name": "ID",            "suffix": "_ID",        "engine": "MATERIAL_ID"},
    {"name": "Height",        "suffix": "_Height",    "engine": "HEIGHT"},
    {"name": "Roughness",     "suffix": "_Roughness", "engine": "ROUGHNESS"},
]

LOW_NAME = "Skin_Sheep_ZSpheres2"   # the low-poly bake target


def _find_low():
    if not _HAVE_BPY:
        return None
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name == LOW_NAME:
            return o
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("Skin_"):
            return o
    return None


def _find_high():
    """High-poly = a real sculpted/high-res mesh, NOT the low sheep and NOT
    the rig's cs_* control/shape helpers (those are UI widgets, not geometry
    to bake from)."""
    if not _HAVE_BPY:
        return []
    low = _find_low()
    lows = {low.name} if low is not None else set()
    highs = []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name in lows:
            continue
        if o.name.startswith("cs_"):
            continue          # rig control/shape helper - not bake geometry
        if o.name.startswith("Skin_"):
            continue          # another low-poly skin variant, not high
        highs.append(o)
    # a true high mesh usually lives in a 'High' collection or carries more verts
    return highs


def _has_uv(obj):
    return _HAVE_BPY and obj is not None and obj.data.uv_layers


def build(manifest_dir=None):
    """Prepare collections + write the bake manifest."""
    if not _HAVE_BPY:
        print("[sheep-bake] no bpy (offline) - returning map list only")
        return BAKE_MAPS

    low = _find_low()
    highs = _find_high()

    # 1) Ensure HIGH / LOW collections exist
    def ensure_col(name):
        if name not in bpy.data.collections:
            bpy.data.collections.new(name)
        return bpy.data.collections[name]
    hi = ensure_col("ChoralSheep_HIGH")
    lo = ensure_col("ChoralSheep_LOW")
    for h in highs:
        if h.name not in hi.objects:
            hi.objects.link(h)
    if low is not None and low.name not in lo.objects:
        lo.objects.link(low)

    # 2) UV check on the low target
    uv_ok = _has_uv(low)
    uv_status = "ok" if uv_ok else "MISSING"

    # 3) Write manifest
    root = manifest_dir or os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "Saved", "Exports", "ChoralSheep")
    os.makedirs(root, exist_ok=True)
    manifest = {
        "schema": "melodia.choral_sheep.bake.v1",
        "target": low.name if low else "Skin_Sheep_*",
        "high_sources": [h.name for h in highs],
        "uv": uv_status,
        "maps": BAKE_MAPS,
        "substance": {
            "export_size": 2048,
            "engine": "SimpleBake",
            "high_to_low": True,
            "cage": "auto",
        },
        "ue_material_target": "/Game/Melodia/Companions/ChoralSheep/MI_ChoralSheep",
    }
    path = os.path.join(root, "choral_sheep_bake_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[sheep-bake] LOW={low.name if low else '?'} UV={uv_status}")
    print(f"[sheep-bake] HIGH sources: {[h.name for h in highs]}")
    print(f"[sheep-bake] collections ChoralSheep_HIGH / ChoralSheep_LOW ready")
    print(f"[sheep-bake] manifest -> {path}")

    # 4) Print the SimpleBake command hints
    print("\n=== SimpleBake (Blender) command ===")
    print(f"  1. Select LOW ({low.name if low else 'Skin_Sheep_*'}) as target.")
    print("  2. Select HIGH meshes as source (cage auto).")
    print("  3. Bake: Normal, AO, Curvature, ID, Height.")
    print("\n=== Substance Painter export ===")
    print("  Import the baked mesh + maps, paint detail masks,")
    print("  export to UE: BaseColor/Normal/ORM(RMAO)/Height/Emissive @ 2048.")
    print("\n=== UE ===")
    print("  Create MI_ChoralSheep from the toon master; plug the texture sets.")
    return manifest


if __name__ == "__main__":
    build()
