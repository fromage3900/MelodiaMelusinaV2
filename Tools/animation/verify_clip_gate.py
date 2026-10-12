#!/usr/bin/env python3
"""Existing Melusina numeric clip prerequisite; never a runtime certificate.

Converges the KineFX / UE-retarget / Shinbi / ACFU / mocap lanes onto a single contract.
Reads canon numbers from specs/universal_rig/rig_contract.v1.json (never hard-codes them).

    python Tools/animation/verify_clip_gate.py --asset /Game/.../A_Clip
    python Tools/animation/verify_clip_gate.py --asset /Game/.../A_Clip --json out.json

Checks:
  1. ARM CANON   [HARD] segment lengths shoulder->arm / arm->forearm / forearm->hand match
                 contract (rejects the 34.789/9.520 reference-pose redistribution — the arm
                 regression). This is the one that MUST pass or the clip is rejected.
  2. LOOP SEAM   [HARD] first vs last frame foot/root displacement < gate (kills the visible pop)
                 on cycling clips (idle/walk/run/sprint/loop). Non-loop clips are exempt.
  3. FOOT Z      [INFO] lowest foot height for the clip's class. Informational only: raw clips are
                 authored in character-space above the floor reference and FootPlacement corrects
                 ground contact at runtime, so this is a sanity signal, not a ship gate.

Exit 0 = numeric PASS, 1 = FAIL, 2 = ERROR (could not measure).
Numeric PASS does not establish shoulder silhouette, blended runtime pose, or contact acceptance.
Missing/unreadable data is ERROR, never PASS. Arm canon checks both arms across the clip.
Read-only. Talks to Monolith on http://127.0.0.1:9316. Mutates nothing.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CONTRACT = REPO / "specs/universal_rig/rig_contract.v1.json"
MONOLITH = "http://127.0.0.1:9316/mcp"
BODY = "/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
POLICY = REPO / "specs/anim_presets/melusina_locomotion_blend.json"
_POSE_CACHE = {}


def package_path(asset):
    if not isinstance(asset, str) or not asset.startswith('/Game/') or "'" in asset:
        raise RuntimeError("expected an explicit /Game/ asset path")
    return asset.split('.', 1)[0]


def asset_identity(asset):
    path = REPO / 'Content' / (package_path(asset)[6:] + '.uasset')
    if not path.is_file():
        raise RuntimeError("saved asset missing: " + str(path))
    return {'package': package_path(asset), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def actual_body_samples(asset):
    """Evaluate compressed stored keys on the required body; no preview fallback.

    Evaluate once per sequence, rather than making one RPC per bone/key. Dirty
    inputs cannot be tied to their disk hashes and therefore fail closed.
    """
    asset = package_path(asset)
    if asset in _POSE_CACHE:
        return _POSE_CACHE[asset]
    command = '''import unreal,json
a=unreal.load_asset(%r)
m=unreal.load_asset(%r)
assert a is not None and m is not None, 'sequence or canonical body did not load'
assert m.get_path_name().split('.')[0]==%r, 'wrong body'
assert a.get_editor_property('skeleton').get_path_name().split('.')[0]==%r, 'foreign skeleton'
dirty={x.get_name() for x in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()}
assert a.get_outermost().get_name() not in dirty and m.get_outermost().get_name() not in dirty, 'unsaved input; disk hash cannot identify evaluated pose'
count=unreal.AnimationLibrary.get_num_keys(a)
assert count>0, 'empty sequence'
options=unreal.AnimPoseEvaluationOptions(evaluation_type=unreal.AnimDataEvalType.COMPRESSED,should_retarget=True,extract_root_motion=False,incorporate_root_motion_into_pose=True,retrieve_additive_as_full_pose=True,optional_skeletal_mesh=m)
bones=['root','root_x','head_x','spine_01_x','foot_l','foot_r','toes_01_l','toes_01_r']+[b+'_'+s for s in ('l','r') for b in ('shoulder','arm_stretch','forearm_stretch','hand')]
rows=[]
for frame in range(count):
 pose=unreal.AnimPoseExtensions.get_anim_pose_at_frame(a,frame,options)
 assert set(bones).issubset({str(x) for x in unreal.AnimPoseExtensions.get_bone_names(pose)}), 'missing required bones'
 world={};local={}
 for b in bones:
  t=unreal.AnimPoseExtensions.get_bone_pose(pose,b,unreal.AnimPoseSpaces.WORLD);world[b]=[t.translation.x,t.translation.y,t.translation.z]
  if b in ('root','foot_l','foot_r','toes_01_l','toes_01_r'):
   t=unreal.AnimPoseExtensions.get_bone_pose(pose,b,unreal.AnimPoseSpaces.LOCAL)
   local[b]={'p':[t.translation.x,t.translation.y,t.translation.z],'q':[t.rotation.x,t.rotation.y,t.rotation.z,t.rotation.w]}
 rt=unreal.AnimPoseExtensions.get_bone_pose(pose,'root',unreal.AnimPoseSpaces.LOCAL)
 rows.append({'world':world,'local':local,'root_scale':[rt.scale3d.x,rt.scale3d.y,rt.scale3d.z]})
print('MELUSINA_BODY_POSES='+json.dumps({'body':m.get_path_name().split('.')[0],'mode':'COMPRESSED','keys':count,'samples':rows}))
''' % (asset, BODY, BODY, SKELETON)
    result = call('editor', {'action': 'run_python', 'command': command})
    lines = [x.get('output', '') for x in result.get('output', []) if x.get('type') == 'info']
    if not lines or not lines[-1].strip().startswith('MELUSINA_BODY_POSES='):
        raise RuntimeError('actual-body extraction failed; no verified pose payload')
    data = json.loads(lines[-1].strip().split('=', 1)[1])
    if data.get('body') != BODY or data.get('mode') != 'COMPRESSED' or not data.get('keys') or len(data.get('samples', [])) != data['keys']:
        raise RuntimeError('incomplete or wrong-body pose payload')
    validate_pose_payload(data)
    _POSE_CACHE[asset] = data
    return data


def validate_pose_payload(data):
    """Reject malformed joint data anywhere, including the middle of a one-shot."""
    required = {'root','root_x','head_x','spine_01_x','foot_l','foot_r','toes_01_l','toes_01_r'} | {
        b+'_'+s for s in ('l','r') for b in ('shoulder','arm_stretch','forearm_stretch','hand')}
    for row in data['samples']:
        if not required.issubset(row.get('world', {})):
            raise RuntimeError('incomplete actual-body joint payload')
        for values in list(row['world'].values()) + [row.get('root_scale', [])]:
            if len(values) != 3 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in values):
                raise RuntimeError('nonfinite or malformed joint transform')
        for name in ('root','foot_l','foot_r','toes_01_l','toes_01_r'):
            local = row.get('local', {}).get(name, {})
            p, q = local.get('p', []), local.get('q', [])
            if len(p)!=3 or len(q)!=4:
                raise RuntimeError('incomplete local transform payload')
            dist(p,p)
            _quat_angle(q,q)


def check_root_units(asset):
    rows = actual_body_samples(asset)['samples']
    for frame, row in enumerate(rows):
        values = row['root_scale']
        if len(values) != 3 or not all(math.isfinite(float(v)) and abs(v-1.0)<0.01 for v in values):
            return {'pass': False, 'frame': frame, 'reason': 'root scale must be unit', 'scale': values}
        if not all(math.isfinite(float(v)) for v in row['world']['root_x']):
            raise RuntimeError('nonfinite root_x')
    return {'pass': True, 'frames_checked': len(rows)}

# clip class -> acceptable foot_z range (cm, world) for its motion class (informational)
FOOT_CLASS = {
    "idle": (0.0, 6.0), "walk": (0.0, 6.0), "run": (0.0, 8.0), "sprint": (0.0, 10.0),
    "jump": (-20.0, 60.0), "land": (0.0, 20.0), "cast": (-25.0, 15.0),
    "fire": (-25.0, 15.0), "drawback": (-25.0, 15.0), "rmb": (-25.0, 15.0),
    "default": (-30.0, 80.0),
}


def _rpc(req):
    data = json.dumps(req).encode()
    r = urllib.request.Request(MONOLITH, data=data, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=180))


def call(ns, args):
    d = _rpc({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
              "params": {"name": ns + "_query", "arguments": args}})
    txt = None
    for c in d.get("result", {}).get("content", []):
        txt = c.get("text", "")
    if txt is None:
        raise RuntimeError("no result content: %s" % json.dumps(d)[:200])
    try:
        return json.loads(txt)
    except Exception:
        raise RuntimeError("non-JSON result: %s" % txt[:200])


def dist(p, q):
    if not all(math.isfinite(float(v)) for v in (*p[:3], *q[:3])):
        raise RuntimeError("non-finite position")
    return math.sqrt(sum((p[i] - q[i]) ** 2 for i in range(3)))


def bone(asset, b, frame=0):
    return tuple(actual_body_samples(asset)['samples'][frame]['world'][b])


def classify(name):
    n = name.lower()
    # order matters: most specific first
    for k in ("idle", "sprint", "walk", "run", "jump", "land", "cast",
              "fire", "drawback", "rmb"):
        if k in n:
            return k
    return "default"


# clips that are meant to loop seamlessly (seam gate applies). TRUE loops only — one-shots
# (cast/fire/draw/emote) animate THROUGH the clip and will always "fail" a wrap metric, so they
# are exempt from the seam check (their arm canon is still hard-gated).
LOOP_CLASSES = {"idle", "walk", "run", "sprint", "loop", "default"}


def _sample_frames(nf):
    """Every stored key; sparse sampling can miss a single-frame regression."""
    if nf <= 0:
        raise RuntimeError("clip reports no frames; cannot sample arm canon")
    return list(range(nf))


def requires_seam(name):
    n = name.lower()
    return "loop" in n or "glide" in n or classify(name) in {"idle", "walk", "run", "sprint"}


def root_motion_value(info):
    for key in ("has_root_motion", "bEnableRootMotion", "root_motion_enabled"):
        if key in info:
            return info[key]
    return None


def check_arm_canon(asset, contract, nf):
    """Both arms, across the clip. Any unreadable bone/frame raises (-> ERROR), never passes."""
    c = contract["arm_canon_cm"]
    tol = c["tol_cm"]
    worst = {"l": None, "r": None}
    ok = True
    reject = False
    for side in ("l", "r"):
        names = ["shoulder_" + side, "arm_stretch_" + side,
                 "forearm_stretch_" + side, "hand_" + side]
        worst_dev = -1.0
        for fr in _sample_frames(nf):
            pos = [bone(asset, n, fr) for n in names]
            seg = [dist(pos[0], pos[1]), dist(pos[1], pos[2]), dist(pos[2], pos[3])]
            dev = max(abs(seg[i] - c["pass"][i]) for i in range(3))
            if dev >= tol:
                ok = False
            if abs(seg[0] - c["reject"][0]) < 2.0 and abs(seg[1] - c["reject"][1]) < 2.0:
                reject = True
            if dev > worst_dev:
                worst_dev = dev
                worst[side] = {"frame": fr, "measured": [round(x, 3) for x in seg],
                               "max_dev_cm": round(dev, 3)}
    return {"pass": ok, "worst": worst, "canon": c["pass"], "tol_cm": tol,
            "frames_checked": len(_sample_frames(nf)), "reject_signature_hit": reject}


def _quat_angle(a, b):
    """Angle in degrees between two quaternions [x,y,z,w], shortest arc."""
    if not all(math.isfinite(float(v)) for v in (*a, *b)):
        raise RuntimeError("non-finite quaternion")
    na = math.sqrt(sum(v*v for v in a))
    nb = math.sqrt(sum(v*v for v in b))
    if na < 1e-8 or nb < 1e-8:
        raise RuntimeError("zero quaternion")
    dot = abs(sum(a[i] * b[i] for i in range(4))) / (na * nb)
    dot = min(1.0, dot)
    return math.degrees(2.0 * math.acos(dot))


def _track(asset, b):
    return call("animation", {"action": "get_bone_track_keys", "asset_path": asset, "bone_name": b})


def check_seam(asset, nf, gate_cm=1.0, gate_deg=5.0):
    """Loop seam in LOCAL space (the correct loop metric).

    World-space Euler decomposition wraps 360->0 and inflates a clean loop into a false
    '322 degree' seam. Local-space position delta + quaternion angle is the true loop test.
    """
    out = {}
    worst_pos, worst_rot, worst_bone = 0.0, 0.0, None
    for b in ["root", "foot_l", "foot_r", "toes_01_l", "toes_01_r"]:
        try:
            rows = actual_body_samples(asset)['samples']
            first, last = rows[0]['local'][b], rows[-1]['local'][b]
            pd = dist(first['p'], last['p'])
            rd = _quat_angle(first['q'], last['q'])
            out[b] = {"pos_cm": round(pd, 3), "rot_deg": round(rd, 2)}
            if pd > worst_pos:
                worst_pos = pd
            if rd > worst_rot:
                worst_rot, worst_bone = rd, b
        except Exception as e:
            raise RuntimeError("seam: cannot measure %s: %s" % (b, e))
    ok = (worst_pos < gate_cm) and (worst_rot < gate_deg)
    return {"pass": ok, "per_bone": out,
            "worst_pos_cm": round(worst_pos, 3), "worst_rot_deg": round(worst_rot, 2),
            "worst_rot_bone": worst_bone, "gate_cm": gate_cm, "gate_deg": gate_deg}


def check_foot_z(asset, nf, cls):
    lo, hi = FOOT_CLASS[cls]
    step = max(1, (nf or 2) // 16)
    mn = float("inf")
    for fr in range(0, nf or 1, step):
        try:
            mn = min(mn, bone(asset, "foot_l", fr)[2])
            mn = min(mn, bone(asset, "foot_r", fr)[2])
        except Exception:
            pass
    if mn == float("inf"):
        return {"pass": False, "min_z_cm": None, "class": cls, "range": [lo, hi]}
    return {"pass": (lo <= mn <= hi), "min_z_cm": round(mn, 3), "class": cls, "range": [lo, hi]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asset", required=True)
    ap.add_argument("--json", default="")
    ap.add_argument("--seam-gate", type=float, default=1.0)
    args = ap.parse_args()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    name = args.asset.split("/")[-1]
    report = {"asset": args.asset, "contract": str(CONTRACT.relative_to(REPO))}

    try:
        info = call("animation", {"action": "get_sequence_info", "asset_path": args.asset})
        nf = info.get("num_keys") or info.get("num_frames") or 0
        report["frames"] = nf
        report["duration"] = info.get("duration")
        report["root_motion"] = root_motion_value(info)
        report["proof_scope"] = "compressed all-key numeric checks on canonical V2 body; visual/runtime/contact acceptance not established"
        report["runtime_admission"] = "UNVERIFIED"
        report["identity"] = {'clip': asset_identity(args.asset), 'body': asset_identity(BODY),
                              'gate_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                              'contract_sha256': hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
                              'policy_sha256': hashlib.sha256(POLICY.read_bytes()).hexdigest()}
        retired = json.loads(POLICY.read_text(encoding='utf-8'))['runtime_reference_policy']['retired_denylist']
        policy_check = {'pass': package_path(args.asset) not in retired,
                        'reason': retired.get(package_path(args.asset))}
        poses = actual_body_samples(args.asset)
        if poses['keys'] != nf:
            raise RuntimeError('metadata/extracted key count differs')
        root = check_root_units(args.asset)
        heights = [row['world']['root_x'][2] for row in poses['samples']]
        report['root_x_height_range_cm'] = [min(heights), max(heights)]
        report['root_height_scope'] = 'diagnostic only; compare against the motion role, not a standing-height rule'

        arm = check_arm_canon(args.asset, contract, nf)
        is_loop = requires_seam(name)
        seam = check_seam(args.asset, nf, args.seam_gate) if is_loop else {"pass": None}
        foot = check_foot_z(args.asset, nf, classify(name))
        # HARD: arm canon always; seam only on cycling clips. Foot is informational.
        ok = policy_check['pass'] and root['pass'] and arm["pass"] and (seam["pass"] if is_loop else True)
        report["checks"] = {"source_policy": policy_check, "root_units": root, "arm_canon": arm, "loop_seam": seam, "foot_z": foot}
        report["checks"]["loop_seam"]["applies"] = is_loop
        report["verdict"] = "PASS" if ok else "FAIL"
    except Exception as e:
        report["verdict"] = "ERROR"
        report["error"] = str(e)[:300]
        ok = False

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return {"PASS": 0, "FAIL": 1}.get(report["verdict"], 2)


if __name__ == "__main__":
    sys.exit(main())
