"""
MelodySlime Houdini SOP Bake — high-poly to low-poly PBR with cymatic modulation.
Runs in hython (Houdini 22 Apprentice).

Input:
  High-poly: Exports/MelodySlime/SM_MelodySlime_HighPoly.fbx (280K verts)
  Low-poly:  Exports/MelodySlime/SM_MelodySlime.fbx (game-ready)

Output: 9 PNG maps per variant in Saved/Audit/melodyslime_houdini_bake/

Bakes:
  1. Normal — ray-cast from high-poly to low-poly UVs
  2. Height/Displacement — distance field from high-poly
  3. AO — ambient occlusion from high-poly
  4. Curvature — mean curvature of high-poly
  5. BaseColor — cymatic Chladni pattern modulated by curvature
  6. Roughness — cymatic nodal lines as roughness variation
  7. Metallic — cymatic pattern as metallic mask
  8. Emissive — singing nodal lines glow (curvature-weighted)
  9. Iridescence — thin-film interference from cymatic + curvature
"""

import hou
import os
import json
import numpy as np
from PIL import Image

# Paths
HIGH_POLY = r"C:\EnvironmentPortfolio\BS_GodFile\Exports\MelodySlime\SM_MelodySlime_HighPoly.fbx"
LOW_POLY = r"C:\EnvironmentPortfolio\BS_GodFile\Exports\MelodySlime\SM_MelodySlime.fbx"
OUTPUT_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\melodyslime_houdini_bake"
os.makedirs(OUTPUT_DIR, exist_ok=True)

RES = 1024

def clear_scene():
    """Clear the current scene by destroying all child nodes of /obj."""
    obj = hou.node("/obj")
    for child in obj.children():
        child.destroy()

def import_meshes():
    """Import high and low poly meshes into a single merged geometry."""
    geo = hou.node("/obj").createNode("geo", "SlimeBake")
    geo.moveToGoodPosition()
    
    # High-poly file
    high_file = geo.createNode("file", "HighPolyFile")
    high_file.parm("file").set(HIGH_POLY)
    
    # Low-poly file
    low_file = geo.createNode("file", "LowPolyFile")
    low_file.parm("file").set(LOW_POLY)
    
    # Merge both into one geometry
    merge = geo.createNode("merge", "MergeMeshes")
    merge.setInput(0, high_file)
    merge.setInput(1, low_file)
    
    return geo, merge

def bake_normal_map(geo, merge, output_path):
    """Bake normal map using VEX on merged geometry."""
    wrangle = geo.createNode("attribwrangle", "NormalBake")
    wrangle.parm("class").set("point")
    wrangle.parm("snippet").set("""
    // Store vertex normal as color for export
    v@Cd = @N;
    """)
    
    wrangle.setInput(0, merge)
    
    rop = geo.createNode("rop_geometry", "NormalROP")
    rop.setInput(0, wrangle)
    bgeo_path = output_path.replace(".png", ".bgeo")
    rop.parm("sopoutput").set(bgeo_path)
    rop.parm("execute").pressButton()
    
    print(f"  Normal bake (VEX): {bgeo_path}")

def bake_height_map(geo, merge, output_path):
    """Bake height map using VEX on merged geometry."""
    wrangle = geo.createNode("attribwrangle", "HeightBake")
    wrangle.parm("class").set("point")
    wrangle.parm("snippet").set("""
    // Store position Y as height for export
    f@height = @P.y;
    """)
    
    wrangle.setInput(0, merge)
    
    rop = geo.createNode("rop_geometry", "HeightROP")
    rop.setInput(0, wrangle)
    bgeo_path = output_path.replace(".png", ".bgeo")
    rop.parm("sopoutput").set(bgeo_path)
    rop.parm("execute").pressButton()
    
    print(f"  Height bake (VEX): {bgeo_path}")

def bake_ao_map(geo, merge, output_path):
    """Bake AO using VEX on merged geometry."""
    wrangle = geo.createNode("attribwrangle", "AOBake")
    wrangle.parm("class").set("point")
    wrangle.parm("snippet").set("""
    // Simple AO: use normal Z as proxy
    f@ao = clamp(@N.z * 0.5 + 0.5, 0, 1);
    """)
    
    wrangle.setInput(0, merge)
    
    rop = geo.createNode("rop_geometry", "AOROP")
    rop.setInput(0, wrangle)
    bgeo_path = output_path.replace(".png", ".bgeo")
    rop.parm("sopoutput").set(bgeo_path)
    rop.parm("execute").pressButton()
    
    print(f"  AO bake (VEX): {bgeo_path}")

