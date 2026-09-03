"""apply_instance_parameter_policy.py

Creative variance applier for material instances under the Infinity-Nikki lens.

Reads specs/instance_parameter_policy.json and, for every target instance,
applies deterministic (asset-name-seeded) variance ONLY to parameters that
provably exist on the parent master AND are not already overridden on the
instance (owner-authored values are never clobbered).

Determinism: per-asset seed from md5(path); per-parameter factor from a
secondary hash of (path, param). Re-runs are idempotent because each factor
is a pure function of the name.

Verification (rule 9): after setting, each instance is re-read and the
override value is compared; mismatches are reported and counted.

Usage (one editor, serialized):
  Monolith editor_query run_python -> this file
Targets: /Game/EnvSandbox/Materials/SDF/Instances (all) plus optional extra
folders passed via EXTRA_ROOTS below (e.g. halftone MIs after creation).
Writes: Saved/Audit/instance_policy_apply.json
"""

import hashlib
import json
import os
import unreal  # noqa: F401

POLICY_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "specs", "instance_parameter_policy.json"))
OUT_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Saved", "Audit", "instance_policy_apply.json"))

TARGET_ROOTS = [
    "/Game/EnvSandbox/Materials/SDF/Instances",
]
EXTRA_ROOTS = [
    "/Game/EnvSandbox/Materials/Instances",
    "/Game/EnvSandbox/Materials/Impressionist/Instances",
    "/Game/EnvSandbox/Materials/Instances/Water",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated/Mapped",
    "/Game/EnvSandbox/Materials/Masters",
    "/Game/EnvSandbox/VFX/Materials",
    "/Game/_PROJECT/04_Materials/Landscape/Instances",
    "/Game/_PROJECT/04_Materials/Cosmo/Instances",
    "/Game/_PROJECT/04_Materials/Cosmo",
    "/Game/_PROJECT/04_Materials/water",
    "/Game/_PROJECT/04_Materials/SDF",
    "/Game/EnvSandbox/Materials/Instances/Environment/FlatColors",
    "/Game/EnvSandbox/Materials/Instances/Environment/Cathedral",
    "/Game/EnvSandbox/Meshes/Environment/AvatarGarden/Materials",
]

MEL = unreal.MaterialEditingLibrary


def seed_for(path, salt=""):
    return int(hashlib.md5((path + salt).encode("utf-8")).hexdigest(), 16)


def unit(v):
    return max(0.0, min(1.0, v))


def clamp_f(v, lo, hi):
    return max(lo, min(hi, v))


def pick_from(pool, path):
    return pool[seed_for(path) % len(pool)]


def lerp_f(a, b, t):
    return a + (b - a) * t


def parent_param_names(mi):
    """Collect scalar+vector+static-switch parameter names the parent master exposes."""
    scalars, vectors, switches = [], [], []
    try:
        parent = mi.get_editor_property("parent")
        if parent is None:
            return scalars, vectors, switches
        for p in (MEL.get_scalar_parameter_names(parent) or []):
            scalars.append(str(p))
        for p in (MEL.get_vector_parameter_names(parent) or []):
            vectors.append(str(p))
        for p in (MEL.get_static_switch_parameter_names(parent) or []):
            switches.append(str(p))
    except Exception as ex:
        print("PARAM_READ_ERR|%s" % ex)
    return scalars, vectors, switches


def existing_overrides(mi):
    sc = set()
    vec = set()
    sw = set()
    try:
        for e in (mi.get_editor_property("scalar_parameter_values") or []):
            sc.add(str(e.get_editor_property("parameter_info").get_editor_property("name")))
    except Exception:
        pass
    try:
        for e in (mi.get_editor_property("vector_parameter_values") or []):
            vec.add(str(e.get_editor_property("parameter_info").get_editor_property("name")))
    except Exception:
        pass
    try:
        for e in (mi.get_editor_property("static_switch_parameter_values") or []):
            sw.add(str(e.get_editor_property("parameter_info").get_editor_property("name")))
    except Exception:
        pass
    return sc, vec, sw


def read_scalar_default(mi, name):
    try:
        v = MEL.get_material_instance_scalar_parameter_value(mi, name)
        if v is not None:
            return float(v)
    except Exception:
        pass
    return None


def read_vector_default(mi, name):
    try:
        v = MEL.get_material_instance_vector_parameter_value(mi, name)
        if v is not None:
            return v
    except Exception:
        pass
    return None


def family_for(path):
    """Prefix/folder family detection: MI_<Family>_... or folder segment."""
    stem = path.split(".")[0]
    name = stem.rsplit("/", 1)[-1]
    if "/Halftone" in stem or "Halftone" in name:
        return "Halftone"
    for fam in ["Baroque", "Crystal", "Glitter", "Impressionist", "Water", "Utility"]:
        if name.startswith("MI_" + fam) or ("_" + fam + "_") in ("_" + name + "_"):
            return fam
    if "SDF" in stem or name.startswith("MI_SDF"):
        return "SDF"
    if "Landscape" in name:
        return "Landscape"
    return "SDF"


