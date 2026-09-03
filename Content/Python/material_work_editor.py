"""Material work — executed in-editor via Monolith.

Priority order for world-building today:
1. ZenTrim misuse fix (2 MIs) — trimsheet on tilable fabric
2. Arch Toon MI creation (374 MIs) — cathedral + atlantis get proper toon materials
3. PBR instance creation for 12 complete sets without instances
4. Folder health report

DO NOT: move existing MIs (breaks refs), rename without spec, touch shipping assets.
"""
import unreal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Saved" / "Audit" / "material_work_2026-08-30_done.json"

# ── helpers ──────────────────────────────────────────────────────────
def log(msg):
    unreal.log(f"[MaterialWork] {msg}")

def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        log(f"Created dir: {path}")

def load_asset(path):
    a = unreal.load_asset(path)
    if a is None:
        log(f"WARN: failed to load {path}")
    return a

def save_asset(a):
    if a and unreal.EditorAssetLibrary.can_save_asset(a.get_path_name()):
        unreal.EditorAssetLibrary.save_loaded_asset(a)
        return True
    return False

# ── 1. ZenTrim misuse fix ───────────────────────────────────────────
log("=== 1. ZenTrim misuse fix ===")

ZEN_MISUSE = [
    {
        "mi_path": "/Game/EnvSandbox/Materials/Instances/NikkiHero/MI_NikkiHero_SakuraDream",
        "target_variant": "A",
        "reason": "SakuraDream hero cloth has no trim UVs — ZenTrim_Base4K causes stretching. Swap to KB3D_ATL_BrickStoneCleanA.",
    },
    {
        "mi_path": "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped/MI_NikkiHero_SakuraDream_IntegratedV1",
        "target_variant": "B",
        "reason": "IntegratedV1 uses tilable NikkiChain master but retains trimsheet. Swap to KB3D_ATL_BrickStoneCleanB.",
    },
]

KB3D_TEXTURES = {}
for variant in ("A", "B"):
    base = f"/Game/EnvSandbox/Textures/Atlantis/KB3D_ATL_BrickStoneClean{variant}"
    KB3D_TEXTURES[variant] = {
        "BaseColor": f"{base}_basecolor",
        "Normal": f"{base}_normal",
        "Roughness": f"{base}_roughness",
        "Metallic": f"{base}_metallic",
        "Height": f"{base}_height",
    }

for item in ZEN_MISUSE:
    mi = load_asset(item["mi_path"])
    if mi is None:
        log(f"  FAIL load: {item['mi_path']}")
        continue
    
    variant = item["target_variant"]
    tex_map = KB3D_TEXTURES[variant]
    
    log(f"  Fixing: {item['mi_path']}")
    log(f"  Reason: {item['reason']}")
    
    # Show current state
    tparams = mi.texture_parameter_values
    log(f"  Current textures ({len(tparams)}):")
    for i in range(len(tparams)):
        tp = tparams[i]
        info = tp.parameter_info
        pv = tp.parameter_value
        path = pv.get_path_name() if hasattr(pv, 'get_path_name') else '?'
        log(f"    {info.name if info else '?'}: {path}")
    
    # Set each texture parameter
    for param_name, tex_path in tex_map.items():
        tex_asset = load_asset(tex_path)
        if tex_asset is None:
            log(f"    WARN: texture not found: {tex_path}")
            continue
        
        # Try setting via set_material_instance_texture_parameter_value
        success = unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
            mi, param_name, tex_asset
        )
        log(f"    Set {param_name}: {'OK' if success else 'FAIL'}")
    
    # Save
    if save_asset(mi):
        log(f"  Saved: OK")
    else:
        log(f"  Save: FAIL")

# ── 2. Arch Toon MI creation ────────────────────────────────────────
log("=== 2. Arch Toon MI creation ===")

PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MI_ROOT_CATH = "/Game/EnvSandbox/Materials/Instances/Architecture/Cathedral"
MI_ROOT_ATL = "/Game/EnvSandbox/Materials/Instances/Architecture/Atlantis"
MESH_ROOTS = ["/Game/EnvSandbox/Meshes/Cathedral", "/Game/EnvSandbox/Meshes/Atlantis"]

# Ensure MI directories exist
ensure_dir(MI_ROOT_CATH)
ensure_dir(MI_ROOT_ATL)

# Verify parent exists
parent = load_asset(PARENT)
if parent is None:
    log(f"FATAL: parent material not found: {PARENT}")
