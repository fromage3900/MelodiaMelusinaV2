"""THE JELLYFISH V2 — "GRAND / MORE SURREAL" expansion of the R6 lane.

Contract with the engine (DO NOT BREAK):
  - Same 4-pose bell set with the SAME pose names (Neutral / PulseContract /
    PulseExpand / SurrealLurch) from one code path -> topology identical within
    the file, so the existing 3-morph UE import + morph-driver wiring stays valid.
  - LUTs stay VALID unchanged: arm uv.y is normalized along-length, so the
    existing T_Jelly_ArmLogic_LUT / T_Jelly_Biolum_LUT drive v2 arms as-is.
  - Same JSON schema (melodia.jellyfish.v1) with a new variant tag; new output
    filenames; v1 files untouched.

Grand/surreal deltas vs v1:
  - bell radius 45 -> 68 m (diameter 90 -> 136 m), density raised to match
  - scallop lobes 16 -> 24, fold amplitude x1.6
  - arms 8 -> 12, length 320 -> 480 m (5.25 football fields), ribbon wider,
    denser (ROWS 240->320, COLS 5->7)
  - Moebius twist pi -> 1.5*pi (three-quarter twist)
  - second bifurcation commit at s>0.72 (arm changes its mind twice)
  - anti-gravity rise 0.30 -> 0.42 (the horizon sweep is stronger)
  - new seed (v1 seed untouched)

Outputs (Saved/Audit/sea_above/meshes/):
  jellyfish_mesh_v2_grand.json
  jellyfish_mesh_v2_grand_manifest.json

Run (isolated console, never bare in a shared shell):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_jellyfish_v2_grand.py
"""

import json
import sys
from pathlib import Path

import hou

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_jellyfish import CODE, _cook_report, _dump_geo, _inject  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "meshes"

SEED_V2 = 20260829
BELL_R = 68.0
BELL_SEG, BELL_RINGS = 128, 56
SCALLOP_LOBES = 24
FOLD_AMP = 0.048          # v1: 0.030
N_ARMS = 12
ARM_LENGTH = 480.0
ARM_ROWS, ARM_COLS, ARM_WIDTH = 320, 7, 8.0
TWIST_TURNS = 1.5         # v1: 0.5 (pi) -> 1.5*pi over the length
RISE_FACTOR = 0.42        # v1: 0.30
BIFURCATIONS = (0.5, 0.72)

V2_CODE = CODE
V2_CODE = V2_CODE.replace("math.cos(th * 16.0)", f"math.cos(th * {SCALLOP_LOBES}.0)")
V2_CODE = V2_CODE.replace("0.030 * math.sin(5.0 * th + 2.0)",
                          f"{FOLD_AMP} * math.sin(5.0 * th + 2.0)")
V2_CODE = V2_CODE.replace("0.02 * math.sin(9.0 * th",
                          f"{round(FOLD_AMP * 0.6667, 4)} * math.sin(9.0 * th")
V2_CODE = V2_CODE.replace("twist = math.pi * s",
                          f"twist = math.pi * {TWIST_TURNS} * s")
V2_CODE = V2_CODE.replace("rise = max(0.0, s - 0.55) ** 1.6 * LENGTH * 0.30",
                          f"rise = max(0.0, s - 0.55) ** 1.6 * LENGTH * {RISE_FACTOR}")
