"""THE JELLYFISH — massive jellyfish-esque structure (R6 of the reef lane).

Scale (metres; UE import x100):
  Bell diameter ~90 m, 8 ribbon arms, each ~320 m long (~3.5 football fields).

Topology contract: the bell's FOUR pose variants (Neutral / PulseContract /
PulseExpand / SurrealLurch) are generated from ONE code path with different
pose parameters — identical vertex order and count guaranteed, which is exactly
what shape keys require. All geometry leaves as a single deterministic
jellyfish_mesh.json (points + faces + uvs + pose point sets) because OBJ
importers re-order/dedup vertices and would silently break shape-key alignment.

Surreal arm logic (also baked independently into the LUTs by
jelly_surreal_lut.py; the geometry carries the resting shape):
  - traveling wave with subharmonic cascade, wavenumber rising along the arm
  - bifurcation drift: the arm commits to a new lateral direction mid-length
  - Moebius half-twist: the ribbon rotates pi over its length
  - anti-gravity rise: arms fall from the bell, then sweep back UP toward the
    horizon — a ribbon that spans football fields without touching the sea
  - all time-independent in geometry (motion lives in the LUT + morphs)

Outputs (Saved/Audit/sea_above/meshes/):
  jellyfish_mesh.json          the whole structure (bell + 4 poses + 8 arms)
  jellyfish_mesh_manifest.json

Run:  hython Tools/Houdini/sea_above_reef/build_jellyfish.py
"""

import json
import math
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "meshes"
SEED = 20260828

CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

V = hou.Vector3

def _rot(v, axis, ang):
    # Rodrigues (hou.Vector3 has no rotateAroundAxis)
    c = math.cos(ang); s = math.sin(ang)
    a = axis.normalized()
    return v * c + a.cross(v) * s + a * (a.dot(v) * (1.0 - c))

# MODE injected: 'bell' or 'arm'
MODE = __MODE__
rng = random.Random(SEED + hash(MODE) % 1000)

def build_bell():
    # params injected
    R = __R__; POSE = __POSE__
    SEG, RINGS = 96, 44
    rows = []
    for j in range(RINGS + 1):
        phi = (j / RINGS) * (math.pi * 0.62)      # dome opens ~112 degrees
        row = []
        for i in range(SEG):
            th = i / SEG * 2.0 * math.pi
            scallop = 1.0 + 0.055 * math.cos(th * 16.0) * (phi / (math.pi * 0.62)) ** 2
            rr = R * math.sin(phi) * scallop
            y = R * 0.72 * math.cos(phi)
            # pose deformation
            if POSE == "PulseContract":
                rr *= 0.86; y -= R * 0.10 * (phi / (math.pi * 0.62)) ** 2
            elif POSE == "PulseExpand":
                rr *= 1.10; y += R * 0.06 * (phi / (math.pi * 0.62)) ** 2
            elif POSE == "SurrealLurch":
                lurch = 0.5 + 0.5 * math.sin(th + 0.8)
                rr *= (0.78 + 0.26 * lurch)
                y += R * (0.09 * lurch - 0.05) * (phi / (math.pi * 0.62)) ** 2
            # organic fold displacement
            fold = 0.030 * math.sin(5.0 * th + 2.0) + 0.02 * math.sin(9.0 * th * (1 + 0.2 * math.sin(phi * 3.0)))
            rr *= (1.0 + fold * (phi / (math.pi * 0.62)))
            p = geo.createPoint()
            p.setPosition(V(rr * math.cos(th), y, rr * math.sin(th)))
            p.setAttribValue(geo.findPointAttrib("uv"), (i / SEG, 1.0 - j / RINGS))
            row.append(p)
        rows.append(row)
    for j in range(RINGS):
        for i in range(SEG):
            f = geo.createPolygon()
            for q in (rows[j][i], rows[j][(i + 1) % SEG],
                      rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
                f.addVertex(q)

def build_arm():
    # params injected
    ARM_INDEX = __ARM_INDEX__
    N_ARMS = __N_ARMS__
    LENGTH = __LENGTH__
    ROWS, COLS = __ROWS__, __COLS__
    WIDTH = __WIDTH__
    rng2 = random.Random(SEED + 500 + ARM_INDEX)
    a0 = ARM_INDEX / N_ARMS * 2.0 * math.pi
    ph = rng2.uniform(0, 6.28)
    # spine: fall from the bell margin, drift, then anti-gravity rise
    pts = []
    for i in range(ROWS + 1):
        s = i / ROWS
        r = 0.92 * __R__ + LENGTH * s * 0.55 * (0.4 + 0.6 * s)      # radial reach grows
        fall = -math.sin(min(1.0, s * 1.6) * math.pi * 0.5) * LENGTH * 0.34
        rise = max(0.0, s - 0.55) ** 1.6 * LENGTH * 0.30            # the surreal rise
        spiral = math.sin(a0 * 3.0 + s * 5.0 + ph) * LENGTH * 0.05 * s
        x = r * math.cos(a0) + spiral * math.cos(a0 + 1.57)
        z = r * math.sin(a0) + spiral * math.sin(a0 + 1.57)
        y = fall + rise
        # bifurcation drift: lateral commit mid-length
        drift = (1.0 if s > 0.5 else -1.0) * (s - 0.5) * 2.0 * LENGTH * 0.06
        x += drift * math.cos(a0 + 1.57)
        z += drift * math.sin(a0 + 1.57)
        pts.append(V(x, y, z))
    # ribbon: Moebius half-twist of the cross-section along the length
    grid = []
    for i, pos in enumerate(pts):
        s = i / ROWS
        if i == 0:
            tan = pts[1] - pts[0]
        elif i == ROWS:
            tan = pts[-1] - pts[-2]
        else:
            tan = pts[i + 1] - pts[i - 1]
        tan = tan.normalized()
        up = V(0, 1, 0)
        if abs(tan.dot(up)) > 0.95:
            up = V(1, 0, 0)
        x1 = tan.cross(up).normalized()
        y1 = tan.cross(x1).normalized()
        twist = math.pi * s          # half twist over the full length
        x2 = _rot(x1, tan, twist)
        y2 = _rot(y1, tan, twist)
        w = WIDTH * (0.3 + 0.7 * math.sin(math.pi * min(1.0, 0.12 + 0.88 * s))) \
            * (1.0 - 0.4 * s)
        row = []
        for k in range(COLS + 1):
            u = k / COLS - 0.5
            cup = (u * u * 4.0 - 1.0) * WIDTH * 0.10
            off = x2 * (w * u) + y2 * cup
            p = geo.createPoint()
            p.setPosition(pos + off)
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, s))   # uv.y = along-arm
            row.append(p)
        grid.append(row)
    for i in range(ROWS):
        for k in range(COLS):
            f = geo.createPolygon()
            for q in (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]):
                f.addVertex(q)

