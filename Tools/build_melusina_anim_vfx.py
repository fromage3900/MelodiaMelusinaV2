"""Build the Melusina ABP-driven VFX set (Infinity Nikki lens).

Systems created (all quiet at rest, driven by User.* params the ABPs write):
  NS_Melusina_EyeSparkle  - SDF star on master_eye_L/R (body), User.MelusinaSparkleRate
  NS_Melusina_Globules    - water beads at hair strand tips, User.MotionEnergy + User.LandBurst
  NS_Melusina_SwingTrail  - ribbon on hand_r + hand_l, User.SwingEnergy

Socket names (bones, not edited): master_eye_L/R, hand_l/r, A/B/C_DEF_hair_bbone tips.

Usage: python Tools/build_melusina_anim_vfx.py [--steps eye|globules|trail|save|all]
Requires Monolith at http://127.0.0.1:9316/mcp (exactly one listener).
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.request import Request, urlopen

MONOLITH = "http://127.0.0.1:9316/mcp"
VFX = "/Game/Melodia/VFX"

EYE = f"{VFX}/NS_Melusina_EyeSparkle"
GLOB = f"{VFX}/NS_Melusina_Globules"
TRAIL = f"{VFX}/NS_Melusina_SwingTrail"

SOCKET_LOC = "/Niagara/Modules/Spawn/Location/SocketLocation.SocketLocation"
BONE_INPUT = "Socket / Bone Name"
BURST = "/Niagara/Modules/Emitter/SpawnBurst_Instantaneous.SpawnBurst_Instantaneous"
SPAWNRATE = "/Niagara/Modules/Emitter/SpawnRate.SpawnRate"
OLD_SKEL = "SkeletalMeshLocation"


def mc(tool: str, action: str, params: dict) -> dict:
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": {"action": action, "params": params}},
    }).encode()
    req = Request(MONOLITH, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=120) as resp:
        envelope = json.loads(resp.read().decode())
    content = envelope.get("result", {}).get("content") or []
    if content:
        return {"text": content[0].get("text", "")}
    return envelope


def nig(action: str, params: dict) -> str:
    r = mc("niagara_query", action, params)
    return r.get("text", json.dumps(r))


def bone_swap(asset: str, emitters: dict) -> None:
    """Replace the v2 index-based skeletal module with the name-based SocketLocation."""
    for em, bone in emitters.items():
        nig("remove_module", {"asset_path": asset, "emitter": em, "module_node": OLD_SKEL})
        nig("add_module", {"asset_path": asset, "emitter": em, "usage": "particle_spawn",
                           "module_script": SOCKET_LOC})
        nig("set_module_input_value", {"asset_path": asset, "emitter": em, "module_node": "SocketLocation",
                                       "input": BONE_INPUT, "value": bone})


def step_eye() -> None:
    print("[eye] rebuild emitters clean: rate binding, bone sockets, lifetime, bounds")
    for em, bone in (("Sparkle_L", "master_eye_L"), ("Sparkle_R", "master_eye_R")):
        nig("clear_emitter_modules", {"asset_path": EYE, "emitter": em, "usage": "all"})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "emitter_update",
                           "module_script": "/Niagara/Modules/Emitter/EmitterState.EmitterState"})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "emitter_update", "module_script": SPAWNRATE})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "particle_spawn",
                           "module_script": "/Niagara/Modules/Spawn/Initialization/V2/InitializeParticle.InitializeParticle"})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "particle_spawn", "module_script": SOCKET_LOC})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "particle_spawn",
                           "module_script": "/Niagara/Modules/Spawn/Velocity/AddVelocity.AddVelocity"})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "particle_update",
                           "module_script": "/Niagara/Modules/Update/Lifetime/ParticleState.ParticleState"})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "particle_update",
                           "module_script": "/Niagara/Modules/Update/Color/ScaleColor.ScaleColor"})
        nig("add_module", {"asset_path": EYE, "emitter": em, "usage": "particle_update",
                           "module_script": "/Niagara/Modules/Solvers/SolveForcesAndVelocity.SolveForcesAndVelocity"})
        nig("set_module_input_value", {"asset_path": EYE, "emitter": em, "module_node": "SpawnRate",
                                       "input": "SpawnRate", "value": "User.MelusinaSparkleRate"})
        nig("set_module_input_value", {"asset_path": EYE, "emitter": em, "module_node": "SocketLocation",
                                       "input": BONE_INPUT, "value": bone})
        nig("set_module_input_value", {"asset_path": EYE, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Lifetime Min", "value": "0.3"})
        nig("set_module_input_value", {"asset_path": EYE, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Lifetime Max", "value": "0.6"})
        nig("set_module_input_value", {"asset_path": EYE, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Sprite Size Min", "value": "0.06,0.06"})
        nig("set_module_input_value", {"asset_path": EYE, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Sprite Size Max", "value": "0.10,0.10"})
    nig("set_fixed_bounds", {"asset_path": EYE, "min": "-0.5,-0.5,-0.5", "max": "0.5,0.5,0.5"})
    nig("request_compile", {"asset_path": EYE})


def step_globules() -> None:
    print("[globules] three strand-tip emitters, motion + land burst")
    nig("add_user_parameter", {"asset_path": GLOB, "name": "MotionEnergy", "type": "NiagaraFloat"})
    nig("set_parameter_default", {"asset_path": GLOB, "parameter": "User.MotionEnergy", "value": "0"})
    nig("add_user_parameter", {"asset_path": GLOB, "name": "LandBurst", "type": "NiagaraFloat"})
    nig("set_parameter_default", {"asset_path": GLOB, "parameter": "User.LandBurst", "value": "0"})
    for em in ("GlobuleA", "GlobuleB", "GlobuleC"):
        nig("set_module_input_value", {"asset_path": GLOB, "emitter": em, "module_node": "SpawnRate",
                                       "input": "SpawnRate", "value": "User.MotionEnergy"})
        nig("remove_module", {"asset_path": GLOB, "emitter": em, "module_node": "SpawnBurst_Instantaneous"})
        nig("add_module", {"asset_path": GLOB, "emitter": em, "usage": "emitter_update", "module_script": BURST})
        nig("set_module_input_value", {"asset_path": GLOB, "emitter": em, "module_node": "SpawnBurst_Instantaneous",
                                       "input": "Spawn Count", "value": "User.LandBurst"})
        nig("set_module_input_value", {"asset_path": GLOB, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Lifetime Min", "value": "1.2"})
        nig("set_module_input_value", {"asset_path": GLOB, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Lifetime Max", "value": "2.0"})
        nig("set_module_input_value", {"asset_path": GLOB, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Sprite Size Min", "value": "0.03,0.03"})
        nig("set_module_input_value", {"asset_path": GLOB, "emitter": em, "module_node": "InitializeParticle",
                                       "input": "Sprite Size Max", "value": "0.06,0.06"})
    bone_swap(GLOB, {"GlobuleA": "A_DEF_hair_bbone_017", "GlobuleB": "B_DEF_hair_bbone_007",
                     "GlobuleC": "C_DEF_hair_bbone_119"})
    nig("set_fixed_bounds", {"asset_path": GLOB, "min": "-1,-1,-1", "max": "1,1,1"})
    nig("request_compile", {"asset_path": GLOB})


def step_trail() -> None:
    print("[trail] two leader/ribbon pairs, per-pair events, bone sockets")
    nig("add_user_parameter", {"asset_path": TRAIL, "name": "SwingEnergy", "type": "NiagaraFloat"})
    nig("set_parameter_default", {"asset_path": TRAIL, "parameter": "User.SwingEnergy", "value": "0"})
    for em in ("TrailLeader_R", "TrailLeader_L"):
        nig("remove_module", {"asset_path": TRAIL, "emitter": em, "module_node": "SpawnBurst_Instantaneous"})
        nig("remove_module", {"asset_path": TRAIL, "emitter": em, "module_node": "SpawnRate"})
        nig("add_module", {"asset_path": TRAIL, "emitter": em, "usage": "emitter_update", "module_script": SPAWNRATE})
        nig("set_module_input_value", {"asset_path": TRAIL, "emitter": em, "module_node": "SpawnRate",
                                       "input": "SpawnRate", "value": "User.SwingEnergy"})
    bone_swap(TRAIL, {"TrailLeader_R": "hand_r", "TrailLeader_L": "hand_l"})
    nig("set_fixed_bounds", {"asset_path": TRAIL, "min": "-1.5,-1.5,-1.5", "max": "1.5,1.5,1.5"})
    nig("request_compile", {"asset_path": TRAIL})


def save_all() -> None:
    for path in (EYE, GLOB, TRAIL):
        nig("save_system", {"asset_path": path})
        diag = nig("get_system_diagnostics", {"asset_path": path})
        print(f"[diag] {path.split('/')[-1]}: {diag[:700]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", default="all",
                        help="comma list: eye,globules,trail,save (default all)")
    args = parser.parse_args()
    steps = args.steps.split(",")
    if "all" in steps:
        steps = ["eye", "globules", "trail", "save"]
    for s in steps:
        if s == "eye":
            step_eye()
        elif s == "globules":
            step_globules()
        elif s == "trail":
            step_trail()
        elif s == "save":
            save_all()
        else:
            print(f"unknown step {s}", file=sys.stderr)
    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
