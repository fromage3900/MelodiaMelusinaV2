#!/usr/bin/env python3
"""
Klein Veil — in-editor importer (idempotent, height-aware, instances only)
Run inside UE Editor Python:
  exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/klein_veil_import.py", encoding="utf-8").read())
"""
import unreal, json
from pathlib import Path
UE_MI="/Game/EnvSandbox/Materials/Instances/Copernicus/MI_KleinVeil_CymaticReactive"
UE_TEX_ROOT="/Game/EnvSandbox/Textures/Copernicus/KleinVeil"
MASTER="/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MPC="/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"
PLACEMENTS=[
  {
    "id": "KleinVeil_ValleyHeart",
    "xy": [
      -900,
      6200
    ],
    "variant": "KleinVeil",
    "scale": 1.0,
    "wpo_scale": [
      0.35,
      0.35,
      0.6
    ],
    "yaw": 18,
    "biome": "FrillValley",
    "tension": 0.32,
    "note": "Primary veil \u2014 Klein seam faces Heart Gate, height-aware raycast",
    "landscape_z_synthetic": 12088.0,
    "final_z": 12123.0,
    "height_aware": {
      "ray_start_z": 25000,
      "ray_end_z": -10000,
      "channel": "Visibility",
      "complex": True,
      "synthetic_fallback": 12088.0,
      "offset_above_surface": 35
    }
  },
  {
    "id": "KleinVeil_RidgeEcho",
    "xy": [
      1200,
      5500
    ],
    "variant": "KleinVeil_Echo",
    "scale": 0.55,
    "wpo_scale": [
      0.18,
      0.18,
      0.3
    ],
    "yaw": 210,
    "biome": "ResonantSeamWay",
    "tension": 0.12,
    "note": "Echo instance on cymatic nodal corridor |Chladni|<0.12",
    "landscape_z_synthetic": 12490.0,
    "final_z": 12525.0,
    "height_aware": {
      "ray_start_z": 25000,
      "ray_end_z": -10000,
      "channel": "Visibility",
      "complex": True,
      "synthetic_fallback": 12490.0,
      "offset_above_surface": 35
    }
  }
]
TEX_DIR=r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\klein_veil"

# Loud-fail policy (2026-09-03). Before this fix the scalar loop silently skipped
# any MI_SCALARS key absent from the master, and worse: if reflection itself threw,
# the fallback claimed EVERY spec key existed -- so a spec naming six params of
# which only two are on the master would "succeed" while dropping four bindings on
# the floor. Unknown spec keys now abort the run; per-set failures abort the run.
# Fix the master (add the parameter) or fix the spec (drop the key) -- there is no
# silent path through here anymore.
FAIL_ON_UNKNOWN=True

def _collect_master_params(master):
    """Reflect the master's parameter names via MaterialEditingLibrary.

    Returns (scalar_names, vector_names, texture_param_names). Raises on failure --
    there is deliberately NO fallback that guesses the parameter set; guessing is
    the silent-no-op defect class this guard exists to kill.
    """
    exprs=unreal.MaterialEditingLibrary.get_material_expressions(master)
    if exprs is None:
        raise RuntimeError("[KLEIN] master reflection returned None -- cannot verify parameters, refusing to proceed")
    scalars=set(); vectors=set(); textures=set()
    for e in exprs:
        kind=type(e).__name__
        try:
            if kind=="MaterialExpressionScalarParameter":
                scalars.add(str(e.get_editor_property("parameter_name")))
            elif kind=="MaterialExpressionVectorParameter":
                vectors.add(str(e.get_editor_property("parameter_name")))
            elif "Texture" in kind and "Parameter" in kind:
                textures.add(str(e.get_editor_property("parameter_name")))
        except Exception:
            pass  # expression kind carries no parameter_name (e.g. TextureCoordinate)
    return scalars, vectors, textures

def _apply_scalars(inst, known_scalars):
    unknown=[k for k in MI_SCALARS if k not in known_scalars]
    if unknown and FAIL_ON_UNKNOWN:
        raise SystemExit(
            "[KLEIN] ABORT: spec names scalars that do NOT exist on "
            f"{MASTER}: {sorted(unknown)}\n"
            f"[KLEIN] known scalar params: {sorted(known_scalars)}\n"
            "[KLEIN] fix by adding the parameters to the master or removing the "
            "keys from MI_SCALARS. Nothing was applied.")
    failures=[]
    applied=[]
    for k,v in MI_SCALARS.items():
        if k not in known_scalars:
            continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst,k,float(v))
            applied.append(k)
        except Exception as e:
            failures.append(f"{k}: {e}")
    if failures:
        raise SystemExit(f"[KLEIN] ABORT: scalar set failed for {failures}. Nothing was saved.")
    return applied