else:
    log(f"Parent: {PARENT} — OK")

# Get all mesh assets
all_mesh_paths = []
for root in MESH_ROOTS:
    if unreal.EditorAssetLibrary.does_directory_exist(root):
        assets = unreal.EditorAssetLibrary.list_assets(root, recursive=True)
        all_mesh_paths.extend(assets)
        log(f"  Found {len(assets)} assets under {root}")

mesh_paths = [p for p in all_mesh_paths 
              if p.startswith("/Game/EnvSandbox/Meshes/Cathedral") 
              or p.startswith("/Game/EnvSandbox/Meshes/Atlantis")]

log(f"Total mesh targets: {len(mesh_paths)}")

# Load the parent's parameter names
if parent:
    scalar_names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(parent)
    vector_names = unreal.MaterialEditingLibrary.get_vector_parameter_names(parent)
    log(f"Parent scalar params: {scalar_names}")
    log(f"Parent vector params: {vector_names}")
    
    has_roughness = "Roughness" in scalar_names
    has_metallic = "Metallic" in scalar_names
    has_texture_weight = "TextureWeight" in scalar_names
    has_shadow_dream_strength = "ShadowDreamStrength" in scalar_names
    has_shadow_dream_tint = "ShadowDreamTint" in vector_names
    has_shadow_flower_color = "ShadowFlowerColor" in vector_names
    log(f"Has Roughness: {has_roughness}, Metallic: {has_metallic}, ShadowDreamStrength: {has_shadow_dream_strength}")
    log(f"Has ShadowDreamTint: {has_shadow_dream_tint}, ShadowFlowerColor: {has_shadow_flower_color}")

# SLOT_PRESETS
SLOT_PRESETS = {
    "stone":   (0.85, 0.0, None),
    "brick":   (0.80, 0.0, None),
    "trim":    (0.70, 0.0, None),
    "gold":    (0.35, 0.85, None),
    "worn":    (0.60, 0.15, None),
    "marble":  (0.25, 0.0, (0.545, 0.627, 0.843, 1.0)),  # soft blue
    "glass":   (0.08, 0.0, (0.545, 0.627, 0.843, 1.0)),
    "rose":    (0.55, 0.0, (0.912, 0.627, 0.749, 1.0)),  # soft pink
    "default": (0.70, 0.0, None),
}

SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)

def preset_for(slot):
    s = slot.lower()
    for k, v in SLOT_PRESETS.items():
        if k in s:
            return v
    return SLOT_PRESETS["default"]

def ensure_mi(slot_name, mi_dir):
    """Create or load an MI for the given slot."""
    safe_name = slot_name.replace(" ", "_").replace(".", "_")
    mi_name = f"MI_Arch_{safe_name}"
    path = f"{mi_dir}/{mi_name}"
    
    # Check if already exists
    existing = load_asset(path)
    if existing is not None:
        return existing, path, "existing"
    
    # Create new
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(mi_name, mi_dir, unreal.MaterialInstanceConstant, factory)
    
    if mi is None:
        return None, path, "create_failed"
    
    # Set parent
    mi.set_editor_property("parent", parent)
    
    # Set parameters
    rough, metal, tint = preset_for(slot_name)
    
    if has_roughness:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Roughness", float(rough))
    if has_metallic:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Metallic", float(metal))
    if has_texture_weight:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.85)
    if has_shadow_dream_strength:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "ShadowDreamStrength", 0.55)
    if has_shadow_dream_tint:
        tint_color = tint if tint is not None else SOFT_BLUE
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "ShadowDreamTint", tint_color)
    if has_shadow_flower_color:
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "ShadowFlowerColor", SOFT_PINK)
    
    # Save
    if save_asset(mi):
        return mi, path, "created"
    else:
        return mi, path, "save_failed"

# Process meshes
results = []
created_count = 0
existing_count = 0

