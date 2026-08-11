"""Execute niagara polish in-editor."""
import unreal

def set_fixed_bounds(system_path, name):
    ns = unreal.load_asset(system_path)
    if not ns:
        print(f"{name}: NOT FOUND")
        return
    try:
        # Fixed bounds might be under a different name
        # Try to find the right property
        props = ["fixed_bounds", "bFixedBounds", "FixedBounds", "use_fixed_bounds", "CalculateBoundsMode"]
        for pn in props:
            try:
                v = ns.get_editor_property(pn)
                print(f"  {name}: {pn} = {v} ({type(v).__name__})")
            except:
                pass
    except Exception as ex:
        print(f"  {name}: error reading props: {str(ex)[:100]}")

def assign_material(system_path, emitter_index, material_path, name):
    """Assign material to a Niagara system's renderer via direct emitter handle access."""
    try:
        # Try to use the emitter handle
        handles = ns.get_editor_property("emitter_handles")  # This might exist in 5.8
        if handles and len(handles) > emitter_index:
            em = handles[emitter_index]
            renderers = em.get_editor_property("renderer_properties") or []
            for r in renderers:
                mat = unreal.load_asset(material_path)
                if mat:
                    r.set_editor_property("material", mat)
                    print(f"  {name}: material assigned to renderer")
    except:
        pass

# ── Step 1: Read system properties to find fixed bounds ────────────────
print("=== Checking system properties ===")
systems = [
    "/Game/EnvSandbox/VFX/Systems/Ambient/NS_ConstellationTwinkle",
    "/Game/EnvSandbox/VFX/Systems/Universal/NS_Uni_GroundWisps",
    "/Game/EnvSandbox/VFX/Systems/Sakura/NS_SakuraDreamSparkle",
]
for sp in systems:
    name = sp.split("/")[-1]
    ns = unreal.load_asset(sp)
    if ns:
        print(f"\n--- {name} ---")
        # Try accessing emitters via get_editor_property with different names
        for prop_name in ["EmitterHandles", "emitter_handles", "EmitterCompressedData"]:
            try:
                v = ns.get_editor_property(prop_name)
                print(f"  {prop_name}: {type(v).__name__} len={len(v) if hasattr(v, '__len__') else '?'}")
            except:
                pass