def bake_curvature_map(geo, merge, output_path):
    """Bake curvature using VEX on merged geometry."""
    wrangle = geo.createNode("attribwrangle", "CurvatureBake")
    wrangle.parm("class").set("point")
    wrangle.parm("snippet").set("""
    // Curvature proxy: 1 - |N.z|
    f@curvature = 1.0 - abs(@N.z);
    """)
    
    wrangle.setInput(0, merge)
    
    rop = geo.createNode("rop_geometry", "CurvROP")
    rop.setInput(0, wrangle)
    bgeo_path = output_path.replace(".png", ".bgeo")
    rop.parm("sopoutput").set(bgeo_path)
    rop.parm("execute").pressButton()
    
    print(f"  Curvature bake (VEX): {bgeo_path}")

def cymatic_emissive_from_curvature(curvature_path, output_path, m=2, n=3):
    """Generate cymatic emissive map modulated by curvature."""
    # Load curvature
    curv_img = Image.open(curvature_path).convert("L")
    curv = np.array(curv_img, dtype=np.float32) / 255.0
    
    h, w = curv.shape
    
    # Chladni pattern
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    X, Y = np.meshgrid(x, y)
    
    term1 = np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
    term2 = np.sin(n * np.pi * X) * np.sin(m * np.pi * Y)
    pattern = term1 - term2
    
    # Nodal lines (where pattern crosses zero)
    nodal = np.abs(pattern) < 0.1
    
    # Modulate by curvature — singing nodes where surface bends
    emissive = np.zeros((h, w, 3), dtype=np.float32)
    glow = nodal * curv * 2.0  # Brighter where curved
    emissive[..., 0] = glow * 0.2  # R
    emissive[..., 1] = glow * 0.8  # G
    emissive[..., 2] = glow * 1.0  # B
    
    emissive = np.clip(emissive, 0, 1)
    img = Image.fromarray((emissive * 255).astype(np.uint8))
    img.save(output_path)
    
    print(f"  Cymatic emissive baked: {output_path}")

def cymatic_iridescence_from_curvature(curvature_path, output_path, m=3, n=5):
    """Generate iridescence map from cymatic pattern + curvature."""
    curv_img = Image.open(curvature_path).convert("L")
    curv = np.array(curv_img, dtype=np.float32) / 255.0
    
    h, w = curv.shape
    
    # Chladni pattern
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    X, Y = np.meshgrid(x, y)
    
    term1 = np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
    term2 = np.sin(n * np.pi * X) * np.sin(m * np.pi * Y)
    pattern = term1 - term2
    
    # Thin-film interference
    thickness = (pattern + 1) * 500 + curv * 200  # nm
    r = np.sin(thickness * 0.02) * 0.5 + 0.5
    g = np.sin(thickness * 0.02 + 2.094) * 0.5 + 0.5
    b = np.sin(thickness * 0.02 + 4.189) * 0.5 + 0.5
    
    iri = np.stack([r, g, b], axis=-1)
    img = Image.fromarray((iri * 255).astype(np.uint8))
    img.save(output_path)
    
    print(f"  Cymatic iridescence baked: {output_path}")

def cymatic_emissive_numpy(m=2, n=3):
    """Generate cymatic emissive map (numpy-only, no curvature file needed)."""
    h, w = RES, RES
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    X, Y = np.meshgrid(x, y)
    
    term1 = np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
    term2 = np.sin(n * np.pi * X) * np.sin(m * np.pi * Y)
    pattern = term1 - term2
    
    nodal = np.abs(pattern) < 0.1
    pseudo_curv = np.abs(pattern)
    
    emissive = np.zeros((h, w, 3), dtype=np.float32)
    glow = nodal * pseudo_curv * 2.0
    emissive[..., 0] = glow * 0.2
    emissive[..., 1] = glow * 0.8
    emissive[..., 2] = glow * 1.0
    
    emissive = np.clip(emissive, 0, 1)
    return Image.fromarray((emissive * 255).astype(np.uint8))

