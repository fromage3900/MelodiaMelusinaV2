"""Stage cooked reef assets into the game content tree (EnvSandbox).

Copies import-ready files from the audit dirs into:
  Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures/
  Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes/

Copies only (no .uasset fabrication - the editor import step belongs to the
holder, per IMPORT_QUEUE.md). Every staged file is sha256-verified against its
audit source and recorded in stage_manifest.json.

Run:  python Tools/Houdini/sea_above_reef/stage_to_sandbox.py
"""

import json
import shutil
from pathlib import Path

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))

import reef_common as rc  # noqa: E402

# not imported from build_clutter_meshes - that module imports hou (hython-only)
MESH_OUT_DIR = rc.PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "meshes"

CONTENT_ROOT = rc.PROJECT_ROOT / "Content" / "EnvSandbox" / "Monoliths" / "SeaAbove" / "Prototype" / "Reef"
TEX_OUT = CONTENT_ROOT / "Textures"
MESH_OUT = CONTENT_ROOT / "Meshes"

TEXTURES = [
    # sand material suite + caustics
    "T_SeaAbove_Sand_Albedo", "T_SeaAbove_Sand_Height", "T_SeaAbove_Sand_Normal",
    "T_SeaAbove_Sand_WetMask", "T_SeaAbove_Sand_RippleMask", "T_SeaAbove_Caustics",
    # shell masks
    "T_SeaAbove_ShellMask_Nautilus", "T_SeaAbove_ShellMask_Scallop",
    "T_SeaAbove_ShellMask_Conch", "T_SeaAbove_ShellMask_SandDollar",
    # clutter
    "T_SeaAbove_Clutter_Atlas", "T_SeaAbove_ClutterFloor_Mask",
    # coral skin
    "T_SeaAbove_CoralSkin_Albedo", "T_SeaAbove_CoralSkin_Normal",
    "T_SeaAbove_CoralSkin_EmissiveMask",
    # kelp sway LUT (R3; half-wrap: U=time loop, V=height clamps)
    "T_SeaAbove_KelpSway_LUT",
    # jellyfish surreal LUTs (R6)
    "T_Jelly_ArmLogic_LUT", "T_Jelly_Biolum_LUT",
    # jellyfish lookdev v2 (iridescence + veil)
    "T_Jelly_Bell_BaseColor", "T_Jelly_Bell_Normal", "T_Jelly_Bell_Opacity",
    "T_Jelly_Bell_CanalMask", "T_Jelly_Bell_Irid_Mottle",
    "T_Jelly_Iridescence_LUT", "T_Jelly_Nematocyst_Glints",
    # leviathan + drowned organ (owner wonders)
    "T_Leviathan_Bone_BaseColor", "T_Leviathan_Bone_Normal", "T_Leviathan_Bone_Roughness",
    "T_Organ_Pipe_BaseColor", "T_Organ_Pipe_Normal", "T_Organ_Pipe_Emissive",
    # leviathan + drowned organ (owner wonders)
    "T_Leviathan_Bone_BaseColor", "T_Leviathan_Bone_Normal", "T_Leviathan_Bone_Roughness",
    "T_Organ_Pipe_BaseColor", "T_Organ_Pipe_Normal", "T_Organ_Pipe_Emissive",
    # volumetrics (R-dreams: UE Sparse Volume Textures)
    "__VOLUMES_ARE_STAGED_SEPARATELY__",
    # R5 texture suite v2
    "T_SeaAbove_Droplet_Atlas", "T_SeaAbove_Membrane_Reveal", "T_SeaAbove_Membrane_Ripple_N",
    "T_SeaAbove_WetRock_Albedo", "T_SeaAbove_WetRock_Normal", "T_SeaAbove_WetRock_Wetline",
    "T_SeaAbove_BarnacleCrust_Mask", "T_SeaAbove_PulseBand_LUT",
    "T_SeaAbove_Foam_Mask", "T_SeaAbove_Sediment_Ramp",
]
MESHES = [
    # clutter (build_clutter_meshes.py)
    "SM_Clutter_PebbleSet", "SM_Clutter_Starfish", "SM_Clutter_SpiralShell",
    "SM_Clutter_SeaWeed",
    # coral (build_coral_generator.py)
    "SM_Coral_Staghorn", "SM_Coral_Table", "SM_Coral_TubeSponges",
    "SM_Coral_Fan", "SM_Coral_Brain", "SM_Coral_ReefCluster",
    # kelp (build_kelp_vat.py)
    "SM_Kelp_Tall", "SM_Kelp_Mid", "SM_Kelp_Cluster",
    # islands (build_island_generator.py)
    "SM_Island_A", "SM_Island_B", "SM_Island_C", "SM_RockChunk_M", "SM_RockChunk_L",
    # leviathan + drowned organ (owner wonders)
    "SM_Leviathan", "SM_DrownedOrgan",
    # dream flora (code-L-system)
    "SM_Flora_Reed", "SM_Flora_Chime", "SM_Flora_Fern",
]
MESH_FBX = ["SM_Banner", "SM_Shroud", "SM_Starskiff_MK2", "SK_ShorewakeDress"]
VDB_VOLUMES = ["VOL_GodRays", "VOL_GhostFog", "VOL_NebulaVeil"]


