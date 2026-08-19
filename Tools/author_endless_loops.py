"""author_endless_loops.py — build the endless-loop petal/leaf systems.

Canonical loop materials (created 2026-08-14):
  M_Niagara_PetalMesh_Loop   (dup of M_NiagaraPetal_Loop_v2_Candidate)
  M_Niagara_PetalSprite_Loop (dup of M_NiagaraPetal_Loop_Candidate)
  M_Niagara_PetalPile        (dup of M_SakuraPetal)
  M_Niagara_SDF_Loop         (dup of M_Niagara_SakuraSprite)

Systems built (candidates):
  NS_Melodia_PetalEndlessLoop_Candidate  — GPU mesh petals, LoopBehavior=Infinite,
                                           phase-stable lifecycle material, quiet at rest.
  NS_Melodia_LeafPileLoop_Candidate      — GPU leaf-card sprites stacking into piles,
                                           LoopBehavior=Infinite, SubUV 2x2 dead-leaf atlas.

Run from Tools/:  python author_endless_loops.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

BASE = "/Game/EnvSandbox/VFX/Candidates/Universal"

M_EMITTERSTATE = "/Niagara/Modules/Emitter/EmitterState.EmitterState"
M_SPAWNRATE = "/Niagara/Modules/Emitter/SpawnRate.SpawnRate"
M_INITPARTICLE = "/Niagara/Modules/Spawn/Initialization/V2/InitializeParticle.InitializeParticle"
M_SHAPELOC = "/Niagara/Modules/Spawn/Location/V2/ShapeLocation.ShapeLocation"
M_ADDVEL = "/Niagara/Modules/Spawn/Velocity/AddVelocity.AddVelocity"
M_PARTICLESTATE = "/Niagara/Modules/Update/Lifetime/ParticleState.ParticleState"
M_SCALECOLOR = "/Niagara/Modules/Update/Color/ScaleColor.ScaleColor"
M_DRAG = "/Niagara/Modules/Update/Forces/Drag.Drag"
M_CURL = "/Niagara/Modules/Update/Forces/CurlNoiseForce.CurlNoiseForce"
M_SOLVE = "/Niagara/Modules/Solvers/SolveForcesAndVelocity.SolveForcesAndVelocity"
M_SUBUV = "/Niagara/Modules/Update/SubUV/V2/SubUVAnimation.SubUVAnimation"

MAT_PETAL_MESH = "/Game/EnvSandbox/VFX/Materials/M_Niagara_PetalMesh_Loop.M_Niagara_PetalMesh_Loop"
MAT_PETAL_SPRITE = "/Game/EnvSandbox/VFX/Materials/M_Niagara_PetalSprite_Loop.M_Niagara_PetalSprite_Loop"
MAT_LEAVES = "/Game/Effects/Environments/Leaves/Materials/MI_Leaves.MI_Leaves"
SM_PETAL_STD = "/Game/EnvSandbox/Meshes/Sakura/SM_SakuraPetal.SM_SakuraPetal"
EFFECT_AMBIENT = "/Game/EnvSandbox/VFX/EffectTypes/ENV_StorybookAmbientVFX.ENV_StorybookAmbientVFX"

TEX_LEAVES = "/Game/Effects/Environments/Leaves/Textures/T_Leaves_Dead_2x2_01_Albedo.T_Leaves_Dead_2x2_01_Albedo"

from niagara_contract import CONTRACT_AUTHOR as CONTRACT


def nq(action, params, timeout=180):
    return monolith("niagara_query", {"action": action, "params": params}, timeout=timeout)


def ok(action, params):
    r = nq(action, params)
    if r.startswith("ERROR:"):
        print(f"  !! {action} FAILED: {r[:200]}")
    return r


def add_module(path, emitter, stage, script):
    ok("add_module", {"asset_path": path, "emitter": emitter, "usage": stage, "module_script": script})


def add_contract_params(path):
    for name, typ in CONTRACT:
        ok("add_user_parameter", {"asset_path": path, "name": name, "type": typ})


def finalize(path, emitter, bounds_min, bounds_max):
    ok("set_emitter_property", {"asset_path": path, "emitter": emitter, "property": "CalculateBoundsMode", "value": "Fixed"})
    ok("set_fixed_bounds", {"asset_path": path, "emitter": emitter, "min": bounds_min, "max": bounds_max})
    ok("set_effect_type", {"asset_path": path, "effect_type": EFFECT_AMBIENT})
    ok("set_emitter_loop_profile", {"asset_path": path, "emitter": emitter, "loop_behavior": "Infinite"})
    ok("set_system_property", {"asset_path": path, "property": "WarmupTime", "value": 0})


def build_petal_endless():
    name = "NS_Melodia_PetalEndlessLoop_Candidate"
    path = f"{BASE}/{name}.{name}"
    print(f"\n== {name}")
    ok("create_system", {"save_path": f"{BASE}/{name}"})
    ok("create_emitter", {"asset_path": path, "name": "PetalLoop"})
    add_module(path, "PetalLoop", "emitter_update", M_EMITTERSTATE)
    add_module(path, "PetalLoop", "emitter_update", M_SPAWNRATE)
    add_module(path, "PetalLoop", "particle_spawn", M_INITPARTICLE)
    add_module(path, "PetalLoop", "particle_spawn", M_SHAPELOC)
    add_module(path, "PetalLoop", "particle_spawn", M_ADDVEL)
    add_module(path, "PetalLoop", "particle_update", M_PARTICLESTATE)
    add_module(path, "PetalLoop", "particle_update", M_SCALECOLOR)
    add_module(path, "PetalLoop", "particle_update", M_DRAG)
    add_module(path, "PetalLoop", "particle_update", M_CURL)
    add_module(path, "PetalLoop", "particle_update", M_SOLVE)

    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "SpawnRate", "input": "SpawnRate", "value": 60.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "InitializeParticle", "input": "Lifetime Min", "value": 8.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "InitializeParticle", "input": "Lifetime Max", "value": 16.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "InitializeParticle", "input": "Color Minimum", "value": "(R=1.0,G=0.86,B=0.9,A=1.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "InitializeParticle", "input": "Color Maximum", "value": "(R=1.0,G=0.95,B=0.98,A=1.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "InitializeParticle", "input": "Mesh Scale Min", "value": 0.8})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "InitializeParticle", "input": "Mesh Scale Max", "value": 1.4})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "ShapeLocation", "input": "Box Size", "value": "(X=1400.0,Y=1000.0,Z=1000.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "AddVelocity", "input": "Velocity", "value": "(X=0.0,Y=0.0,Z=-18.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "Drag", "input": "Drag", "value": 0.4})
    ok("set_module_input_value", {"asset_path": path, "emitter": "PetalLoop", "module_node": "CurlNoiseForce", "input": "Noise Strength", "value": 10.0})

    ok("set_emitter_property", {"asset_path": path, "emitter": "PetalLoop", "property": "SimTarget", "value": "GPUComputeSim"})
    ok("add_renderer", {"asset_path": path, "emitter": "PetalLoop", "class": "NiagaraMeshRendererProperties"})
    ok("set_renderer_mesh", {"asset_path": path, "emitter": "PetalLoop", "renderer_index": 0, "mesh": SM_PETAL_STD})
    ok("set_renderer_material", {"asset_path": path, "emitter": "PetalLoop", "renderer_index": 0, "material": MAT_PETAL_MESH})
    r = ok("list_renderers", {"asset_path": path, "emitter": "PetalLoop"})
    try:
        rends = json.loads(r).get("renderers", [])
        for rr in rends:
            if rr.get("type") == "sprite":
                ok("remove_renderer", {"asset_path": path, "emitter": "PetalLoop", "renderer_index": rr["index"]})
    except Exception:
        pass
    add_contract_params(path)
    finalize(path, "PetalLoop", [-1400, -1000, -1000], [1400, 1000, 1000])
    return path


def build_leaf_pile():
    name = "NS_Melodia_LeafPileLoop_Candidate"
    path = f"{BASE}/{name}.{name}"
    print(f"\n== {name}")
    ok("create_system", {"save_path": f"{BASE}/{name}"})
    ok("create_emitter", {"asset_path": path, "name": "LeafPile"})
    add_module(path, "LeafPile", "emitter_update", M_EMITTERSTATE)
    add_module(path, "LeafPile", "emitter_update", M_SPAWNRATE)
    add_module(path, "LeafPile", "particle_spawn", M_INITPARTICLE)
    add_module(path, "LeafPile", "particle_spawn", M_SHAPELOC)
    add_module(path, "LeafPile", "particle_spawn", M_ADDVEL)
    add_module(path, "LeafPile", "particle_update", M_PARTICLESTATE)
    add_module(path, "LeafPile", "particle_update", M_SCALECOLOR)
    add_module(path, "LeafPile", "particle_update", M_DRAG)
    add_module(path, "LeafPile", "particle_update", M_CURL)
    add_module(path, "LeafPile", "particle_update", M_SOLVE)
    add_module(path, "LeafPile", "particle_update", M_SUBUV)

    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "SpawnRate", "input": "SpawnRate", "value": 30.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "InitializeParticle", "input": "Lifetime Min", "value": 10.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "InitializeParticle", "input": "Lifetime Max", "value": 20.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "InitializeParticle", "input": "Color Minimum", "value": "(R=0.5,G=0.36,B=0.18,A=1.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "InitializeParticle", "input": "Color Maximum", "value": "(R=0.8,G=0.62,B=0.3,A=1.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Min", "value": 10.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Max", "value": 26.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "ShapeLocation", "input": "Box Size", "value": "(X=800.0,Y=500.0,Z=120.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "AddVelocity", "input": "Velocity", "value": "(X=0.0,Y=0.0,Z=-4.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "Drag", "input": "Drag", "value": 2.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafPile", "module_node": "CurlNoiseForce", "input": "Noise Strength", "value": 3.0})

    ok("set_emitter_property", {"asset_path": path, "emitter": "LeafPile", "property": "SimTarget", "value": "GPUComputeSim"})
    ok("add_renderer", {"asset_path": path, "emitter": "LeafPile", "class": "NiagaraSpriteRendererProperties"})
    ok("set_renderer_material", {"asset_path": path, "emitter": "LeafPile", "renderer_index": 0, "material": MAT_LEAVES})
    # SubUV: 2x2 dead-leaf atlas
    ok("configure_subuv", {"asset_path": path, "emitter": "LeafPile", "renderer_index": 0,
                           "columns": 2, "rows": 2,
                           "start_frame": 0, "end_frame": 3, "animation_mode": "Loop"})
    # remove default sprite renderer duplicate if any
    r = ok("list_renderers", {"asset_path": path, "emitter": "LeafPile"})
    try:
        rends = json.loads(r).get("renderers", [])
        for rr in rends:
            if rr.get("type") == "sprite" and rr.get("index") != 0 and not rr.get("material"):
                ok("remove_renderer", {"asset_path": path, "emitter": "LeafPile", "renderer_index": rr["index"]})
    except Exception:
        pass
    add_contract_params(path)
    finalize(path, "LeafPile", [-800, -500, -120], [800, 500, 120])
    return path


def compile_and_report(path):
    print(f"  compile: {ok('request_compile', {'asset_path': path})[:120]}")
    time.sleep(3)
    r = ok("get_system_diagnostics", {"asset_path": path})
    try:
        d = json.loads(r)
        print(f"  diagnostics: errors={d.get('error_count')} warnings={d.get('warning_count')}")
        for e in d.get("errors", []):
            print(f"    ERR {e.get('emitter')}: {e.get('message','')[:160]}")
        for w in d.get("warnings", []):
            print(f"    WRN {w.get('emitter')}: {w.get('message','')[:160]}")
    except Exception:
        print("  diagnostics raw:", r[:400])
    r2 = ok("validate_system", {"asset_path": path})
    print("  validate:", r2[:300])


if __name__ == "__main__":
    p1 = build_petal_endless()
    compile_and_report(p1)
    p2 = build_leaf_pile()
    compile_and_report(p2)
    print("\nDone.")