V2_CODE = V2_CODE.replace(
    "drift = (1.0 if s > 0.5 else -1.0) * (s - 0.5) * 2.0 * LENGTH * 0.06",
    "drift = 0.0\n"
    "        for _bs in __BIFURCATIONS__:\n"
    "            if s > _bs:\n"
    "                drift += (1.0 if (int(_bs * 100) + ARM_INDEX) % 2 == 0 else -1.0) "
    "* (s - _bs) * 2.0 * LENGTH * 0.05"
)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    payload = {"schema": "melodia.jellyfish.v1", "variant": "v2_grand",
               "seed": SEED_V2, "scale": "metres; UE import x100",
               "bell": None, "bell_poses": {}, "arms": []}

    poses = [(n, dict(R=BELL_R, POSE=n)) for n in
             ("Neutral", "PulseContract", "PulseExpand", "SurrealLurch")]
    for pose_name, params in poses:
        for old in [n for n in obj.children() if n.name() == "JELLY_BELL_V2"]:
            old.destroy()
        g = obj.createNode("geo", "JELLY_BELL_V2", run_init_scripts=True)
        py = g.createNode("python", "gen_bell_v2")
        code = _inject(V2_CODE, MODE="bell", SEED=SEED_V2, **params)
        code = code.replace("random.Random(SEED + hash(MODE) % 1000)",
                            f"random.Random({SEED_V2} + hash(MODE) % 1000)")
        code = code.replace("SEG, RINGS = 96, 44",
                            f"SEG, RINGS = {BELL_SEG}, {BELL_RINGS}")
        py.parm("python").set(code)
        if not _cook_report(py, f"bell_v2:{pose_name}"):
            g.destroy()
            continue
        data = _dump_geo(py.geometry())
        if pose_name == "Neutral":
            payload["bell"] = data
        else:
            same = len(data["points"]) == len(payload["bell"]["points"])
            payload["bell_poses"][pose_name] = {"points": data["points"],
                                                "topology_matches": same}
            if not same:
                print(f"[jellyv2] WARNING: pose {pose_name} topology mismatch!")
        print(f"[jellyv2] bell pose {pose_name}: {len(data['points'])} pts, "
              f"{len(data['faces'])} faces")
        g.destroy()

    for old in [n for n in obj.children() if n.name() == "JELLY_ARMS_V2"]:
        old.destroy()
    g = obj.createNode("geo", "JELLY_ARMS_V2", run_init_scripts=True)
    g.destroy()
    arm_entries = []
    for arm_i in range(N_ARMS):
        for old in [n for n in obj.children() if n.name() == f"JELLY_ARM_V2_{arm_i}"]:
            old.destroy()
        ga = obj.createNode("geo", f"JELLY_ARM_V2_{arm_i}", run_init_scripts=True)
        pya = ga.createNode("python", f"gen_arm_v2_{arm_i}")
        ca = _inject(V2_CODE, MODE="arm", SEED=SEED_V2, R=BELL_R, ARM_INDEX=arm_i,
                     N_ARMS=N_ARMS, LENGTH=ARM_LENGTH, ROWS=ARM_ROWS,
                     COLS=ARM_COLS, WIDTH=ARM_WIDTH, BIFURCATIONS=BIFURCATIONS)
        ca = ca.replace("random.Random(SEED + hash(MODE) % 1000)",
                        f"random.Random({SEED_V2} + hash(MODE) % 1000)")
        ca = ca.replace("rng2 = random.Random(SEED + 500 + ARM_INDEX)",
                        f"rng2 = random.Random({SEED_V2} + 500 + ARM_INDEX)")
        pya.parm("python").set(ca)
        if not _cook_report(pya, f"arm_v2:{arm_i}"):
            ga.destroy()
            continue
        arm_entries.append(_dump_geo(pya.geometry()))
        print(f"[jellyv2] arm {arm_i}: {len(arm_entries[-1]['points'])} pts")
        ga.destroy()
    payload["arms"] = arm_entries
    payload["meta"] = {
        "n_arms": N_ARMS, "arm_length_m": ARM_LENGTH,
        "football_fields_per_arm": round(ARM_LENGTH / 91.44, 2),
        "bell_diameter_m": BELL_R * 2,
        "surreal_logic": ["subharmonic cascade wave",
                          "double bifurcation drift (s>0.5, s>0.72)",
                          "moebius 1.5*pi twist over length",
                          f"anti-gravity rise {RISE_FACTOR} (v1 0.30)",
                          "scallop lobes 24 (v1 16), fold amp x1.6",
                          "LUT time-loop per jelly_surreal_lut.py (unchanged, uv.y-normalized)"],
    }

    out = OUT_DIR / "jellyfish_mesh_v2_grand.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"[jellyv2] wrote {out.name} ({out.stat().st_size} bytes)")

    manifest = {
        "schema": "melodia.sea_above_reef_meshes.v1",
        "kind": "jellyfish structure R6 v2 GRAND: bigger bell, 12 double-bifurcating "
                "1.5-twist arms, stronger rise",
        "variant": "v2_grand", "seed": SEED_V2,
        "hython": hou.applicationVersionString(),
        "mesh_json": str(out),
        "poses": [p for p, _ in poses],
        "engine_contract": "pose names + uv layout unchanged from v1; existing 3-morph "
                           "import path and LUTs remain valid",
        "ue_import": {"scale": "100x (m -> cm)",
                      "bell": "skeletal, single root bone; same morph driver wiring as v1",
                      "arms": "static Nanite meshes; existing T_Jelly_ArmLogic_LUT recipe"},
        "entries": [{"name": "bell/arms_v2", "json_bytes": out.stat().st_size}],
    }
    (OUT_DIR / "jellyfish_mesh_v2_grand_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[jellyv2] manifest -> jellyfish_mesh_v2_grand_manifest.json")


if __name__ == "__main__":
    main()