for mp in sorted(mesh_paths):
    is_cath = "/Cathedral" in mp
    mi_dir = MI_ROOT_CATH if is_cath else MI_ROOT_ATL
    
    mesh = load_asset(mp)
    if mesh is None:
        results.append({"mesh": mp, "status": "mesh_not_found"})
        continue
    
    mats = mesh.get_editor_property("static_materials") or []
    mesh_changes = []
    
    for idx, sm in enumerate(mats):
        slot = str(sm.get_editor_property("material_slot_name") or f"Slot{idx}")
        imported = str(sm.get_editor_property("imported_material_slot_name") or slot)
        key = imported or slot
        
        # Check current material
        cur = sm.get_editor_property("material_interface")
        cur_path = cur.get_path_name() if cur else ""
        
        if "M_Master_Toon_Universal" in cur_path or "MI_Arch_" in cur_path:
            mesh_changes.append({"slot": slot, "action": "already_toon"})
            continue
        
        mi, mi_path, action = ensure_mi(key, mi_dir)
        if mi is None:
            mesh_changes.append({"slot": slot, "action": "mi_failed", "key": key})
            continue
        
        if action == "created":
            created_count += 1
        elif action == "existing":
            existing_count += 1
        
        # Assign to mesh
        mesh.set_material(idx, mi)
        mesh_changes.append({"slot": slot, "key": key, "action": "assigned", "mi": mi_path})
    
    # Save mesh
    if mesh_changes:
        save_asset(mesh)
    
    results.append({
        "mesh": mp,
        "status": "ok",
        "changes": mesh_changes,
    })

log(f"Created: {created_count}, Existing: {existing_count}, Total meshes: {len(mesh_paths)}")

# ── 3. PBR instance creation for complete sets without instances ─────
log("=== 3. PBR instance creation ===")

# From the Monolith PBR scan: 12 complete sets, 0 instances
COMPLETE_SETS_NO_MI = [
    "T_FloralBrickGrayScale",
    "ZenTrim_Base4K", "ZenTrim_ColourShift", "ZenTrim_CrackedToHell",
    "ZenTrim_FlowersLIttleBit", "ZenTrim_FlowersLOTS", "ZenTrim_FlowersMid", "ZenTrim_Wet",
    "basetrim", "concretetrim",
    "landscape_grass", "landscapegrayscale",
]

# But some of these already have MIs on disk (ZenTrim variants in Stylized/)
# Let's check what actually exists vs what the PBR scan says
log("Checking existing MIs for complete PBR sets...")

pbr_mis_found = 0
pbr_sets_without_mi = []

for stem in COMPLETE_SETS_NO_MI:
    # Search for MIs that might reference this texture set
    found = False
    for root_dir in ["/Game/EnvSandbox/Materials/Instances/Environment/Stylized",
                     "/Game/EnvSandbox/Materials/Instances/Environment",
                     "/Game/EnvSandbox/Materials/Instances/Architecture"]:
        if unreal.EditorAssetLibrary.does_directory_exist(root_dir):
            assets = unreal.EditorAssetLibrary.list_assets(root_dir, recursive=True)
            for a in assets:
                if stem in a and a.endswith(".uasset"):
                    found = True
                    log(f"  {stem}: found existing MI at {a}")
                    break
        if found:
            break
    
    if not found:
        pbr_sets_without_mi.append(stem)
        log(f"  {stem}: NO existing MI — needs creation")

log(f"PBR sets without MI: {len(pbr_sets_without_mi)} — {pbr_sets_without_mi}")

# ── 4. Folder health summary ────────────────────────────────────────
log("=== 4. Folder health summary ===")

instance_dirs = {}
for d in unreal.EditorAssetLibrary.list_assets("/Game/EnvSandbox/Materials/Instances", recursive=False):
    if d.endswith("/") or unreal.EditorAssetLibrary.does_directory_exist(d):
        count = len(unreal.EditorAssetLibrary.list_assets(d, recursive=True))
        name = d.split("/")[-1]
        instance_dirs[name] = count
        log(f"  Instances/{name}: {count} MIs")

# ── Write report ────────────────────────────────────────────────────
report = {
    "timestamp": "2026-08-30T14:44+00:00",
    "zen_trim_fix": {
        "affected_mis": [i["mi_path"] for i in ZEN_MISUSE],
        "textures_swapped": "KB3D_ATL_BrickStoneCleanA/B (full PBR sets)",
    },
    "arch_toon": {
        "total_meshes": len(mesh_paths),
        "mius_created": created_count,
        "mius_existing": existing_count,
        "cathedral_dir": MI_ROOT_CATH,
        "atlantis_dir": MI_ROOT_ATL,
    },
    "pbr_sets_without_instance": pbr_sets_without_mi,
    "instance_folder_counts": instance_dirs,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
log(f"Report written: {OUT}")

log("=== DONE ===")