def stage(names, src_dir, dst_dir, exts, entries, kind):
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        for ext in exts:
            src = src_dir / f"{name}{ext}"
            if not src.exists():
                print(f"[stage] MISSING source: {src.name} (skipping)")
                continue
            dst = dst_dir / src.name
            try:
                shutil.copy2(src, dst)
            except PermissionError:
                entries.append({"file": str(dst.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
                                "source": str(src.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
                                "locked": True, "kind": kind,
                                "note": "destination write-locked (editor/viewer open?) - "
                                        "re-run staging when free"})
                print(f"[stage] LOCKED, skipped: {dst.name}")
                continue
            src_hash = rc.sha256_of(src)
            dst_hash = rc.sha256_of(dst)
            ok = src_hash == dst_hash
            entries.append({
                "file": str(dst.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
                "source": str(src.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
                "bytes": dst.stat().st_size,
                "sha256": dst_hash,
                "verified": ok,
                "kind": kind,
            })
            print(f"[stage] {src.name} -> {dst.relative_to(rc.PROJECT_ROOT)} "
                  f"({'hash OK' if ok else 'HASH MISMATCH'})")


def main():
    tex_entries, mesh_entries = [], []
    TEXTURES[:] = [t for t in TEXTURES if not t.startswith("__")]
    stage(TEXTURES, rc.OUT_DIR, TEX_OUT, [".png"], tex_entries, "texture")
    stage(MESHES, MESH_OUT_DIR, MESH_OUT, [".obj"], mesh_entries, "mesh_obj")
    stage(MESH_FBX, MESH_OUT_DIR, MESH_OUT, [".fbx"], mesh_entries, "mesh_fbx")
    stage(VDB_VOLUMES,
          rc.PROJECT_ROOT / "Saved/Audit/sea_above/volumes",
          CONTENT_ROOT / "Volumes", [".vdb"], mesh_entries, "volume_vdb_svt")
    # jellyfish ships as FBX with morph targets (Blender-exported; Apprentice cannot)
    stage(["JELLY_Bell", "JELLY_Arms"], MESH_OUT_DIR, MESH_OUT, [".fbx"],
          mesh_entries, "mesh_fbx_morphs")

    payload = {
        "schema": "melodia.sea_above_reef_stage.v1",
        "staged_root": str(CONTENT_ROOT.relative_to(rc.PROJECT_ROOT)).replace("\\", "/"),
        "note": "raw assets staged for editor import; .uasset creation is the "
                "editor holder's step (IMPORT_QUEUE.md). bgeo.sc copies stay in "
                "Saved/Audit for a future Engine-license import path.",
        "textures": tex_entries,
        "meshes": mesh_entries,
    }
    out = CONTENT_ROOT / "stage_manifest.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    bad = [e for e in tex_entries + mesh_entries
           if e.get("verified") is False and not e.get("locked")]
    print(f"[stage] {len(tex_entries)} textures + {len(mesh_entries)} meshes staged "
          f"-> {out}")
    print(f"[stage] hash verification: {len(tex_entries) + len(mesh_entries) - len(bad)}"
          f"/{len(tex_entries) + len(mesh_entries)} OK")
    if bad:
        for e in bad:
            print(f"[stage] MISMATCH: {e['file']}")


if __name__ == "__main__":
    main()