if MODE == "bell":
    build_bell()
else:
    build_arm()
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def _inject(code, **params):
    for key, value in params.items():
        code = code.replace(f"__{key}__", repr(value))
    return code


def _dump_geo(geo):
    pts = [[round(c, 3) for c in p.position()] for p in geo.points()]
    uvs = [list(p.attribValue(geo.findPointAttrib("uv"))) for p in geo.points()]
    faces = []
    for prim in geo.prims():
        faces.append([v.point().number() for v in prim.vertices()])
    return {"points": pts, "uvs": uvs, "faces": faces}


def _cook_report(py, tag):
    try:
        py.cook(force=True)
    except Exception:
        pass
    err = " ".join(str(py.errors()).split()) if py.errors() else ""
    if err:
        print(f"[jelly] NODE ERROR [{tag}]: {err[:500]}")
        return False
    return True


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    payload = {"schema": "melodia.jellyfish.v1", "seed": SEED,
               "scale": "metres; UE import x100",
               "bell": None, "bell_poses": {}, "arms": []}

    # bell: 4 pose variants from the same code path -> identical topology
    poses = [("Neutral", dict(R=45.0, POSE="Neutral")),
             ("PulseContract", dict(R=45.0, POSE="PulseContract")),
             ("PulseExpand", dict(R=45.0, POSE="PulseExpand")),
             ("SurrealLurch", dict(R=45.0, POSE="SurrealLurch"))]
    base_pts = None
    for pose_name, params in poses:
        for old in [n for n in obj.children() if n.name() == "JELLY_BELL"]:
            old.destroy()
        g = obj.createNode("geo", "JELLY_BELL", run_init_scripts=True)
        py = g.createNode("python", "gen_bell")
        code = _inject(CODE, MODE="bell", SEED=SEED, **params)
        code = code.replace("random.Random(SEED + hash(MODE) % 1000)",
                            f"random.Random({SEED} + hash(MODE) % 1000)")
        dbg = [ln.strip() for ln in code.splitlines() if ln.strip().startswith("MODE")]
        print(f"[jelly] debug {pose_name}: {dbg}")
        py.parm("python").set(code)
        if not _cook_report(py, f"bell:{pose_name}"):
            g.destroy()
            continue
        geo = py.geometry()
        data = _dump_geo(geo)
        if pose_name == "Neutral":
            payload["bell"] = data
            base_pts = [tuple(p) for p in data["points"]]
        else:
            same = len(data["points"]) == len(payload["bell"]["points"])
            payload["bell_poses"][pose_name] = {"points": data["points"],
                                                "topology_matches": same}
            if not same:
                print(f"[jelly] WARNING: pose {pose_name} topology mismatch!")
        print(f"[jelly] bell pose {pose_name}: {len(data['points'])} pts, "
              f"{len(data['faces'])} faces")
        g.destroy()

    # arms: 8 surreal ribbons, ~320 m each
    N_ARMS, LENGTH, ROWS, COLS, WIDTH = 8, 320.0, 240, 5, 6.0
    for old in [n for n in obj.children() if n.name() == "JELLY_ARMS"]:
        old.destroy()
    g = obj.createNode("geo", "JELLY_ARMS", run_init_scripts=True)
    py = g.createNode("python", "gen_arms")
    code = _inject(CODE, MODE="arm", SEED=SEED, R=45.0, ARM_INDEX=0, N_ARMS=N_ARMS,
                   LENGTH=LENGTH, ROWS=ROWS, COLS=COLS, WIDTH=WIDTH)
    # arms loop: one geo per arm merged via separate objects -> separate entries
    arm_entries = []
    for arm_i in range(N_ARMS):
        for old in [n for n in obj.children() if n.name() == f"JELLY_ARM_{arm_i}"]:
            old.destroy()
        ga = obj.createNode("geo", f"JELLY_ARM_{arm_i}", run_init_scripts=True)
        pya = ga.createNode("python", f"gen_arm_{arm_i}")
        ca = _inject(CODE, MODE="arm", R=45.0, ARM_INDEX=arm_i, N_ARMS=N_ARMS,
                     LENGTH=LENGTH, ROWS=ROWS, COLS=COLS, WIDTH=WIDTH)
        ca = ca.replace("random.Random(SEED + hash(MODE) % 1000)",
                        f"random.Random({SEED} + hash(MODE) % 1000)")
        ca = ca.replace("rng2 = random.Random(SEED + 500 + ARM_INDEX)",
                        f"rng2 = random.Random({SEED} + 500 + ARM_INDEX)")
        pya.parm("python").set(ca)
        if not _cook_report(pya, f"arm:{arm_i}"):
            ga.destroy()
            continue
        arm_entries.append(_dump_geo(pya.geometry()))
        print(f"[jelly] arm {arm_i}: {len(arm_entries[-1]['points'])} pts")
        ga.destroy()
    payload["arms"] = arm_entries
    payload["meta"] = {"n_arms": N_ARMS, "arm_length_m": LENGTH,
                       "football_fields_per_arm": round(LENGTH / 91.44, 2),
                       "bell_diameter_m": 90.0,
                       "surreal_logic": ["subharmonic cascade wave",
                                         "bifurcation drift at s>0.5",
                                         "moebius half-twist (pi over length)",
                                         "anti-gravity rise after the fall",
                                         "LUT time-loop per jelly_surreal_lut.py"]}
    g.destroy()

    out = OUT_DIR / "jellyfish_mesh.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"[jelly] wrote {out.name} ({out.stat().st_size} bytes)")

    manifest = {
        "schema": "melodia.sea_above_reef_meshes.v1",
        "kind": "jellyfish structure (R6): bell morphs + surreal ribbon arms",
        "seed": SEED, "hython": hou.applicationVersionString(),
        "mesh_json": str(out), "poses": [p for p, _ in poses],
        "ue_import": {"scale": "100x (m -> cm)",
                      "bell": "import as skeletal (single root bone) so the 4 morphs "
                              "are animatable: PulseContract/PulseExpand crossfade = "
                              "swim; SurrealLurch rare",
                      "arms": "static Nanite meshes; motion via WPO sampling "
                              "T_Jelly_ArmLogic_LUT (see jelly_surreal_lut.py)"},
        "entries": [{"name": "bell/arms", "json_bytes": out.stat().st_size}],
    }
    (OUT_DIR / "jellyfish_mesh_manifest.json").write_text(json.dumps(manifest, indent=2),
                                                          encoding="utf-8")
    print(f"[jelly] manifest -> jellyfish_mesh_manifest.json")


if __name__ == "__main__":
    main()