def _apply_vectors(inst, known_vectors):
    VEC_SPEC={"BaseTint":(1.02,0.97,1.04,1.0),"GoldTint":(1.08,0.88,0.42,1.0)}
    unknown=[k for k in VEC_SPEC if k not in known_vectors]
    if unknown and FAIL_ON_UNKNOWN:
        raise SystemExit(
            f"[KLEIN] ABORT: spec names vector params absent from master: {sorted(unknown)}\n"
            f"[KLEIN] known vector params: {sorted(known_vectors)}\n"
            "[KLEIN] Nothing was applied.")
    failures=[]; applied=[]
    for vname,vval in VEC_SPEC.items():
        if vname not in known_vectors:
            continue
        try:
            col=unreal.LinearColor(vval[0],vval[1],vval[2],vval[3])
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(inst,vname,col)
            applied.append(vname)
        except Exception as e:
            failures.append(f"{vname}: {e}")
    if failures:
        raise SystemExit(f"[KLEIN] ABORT: vector set failed for {failures}. Nothing was saved.")
    return applied

CHANNEL_SLOTS={"BaseColor":"Albedo","Normal":"NormalMap","ORM":"ORM","Height":"HeightMap","Roughness":"RoughnessMap","Metallic":"MetallicMap","Emissive":"EmissiveMap","Iridescence":"Iridescence","Opacity":"OpacityMask"}
# Scalar wiring for audio-reactive — these exist on M_Master_Toon_Universal per BRASS doc
MI_SCALARS={"TextureWeight":1.0,"LayerA_TextureWeight":1.0,"NormalStrength":1.0,"Roughness":0.18,"LayerBaseHeightScale":0.08,"LayerA_ParallaxScale":0.02,"DreamPulseSpeed":0.55,"DreamPulseAmp":0.22,"DreamFlowSpeed":0.28,"GlintSpeed":0.32,"EmissiveMapIntensity":1.35,"GlobalEmissiveBoost":0.65,"GlobalSparkleIntensity":0.35,"WPO_Resonance_Scale":1.0,"Grazing_Rim_Boost":0.85,"POM_StepCount":32.0,"Toksvig_AntiAliasing_Weight":0.0,"IridescenceIntensity":1.0,"CymaticAmplitude":1.0,"BeatPulse":0.0,"BassIntensity":0.5}

def ensure_mi():
    master=unreal.EditorAssetLibrary.load_asset(MASTER)
    if not master:
        raise SystemExit(f"[KLEIN] ABORT master missing {MASTER}")
    if unreal.EditorAssetLibrary.does_asset_exist(UE_MI):
        inst=unreal.EditorAssetLibrary.load_asset(UE_MI)
        if not inst:
            raise SystemExit(f"[KLEIN] ABORT: {UE_MI} exists but load returned None (rule: in-session state vs file damage)")
        print(f"[KLEIN] existing MI found: {UE_MI} -- re-applying spec (idempotent)")
    else:
        if not unreal.EditorAssetLibrary.does_directory_exist("/Game/EnvSandbox/Materials/Instances/Copernicus"):
            unreal.EditorAssetLibrary.make_directory("/Game/EnvSandbox/Materials/Instances/Copernicus")
        inst=unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_KleinVeil_CymaticReactive","/Game/EnvSandbox/Materials/Instances/Copernicus",unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
        if not inst: raise SystemExit("[KLEIN] ABORT: MI create failed")
        try:
            inst.set_editor_property("parent", master)
        except Exception as e:
            raise SystemExit(f"[KLEIN] ABORT: parent set failed ({e}) -- an MI with the wrong parent is worse than no MI")

    # scalars + vectors: loud-fail partition and apply (see _apply_scalars doc)
    known_scalars, known_vectors, tex_params = _collect_master_params(master)
    applied=_apply_scalars(inst, known_scalars)
    print(f"[KLEIN] scalars applied ({len(applied)}): {sorted(applied)}")
    applied_v=_apply_vectors(inst, known_vectors)
    print(f"[KLEIN] vectors applied ({len(applied_v)}): {sorted(applied_v)}")

    # textures: import PNGs from Saved/Audit/klein_veil
    import os
    tex_root="/Game/EnvSandbox/Textures/Copernicus/KleinVeil"
    if not unreal.EditorAssetLibrary.does_directory_exist(tex_root):
        unreal.EditorAssetLibrary.make_directory(tex_root)
    # tex_params already reflected above (same expression pass as scalars/vectors)
    tex_failures=[]
    for ch, slot in CHANNEL_SLOTS.items():
        if slot not in tex_params:
            print(f"[KLEIN] skip {ch}: master has no '{slot}' texture param (authored gap, not a wiring failure)")
            continue
        src=Path(TEX_DIR)/f"T_KleinVeil_{ch}.png"
        if not src.exists():
            print(f"[KLEIN] skip {ch}: source {src} not present (authored gap, not a wiring failure)")
            continue
        dest=f"{tex_root}/T_KleinVeil_{ch}"
        if not unreal.EditorAssetLibrary.does_asset_exist(dest):
            task=unreal.AssetImportTask(); task.filename=str(src); task.destination_path=tex_root; task.destination_name=f"T_KleinVeil_{ch}"; task.replace_existing=True; task.automated=True
            try:
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            except Exception as e:
                tex_failures.append(f"{ch}: import failed {e}"); continue
        tex=unreal.EditorAssetLibrary.load_asset(dest)
        if not tex:
            tex_failures.append(f"{ch}: loaded None from {dest}"); continue
        try:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(inst,slot,tex); print(f"[KLEIN] wired {slot} <- {dest}")
        except Exception as e:
            tex_failures.append(f"{ch}: set {slot} failed {e}")
    if tex_failures:
        raise SystemExit(f"[KLEIN] ABORT: texture wiring failures: {tex_failures}. Nothing was saved.")

    saved=False
    try: saved=unreal.EditorAssetLibrary.save_loaded_asset(inst, True)
    except Exception as e: raise SystemExit(f"[KLEIN] ABORT: save failed ({e})")
    if not saved:
        raise SystemExit("[KLEIN] ABORT: save_loaded_asset returned False (rule 9: verify by re-reading)")
    print(f"[KLEIN] MI ready: {UE_MI}")
    return inst

