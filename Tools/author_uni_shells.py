"""author_uni_shells.py — author real content for the 4 NS_Uni_* shell systems.

Deterministic imperative build (create_system -> create_emitter -> add_module
-> set inputs -> add renderer -> set material -> set bounds), then compile and
report diagnostics. Sources rates/lifetimes/shapes from the pre-cleanup
recovery specs mined from Saved/Recovery/Niagara_20260801.

Targets (all under /Game/EnvSandbox/VFX/Candidates/Universal/):
  NS_Uni_DustShafts_Candidate   (GPU motes + CPU shaft leader/ribbon)
  NS_Uni_PollenSparkle_Candidate (GPU pink pollen motes)
  NS_Uni_Fireflies_Candidate     (CPU sprite motes + light renderer)
  NS_Uni_LeafDrift_Candidate     (GPU leaf-card sprites w/ leaf material)

Run from Tools/:  python author_uni_shells.py
Requires editor with Monolith on :9316.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcp_client import monolith  # noqa: E402

BASE = "/Game/EnvSandbox/VFX/Candidates/Universal"

# module script paths (engine-standard)
M_EMITTERSTATE = "/Niagara/Modules/Emitter/EmitterState.EmitterState"
M_SPAWNRATE = "/Niagara/Modules/Emitter/SpawnRate.SpawnRate"
M_SPAWNBURST = "/Niagara/Modules/Emitter/SpawnBurst_Instantaneous.SpawnBurst_Instantaneous"
M_INITPARTICLE = "/Niagara/Modules/Spawn/Initialization/V2/InitializeParticle.InitializeParticle"
M_SHAPELOC = "/Niagara/Modules/Spawn/Location/V2/ShapeLocation.ShapeLocation"
M_ADDVEL = "/Niagara/Modules/Spawn/Velocity/AddVelocity.AddVelocity"
M_PARTICLESTATE = "/Niagara/Modules/Update/Lifetime/ParticleState.ParticleState"
M_SCALECOLOR = "/Niagara/Modules/Update/Color/ScaleColor.ScaleColor"
M_DRAG = "/Niagara/Modules/Update/Forces/Drag.Drag"
M_CURL = "/Niagara/Modules/Update/Forces/CurlNoiseForce.CurlNoiseForce"
M_SOLVE = "/Niagara/Modules/Solvers/SolveForcesAndVelocity.SolveForcesAndVelocity"
M_GENLOCEVENT = "/Niagara/Modules/Update/GenerateLocationEvent.GenerateLocationEvent"
M_RECEIVELOCEVENT = "/Niagara/Modules/Event/ReceiveLocationEvent.ReceiveLocationEvent"

# project materials
MAT_MOTE = "/Game/EnvSandbox/VFX/Materials/MI_Niagara_Mote.MI_Niagara_Mote"
MAT_SPARKLE = "/Game/EnvSandbox/VFX/Materials/MI_Niagara_Sparkle.MI_Niagara_Sparkle"
MAT_AURORA_RIBBON = "/Game/EnvSandbox/VFX/Materials/MI_Niagara_AuroraRibbon.MI_Niagara_AuroraRibbon"
MAT_LEAVES = "/Game/Effects/Environments/Leaves/Materials/MI_Leaves.MI_Leaves"
EFFECT_AMBIENT = "/Game/EnvSandbox/VFX/EffectTypes/ENV_StorybookAmbientVFX.ENV_StorybookAmbientVFX"

STAGE_TO_USAGE = {
    "emitter_update": "emitter_update",
    "particle_spawn": "particle_spawn",
    "particle_update": "particle_update",
}


def nq(action, params, tries=1, wait=5.0):
    last = None
    for _ in range(tries):
        r = monolith("niagara_query", {"action": action, "params": params}, timeout=180)
        if not r.startswith("ERROR:"):
            return r
        last = r
        time.sleep(wait)
    return last


def ok(action, params):
    r = nq(action, params)
    if r.startswith("ERROR:"):
        print(f"  !! {action} FAILED: {r[:200]}")
    return r


def add_module(path, emitter, stage, script):
    ok("add_module", {"asset_path": path, "emitter": emitter, "usage": STAGE_TO_USAGE[stage], "module_script": script})


def build_motes_system(name, spawn_rate, lifetime, color_min, color_max, size_min, size_max,
                       box, velocity, drag, curl, material, sim_target="GPU"):
    path = f"{BASE}/{name}.{name}"
    print(f"\n== {name}")
    ok("create_system", {"save_path": f"{BASE}/{name}"})
    ok("create_emitter", {"asset_path": path, "name": "Motes"})
    add_module(path, "Motes", "emitter_update", M_EMITTERSTATE)
    add_module(path, "Motes", "emitter_update", M_SPAWNRATE)
    add_module(path, "Motes", "particle_spawn", M_INITPARTICLE)
    add_module(path, "Motes", "particle_spawn", M_SHAPELOC)
    add_module(path, "Motes", "particle_spawn", M_ADDVEL)
    add_module(path, "Motes", "particle_update", M_PARTICLESTATE)
    add_module(path, "Motes", "particle_update", M_SCALECOLOR)
    add_module(path, "Motes", "particle_update", M_DRAG)
    add_module(path, "Motes", "particle_update", M_CURL)
    add_module(path, "Motes", "particle_update", M_SOLVE)

    # set inputs (module_name matching is case-insensitive; use unique suffixes)
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "SpawnRate", "input": "SpawnRate", "value": spawn_rate})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "InitializeParticle", "input": "Lifetime Min", "value": lifetime[0]})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "InitializeParticle", "input": "Lifetime Max", "value": lifetime[1]})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "InitializeParticle", "input": "Color Minimum", "value": color_min})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "InitializeParticle", "input": "Color Maximum", "value": color_max})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Min", "value": size_min})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Max", "value": size_max})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "ShapeLocation", "input": "Box Size", "value": box})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "AddVelocity", "input": "Velocity", "value": velocity})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "Drag", "input": "Drag", "value": drag})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Motes", "module_node": "CurlNoiseForce", "input": "Noise Strength", "value": curl})

    ok("set_emitter_property", {"asset_path": path, "emitter": "Motes", "property": "SimTarget", "value": sim_target})
    ok("add_renderer", {"asset_path": path, "emitter": "Motes", "class": "NiagaraSpriteRendererProperties"})
    ok("set_renderer_material", {"asset_path": path, "emitter": "Motes", "renderer_index": 0, "material": material})
    ok("set_effect_type", {"asset_path": path, "effect_type": EFFECT_AMBIENT})
    ok("set_fixed_bounds", {"asset_path": path, "emitter": "Motes", "min": [-900, -700, -400], "max": [900, 700, 1800]})
    ok("set_system_property", {"asset_path": path, "property": "WarmupTime", "value": 0})
    return path


def build_fireflies():
    name = "NS_Uni_Fireflies_Candidate"
    path = f"{BASE}/{name}.{name}"
    print(f"\n== {name}")
    ok("create_system", {"save_path": f"{BASE}/{name}"})
    ok("create_emitter", {"asset_path": path, "name": "Firefly"})
    add_module(path, "Firefly", "emitter_update", M_EMITTERSTATE)
    add_module(path, "Firefly", "emitter_update", M_SPAWNRATE)
    add_module(path, "Firefly", "particle_spawn", M_INITPARTICLE)
    add_module(path, "Firefly", "particle_spawn", M_SHAPELOC)
    add_module(path, "Firefly", "particle_spawn", M_ADDVEL)
    add_module(path, "Firefly", "particle_update", M_PARTICLESTATE)
    add_module(path, "Firefly", "particle_update", M_DRAG)
    add_module(path, "Firefly", "particle_update", M_CURL)
    add_module(path, "Firefly", "particle_update", M_SOLVE)

    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "SpawnRate", "input": "SpawnRate", "value": 35.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "InitializeParticle", "input": "Lifetime Min", "value": 6.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "InitializeParticle", "input": "Lifetime Max", "value": 12.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "InitializeParticle", "input": "Color Minimum", "value": "(R=1.0,G=1.0,B=0.75,A=0.25)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "InitializeParticle", "input": "Color Maximum", "value": "(R=1.0,G=1.0,B=0.9,A=0.9)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Min", "value": 2.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Max", "value": 4.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "ShapeLocation", "input": "Box Size", "value": "(X=1000.0,Y=800.0,Z=600.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "AddVelocity", "input": "Velocity", "value": "(X=0.0,Y=0.0,Z=10.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "Drag", "input": "Drag", "value": 1.2})
    ok("set_module_input_value", {"asset_path": path, "emitter": "Firefly", "module_node": "CurlNoiseForce", "input": "Noise Strength", "value": 8.0})

    # fireflies: CPU sim (light renderer is CPU-only), sprite + light renderers
    ok("set_emitter_property", {"asset_path": path, "emitter": "Firefly", "property": "SimTarget", "value": "CPUSim"})
    ok("add_renderer", {"asset_path": path, "emitter": "Firefly", "class": "NiagaraSpriteRendererProperties"})
    ok("set_renderer_material", {"asset_path": path, "emitter": "Firefly", "renderer_index": 0, "material": MAT_MOTE})
    ok("add_renderer", {"asset_path": path, "emitter": "Firefly", "class": "NiagaraLightRendererProperties"})
    ok("set_effect_type", {"asset_path": path, "effect_type": EFFECT_AMBIENT})
    ok("set_fixed_bounds", {"asset_path": path, "emitter": "Firefly", "min": [-1000, -800, -600], "max": [1000, 800, 600]})
    ok("set_system_property", {"asset_path": path, "property": "WarmupTime", "value": 0})
    return path


def build_leafdrift():
    name = "NS_Uni_LeafDrift_Candidate"
    path = f"{BASE}/{name}.{name}"
    print(f"\n== {name}")
    ok("create_system", {"save_path": f"{BASE}/{name}"})
    ok("create_emitter", {"asset_path": path, "name": "LeafDrift"})
    add_module(path, "LeafDrift", "emitter_update", M_EMITTERSTATE)
    add_module(path, "LeafDrift", "emitter_update", M_SPAWNRATE)
    add_module(path, "LeafDrift", "particle_spawn", M_INITPARTICLE)
    add_module(path, "LeafDrift", "particle_spawn", M_SHAPELOC)
    add_module(path, "LeafDrift", "particle_spawn", M_ADDVEL)
    add_module(path, "LeafDrift", "particle_update", M_PARTICLESTATE)
    add_module(path, "LeafDrift", "particle_update", M_SCALECOLOR)
    add_module(path, "LeafDrift", "particle_update", M_DRAG)
    add_module(path, "LeafDrift", "particle_update", M_CURL)
    add_module(path, "LeafDrift", "particle_update", M_SOLVE)

    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "SpawnRate", "input": "SpawnRate", "value": 6.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "InitializeParticle", "input": "Lifetime Min", "value": 6.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "InitializeParticle", "input": "Lifetime Max", "value": 14.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "InitializeParticle", "input": "Color Minimum", "value": "(R=0.55,G=0.4,B=0.2,A=1.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "InitializeParticle", "input": "Color Maximum", "value": "(R=0.8,G=0.65,B=0.35,A=1.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Min", "value": 12.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "InitializeParticle", "input": "Uniform Sprite Size Max", "value": 22.0})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "ShapeLocation", "input": "Box Size", "value": "(X=1200.0,Y=900.0,Z=800.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "AddVelocity", "input": "Velocity", "value": "(X=15.0,Y=8.0,Z=-12.0)"})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "Drag", "input": "Drag", "value": 0.6})
    ok("set_module_input_value", {"asset_path": path, "emitter": "LeafDrift", "module_node": "CurlNoiseForce", "input": "Noise Strength", "value": 6.0})

    ok("set_emitter_property", {"asset_path": path, "emitter": "LeafDrift", "property": "SimTarget", "value": "GPUComputeSim"})
    ok("add_renderer", {"asset_path": path, "emitter": "LeafDrift", "class": "NiagaraSpriteRendererProperties"})
    ok("set_renderer_material", {"asset_path": path, "emitter": "LeafDrift", "renderer_index": 0, "material": MAT_LEAVES})
    ok("set_effect_type", {"asset_path": path, "effect_type": EFFECT_AMBIENT})
    ok("set_fixed_bounds", {"asset_path": path, "emitter": "LeafDrift", "min": [-1200, -900, -800], "max": [1200, 900, 800]})
    ok("set_system_property", {"asset_path": path, "property": "WarmupTime", "value": 0})
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


if __name__ == "__main__":
    print("Building candidate systems under", BASE)
    p1 = build_motes_system(
        "NS_Uni_DustShafts_Candidate",
        spawn_rate=12.0, lifetime=[4.0, 8.0],
        color_min="(R=1.0,G=0.78,B=0.52,A=0.08)", color_max="(R=1.0,G=0.95,B=0.78,A=0.45)",
        size_min=1.5, size_max=5.0, box="(X=750.0,Y=450.0,Z=900.0)",
        velocity="(X=0.0,Y=0.0,Z=5.0)", drag=1.5, curl=4.0, material=MAT_MOTE,
        sim_target="GPUComputeSim",
    )
    compile_and_report(p1)
    p2 = build_motes_system(
        "NS_Uni_PollenSparkle_Candidate",
        spawn_rate=18.0, lifetime=[3.5, 7.0],
        color_min="(R=1.0,G=0.68,B=0.86,A=0.18)", color_max="(R=1.0,G=0.92,B=0.95,A=0.5)",
        size_min=1.0, size_max=3.0, box="(X=900.0,Y=700.0,Z=350.0)",
        velocity="(X=0.0,Y=0.0,Z=8.0)", drag=1.8, curl=5.0, material=MAT_SPARKLE,
        sim_target="GPUComputeSim",
    )
    compile_and_report(p2)
    p3 = build_fireflies()
    compile_and_report(p3)
    p4 = build_leafdrift()
    compile_and_report(p4)
    print("\nDone.")