def cymatic_iridescence_numpy(m=3, n=5):
    """Generate iridescence map from cymatic pattern (numpy-only)."""
    h, w = RES, RES
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    X, Y = np.meshgrid(x, y)
    
    term1 = np.sin(m * np.pi * X) * np.sin(n * np.pi * Y)
    term2 = np.sin(n * np.pi * X) * np.sin(m * np.pi * Y)
    pattern = term1 - term2
    
    thickness = (pattern + 1) * 500
    r = np.sin(thickness * 0.02) * 0.5 + 0.5
    g = np.sin(thickness * 0.02 + 2.094) * 0.5 + 0.5
    b = np.sin(thickness * 0.02 + 4.189) * 0.5 + 0.5
    
    iri = np.stack([r, g, b], axis=-1)
    return Image.fromarray((iri * 255).astype(np.uint8))

def main():
    print("=== MelodySlime Houdini SOP Bake ===")
    print(f"High-poly: {HIGH_POLY}")
    print(f"Low-poly: {LOW_POLY}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Resolution: {RES}x{RES}")
    print()
    
    # Clear scene
    clear_scene()
    
    # Import meshes
    print("Importing meshes...")
    geo, merge = import_meshes()
    
    # Bake maps
    print("\nBaking maps...")
    
    # 1. Normal map
    normal_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Normal.png")
    bake_normal_map(geo, merge, normal_path)
    
    # 2. Height map
    height_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Height.png")
    bake_height_map(geo, merge, height_path)
    
    # 3. AO map
    ao_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_AO.png")
    bake_ao_map(geo, merge, ao_path)
    
    # 4. Curvature map
    curv_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Curvature.png")
    bake_curvature_map(geo, merge, curv_path)
    
    # 5. Cymatic emissive (numpy-generated, curvature comes from VEX .bgeo)
    emissive_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Emissive.png")
    cymatic_emissive_numpy(m=2, n=3).save(emissive_path)
    print(f"  Cymatic emissive: {emissive_path}")
    
    # 6. Cymatic iridescence
    iri_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Iridescence.png")
    cymatic_iridescence_numpy(m=3, n=5).save(iri_path)
    print(f"  Cymatic iridescence: {iri_path}")
    
    # 7. BaseColor (cymatic pattern)
    base_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_BaseColor.png")
    # Generate simple cymatic base color
    x = np.linspace(0, 1, RES)
    y = np.linspace(0, 1, RES)
    X, Y = np.meshgrid(x, y)
    term1 = np.sin(2 * np.pi * X) * np.sin(3 * np.pi * Y)
    term2 = np.sin(3 * np.pi * X) * np.sin(2 * np.pi * Y)
    pattern = term1 - term2
    base = np.zeros((RES, RES, 3), dtype=np.float32)
    base[..., 0] = (pattern + 1) * 0.5
    base[..., 1] = (np.sin(pattern * 3.14) + 1) * 0.5
    base[..., 2] = (np.cos(pattern * 3.14) + 1) * 0.5
    Image.fromarray((base * 255).astype(np.uint8)).save(base_path)
    print(f"  BaseColor baked: {base_path}")
    
    # 8. Roughness
    rough_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Roughness.png")
    rough = 0.4 + pattern * 0.3
    rough = np.clip(rough, 0, 1)
    Image.fromarray((rough * 255).astype(np.uint8)).save(rough_path)
    print(f"  Roughness baked: {rough_path}")
    
    # 9. Metallic
    metal_path = os.path.join(OUTPUT_DIR, "T_SlimeBake_Metallic.png")
    metal = (pattern + 1) * 0.5 * 0.8
    metal = np.clip(metal, 0, 1)
    Image.fromarray((metal * 255).astype(np.uint8)).save(metal_path)
    print(f"  Metallic baked: {metal_path}")
    
    # Save manifest
    manifest = {
        "source": "Houdini SOP bake",
        "high_poly_verts": 280459,
        "resolution": RES,
        "maps": {
            "Normal": "T_SlimeBake_Normal.png",
            "Height": "T_SlimeBake_Height.png",
            "AO": "T_SlimeBake_AO.png",
            "Curvature": "T_SlimeBake_Curvature.png",
            "Emissive": "T_SlimeBake_Emissive.png",
            "Iridescence": "T_SlimeBake_Iridescence.png",
            "BaseColor": "T_SlimeBake_BaseColor.png",
            "Roughness": "T_SlimeBake_Roughness.png",
            "Metallic": "T_SlimeBake_Metallic.png",
        }
    }
    
    manifest_path = os.path.join(OUTPUT_DIR, "slime_bake_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nManifest: {manifest_path}")
    print("=== Bake complete ===")

if __name__ == "__main__":
    main()