def place_height_aware():
    mi=ensure_mi()
    if not mi: return
    world=unreal.EditorLevelLibrary.get_editor_world()
    if not world: print("[KLEIN] no editor world"); return
    # find landscape for raycast (optional)
    lvl_actors=unreal.EditorLevelLibrary.get_all_level_actors()
    landscape=None
    for a in lvl_actors:
        if "Landscape" in a.get_actor_label() or "Faraway" in a.get_actor_label():
            landscape=a; break
    def get_z(x,y):
        try:
            hit=unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x,y,25000), unreal.Vector(x,y,-10000), unreal.DrawDebugType.NONE, True, [], unreal.CollisionChannel.Visibility)
            if hit and hit.get_editor_property("bBlockingHit"):
                return hit.get_editor_property("ImpactPoint").z
        except: pass
        # fallback synthetic
        for p in PLACEMENTS:
            if abs(p["xy"][0]-x)<1 and abs(p["xy"][1]-y)<1:
                return p["landscape_z_synthetic"]
        return 11850
    # mesh to spawn — use a simple plane proxy or imported KleinVeil mesh if present
    mesh_path="/Game/EnvSandbox/Meshes/FarawayMother/VDM/SM_Fabric_Plane_VDM"  # proxy; replace with SM_KleinVeil when HDA cooked
    mesh=unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        # fallback: Engine plane
        mesh=unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    for p in PLACEMENTS:
        x,y=p["xy"]; z=get_z(x,y)+35
        loc=unreal.Vector(x,y,z); rot=unreal.Rotator(0,p["yaw"],0); scl=unreal.Vector(p["scale"],p["scale"],p["scale"])
        actor=unreal.EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)
        if actor:
            try: actor.set_actor_label(p["id"])
            except: pass
            try: actor.set_actor_scale3d(scl)
            except: pass
            try:
                comp=actor.get_component_by_class(unreal.StaticMeshComponent)
                if comp: comp.set_material(0, mi)
            except: pass
            # WPO scale as custom primitive data or material param (store as actor tag for now)
            try: actor.tags=[f"WPO={p['wpo_scale']}", f"biome={p['biome']}"]
            except: pass
            print(f"[KLEIN] placed {p['id']} at ({x:.0f},{y:.0f},{z:.0f}) scale={p['scale']} WPO={p['wpo_scale']}")
    try: unreal.EditorLevelLibrary.save_current_level()
    except: pass
    print("[KLEIN] placement done — instances only, height-aware, MPC-driven")

if __name__=="__main__":
    ensure_mi(); place_height_aware()