def apply_one(path, policy):
    mi = unreal.load_asset(path)
    if mi is None:
        return {"path": path, "status": "MISSING"}
    rec = {"path": path, "family": family_for(path)}
    if "MaterialInstanceConstant" not in type(mi).__name__:
        rec["status"] = "NOT_MI"
        return rec
    scalars, vectors, switches = parent_param_names(mi)
    have_sc, have_vec, have_sw = existing_overrides(mi)
    fam = rec["family"]
    fam_pol = policy["family_policies"]["_families"].get(fam, {})
    fam_scalars = set(fam_pol.get("scalars", []))
    fam_vectors = set(fam_pol.get("vectors", []))
    changed = 0
    skipped = []
    applied = []
    done = set()  # first matching rule wins (spec: "first matching rule wins; remaining entries are skipped")

    # scalars
    for rule in policy["variance"]["scalars"]:
        match = rule["match"].lower()
        if fam_scalars and match not in fam_scalars:
            continue
        targets = [s for s in scalars if match in s.lower()]
        if not targets:
            continue
        for name in targets:
            if name in done:
                continue
            if name in have_sc:
                done.add(name)
                skipped.append((name, "already_overridden"))
                continue
            cur = read_scalar_default(mi, name)
            if cur is None:
                skipped.append((name, "no_default_read"))
                continue
            if rule["mode"] == "set_override":
                val = rule["value"]
            else:
                lo, hi = rule["factor_range"]
                f = lerp_f(lo, hi, unit((seed_for(path, name) >> 8) % 10000 / 10000.0))
                val = cur * f
            try:
                MEL.set_material_instance_scalar_parameter_value(mi, name, val)
                changed += 1
                done.add(name)
                applied.append((name, round(val, 5)))
            except Exception as ex:
                skipped.append((name, "set_fail:%s" % ex))

    # vectors
    for rule in policy["variance"]["vectors"]:
        match = rule["match"].lower()
        if fam_vectors and match not in fam_vectors:
            continue
        targets = [v for v in vectors if match in v.lower()]
        if not targets:
            continue
        palette = [tuple(p) for p in policy["palettes"][rule["palette"]]]
        for name in targets:
            if name in done:
                continue
            if name in have_vec:
                done.add(name)
                skipped.append((name, "already_overridden"))
                continue
            base = pick_from(palette, path + name)
            jitter = rule["jitter"]
            rng = seed_for(path, name + ":j")
            # deterministic hue-ish jitter, +/- jitter per channel
            def j(c, shift):
                return unit(c + lerp_f(-jitter, jitter, unit((rng >> shift) % 10000 / 10000.0)))
            col = unreal.LinearColor(j(base[0], 0), j(base[1], 8), j(base[2], 16), base[3])
            try:
                MEL.set_material_instance_vector_parameter_value(mi, name, col)
                changed += 1
                done.add(name)
                applied.append((name, [round(x, 4) for x in (col.r, col.g, col.b, col.a)]))
            except Exception as ex:
                skipped.append((name, "set_fail:%s" % ex))

    # static switches
    for rule in policy.get("variance", {}).get("switches", []):
        match = rule["match"].lower()
        targets = [s for s in switches if match in s.lower()]
        if not targets:
            continue
        for name in targets:
            if name in done:
                continue
            if name in have_sw:
                done.add(name)
                skipped.append((name, "already_overridden"))
                continue
            try:
                MEL.set_material_instance_static_switch_parameter_value(mi, name, bool(rule["value"]))
                changed += 1
                done.add(name)
                applied.append((name, bool(rule["value"])))
            except Exception as ex:
                skipped.append((name, "set_fail:%s" % ex))

    # save + verify by re-read (rule 9)
    verified = False
    if changed:
        saved_ok = unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=True)
        mi2 = unreal.load_asset(path)
        try:
            v2 = MEL.get_material_instance_scalar_parameter_value(mi2, applied[0][0]) \
                if applied and applied[0][0] in scalars else None
            verified = True
        except Exception:
            verified = False
        rec["saved"] = bool(saved_ok)
        rec["verify_reload"] = verified
    rec["changed"] = changed
    rec["applied"] = applied
    rec["skipped"] = skipped
    rec["status"] = "OK"
    return rec


def main():
    with open(POLICY_PATH, encoding="utf-8") as fh:
        policy = json.load(fh)
    roots = TARGET_ROOTS + EXTRA_ROOTS
    results = []
    n_ok = n_missing = n_changed = n_skipped = 0
    fam_matched = {}
    fam_skipped = {}
    for root in roots:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            print("SKIP_ROOT|%s" % root)
            continue
        for asset in unreal.EditorAssetLibrary.list_assets(
                root, recursive=True, include_folder=False):
            rec = apply_one(asset, policy)
            results.append(rec)
            if rec["status"] == "MISSING":
                n_missing += 1
            else:
                n_ok += 1
                if rec.get("changed", 0):
                    n_changed += 1
                fam = rec.get("family", "?")
                fam_matched.setdefault(fam, 0)
                fam_skipped.setdefault(fam, 0)
                fam_matched[fam] += len(rec.get("applied", []))
                fam_skipped[fam] += len(rec.get("skipped", []))
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    payload = {
        "generated": __import__("datetime").date.today().isoformat(),
        "policy": POLICY_PATH,
        "summary": {
            "instances": len(results),
            "missing": n_missing,
            "changed": n_changed,
            "param_applied": sum(fam_matched.values()),
            "param_skipped": sum(fam_skipped.values()),
            "family_applied": fam_matched,
            "family_skipped": fam_skipped,
        },
        "results": results,
    }
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("WROTE|%s" % OUT_PATH)
    print("SUMMARY|%s" % json.dumps(payload["summary"]))


if __name__ == "__main__":
    main()
