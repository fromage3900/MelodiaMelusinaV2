
import unreal

PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MI_ROOT_CATH = "/Game/EnvSandbox/Materials/Instances/Architecture/Cathedral"
MI_ROOT_ATL = "/Game/EnvSandbox/Materials/Instances/Architecture/Atlantis"

SOFT_BLUE = unreal.LinearColor(0.545, 0.627, 0.843, 1.0)
SOFT_PINK = unreal.LinearColor(0.912, 0.627, 0.749, 1.0)

SLOT_PRESETS = {
    "stone": (0.85, 0.0, None),
    "brick": (0.80, 0.0, None),
    "trim": (0.70, 0.0, None),
    "gold": (0.35, 0.85, None),
    "worn": (0.60, 0.15, None),
    "marble": (0.25, 0.0, SOFT_BLUE),
    "glass": (0.08, 0.0, SOFT_BLUE),
    "rose": (0.55, 0.0, SOFT_PINK),
    "default": (0.70, 0.0, None),
}

def preset_for(slot):
    s = slot.lower()
    for k, v in SLOT_PRESETS.items():
        if k in s:
            return v
    return SLOT_PRESETS["default"]

def ensure_dir(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
        print(f"  Created dir: {path}")

def ensure_mi(slot_name, mi_dir):
    safe = slot_name.replace(" ", "_").replace(".", "_")
    mi_name = f"MI_Arch_{safe}"
    path = f"{mi_dir}/{mi_name}"
    existing = unreal.load_asset(path)
    if existing:
        return existing, path, "existing"
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialInstanceConstantFactoryNew()
    mi = tools.create_asset(mi_name, mi_dir, unreal.MaterialInstanceConstant, factory)
    if not mi:
        return None, path, "create_failed"
    mi.set_editor_property("parent", parent)
    rough, metal, tint = preset_for(slot_name)
    for nm, val in [("Roughness", float(rough)), ("Metallic", float(metal))]:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, nm, val)
        except: pass
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "TextureWeight", 0.85)
    except: pass
    try:
        unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "ShadowDreamStrength", 0.55)
    except: pass
    if tint:
        try:
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "ShadowDreamTint", tint)
        except: pass
    try:
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "ShadowFlowerColor", SOFT_PINK)
    except: pass
    saved = unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi, path, "created" if saved else "save_failed"

# Ensure dirs
for d in [MI_ROOT_CATH, MI_ROOT_ATL]:
    ensure_dir(d)

# Parent
parent = unreal.load_asset(PARENT)
print(f"Parent: {'OK' if parent else 'MISSING'}")

# Collect meshes
mesh_paths = []
for root in [("/Game/EnvSandbox/Meshes/Cathedral", MI_ROOT_CATH),
             ("/Game/EnvSandbox/Meshes/Atlantis", MI_ROOT_ATL)]:
    if unreal.EditorAssetLibrary.does_directory_exist(root[0]):
        for a in unreal.EditorAssetLibrary.list_assets(root[0], recursive=True):
            if a.endswith(".uasset"):
                mesh_paths.append((a, root[1]))

print(f"Mesh targets: {len(mesh_paths)}")

created = 0
existing = 0
assigned = 0
failed = 0

for idx, (mp, mi_dir) in enumerate(mesh_paths):
    if idx % 50 == 0:
        print(f"  Progress: {idx}/{len(mesh_paths)}")
    mesh = unreal.load_asset(mp)
    if not mesh:
        failed += 1
        continue
    mats = mesh.get_editor_property("static_materials") or []
    for si, sm in enumerate(mats):
        slot = str(sm.get_editor_property("material_slot_name") or f"Slot{si}")
        imported = str(sm.get_editor_property("imported_material_slot_name") or slot)
        key = imported or slot
        cur = sm.get_editor_property("material_interface")
        cur_path = cur.get_path_name() if cur else ""
        if "M_Master_Toon_Universal" in cur_path or "MI_Arch_" in cur_path:
            continue
        mi, mipath, action = ensure_mi(key, mi_dir)
        if not mi:
            failed += 1
            continue
        if action == "created": created += 1
        elif action == "existing": existing += 1
        mesh.set_material(si, mi)
        assigned += 1
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)

print(f"\nResults: created={created}, existing={existing}, assigned_slots={assigned}, failed_meshes={failed}")
print(f"Total meshes processed: {len(mesh_paths)}")
