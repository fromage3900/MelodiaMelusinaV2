"""extract_owner_instance_profiles.py

Fold-in tool: dump every owner-authored/edited material instance's parameter
overrides (scalars, vectors, textures) so their "good working instance" choices
become a reusable policy specimen.

Run via Monolith editor_query run_python (one editor, serialized). Writes:
  Saved/Audit/owner_instance_profiles.json
Prints a summary of parameter-name frequency across the owner's instances —
that vocabulary drives specs/instance_parameter_policy.json.

Scopes (owner-authored roots; add more as discovered):
  /Game/EnvSandbox/Materials/Instances/Environment
  /Game/EnvSandbox/Materials/Impressionist/Instances
  /Game/EnvSandbox/Materials/Instances/Landscape
  /Game/EnvSandbox/Materials/Instances/Showcase
  /Game/EnvSandbox/Materials/Instances/Character
  /Game/EnvSandbox/Materials/Instances/Sakura
  /Game/EnvSandbox/Materials/Instances/NikkiHero
  /Game/EnvSandbox/Materials/Instances/NikkiIntegrated
  /Game/EnvSandbox/Materials/Instances/Water
  /Game/EnvSandbox/Materials/Instances/Rhythm
  /Game/EnvSandbox/Materials/Instances/MelodyTokens
  /Game/EnvSandbox/Materials/Instances/Grotto
  /Game/Melodia/Characters
"""

import json
import os
import unreal  # noqa: F401  (editor context)

ROOTS = [
    "/Game/EnvSandbox/Materials/Instances/Environment",
    "/Game/EnvSandbox/Materials/Impressionist/Instances",
    "/Game/EnvSandbox/Materials/Instances/Landscape",
    "/Game/EnvSandbox/Materials/Instances/Showcase",
    "/Game/EnvSandbox/Materials/Instances/Character",
    "/Game/EnvSandbox/Materials/Instances/Sakura",
    "/Game/EnvSandbox/Materials/Instances/NikkiHero",
    "/Game/EnvSandbox/Materials/Instances/NikkiIntegrated",
    "/Game/EnvSandbox/Materials/Instances/Water",
    "/Game/EnvSandbox/Materials/Instances/Rhythm",
    "/Game/EnvSandbox/Materials/Instances/MelodyTokens",
    "/Game/EnvSandbox/Materials/Instances/Grotto",
    "/Game/Melodia/Characters",
]

OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Saved", "Audit", "owner_instance_profiles.json"))


def _name_of(info):
    try:
        return str(info.get_editor_property("name"))
    except Exception:
        return "<anon>"


def dump_instance(mi):
    """Return {parent, scalars, vectors, textures} for one MI."""
    out = {}
    try:
        parent = mi.get_editor_property("parent")
        out["parent"] = parent.get_path_name() if parent else "<NONE>"
    except Exception:
        out["parent"] = "<ERR>"
    scalars = {}
    try:
        for e in (mi.get_editor_property("scalar_parameter_values") or []):
            scalars[_name_of(e.get_editor_property("parameter_info"))] = round(
                e.get_editor_property("parameter_value"), 5)
    except Exception:
        pass
    vectors = {}
    try:
        for e in (mi.get_editor_property("vector_parameter_values") or []):
            v = e.get_editor_property("parameter_value")
            vectors[_name_of(e.get_editor_property("parameter_info"))] = [
                round(x, 4) for x in (v.r, v.g, v.b, v.a)]
    except Exception:
        pass
    textures = {}
    try:
        for e in (mi.get_editor_property("texture_parameter_values") or []):
            tex = e.get_editor_property("parameter_value")
            textures[_name_of(e.get_editor_property("parameter_info"))] = (
                tex.get_path_name() if tex else None)
    except Exception:
        pass
    out["scalars"] = scalars
    out["vectors"] = vectors
    out["textures"] = textures
    out["override_count"] = len(scalars) + len(vectors) + len(textures)
    return out


def main():
    results = {}
    by_parent = {}
    scalar_freq = {}
    vector_freq = {}
    n_mi = 0
    n_with_overrides = 0
    for root in ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            print("SKIP|%s" % root)
            continue
        for asset in unreal.EditorAssetLibrary.list_assets(
                root, recursive=True, include_folder=False):
            mi = unreal.load_asset(asset)
            if mi is None:
                continue
            cls = type(mi).__name__
            if "MaterialInstanceConstant" not in cls:
                continue
            n_mi += 1
            key = asset.split(".")[0]
            rec = dump_instance(mi)
            results[key] = rec
            p = rec["parent"]
            by_parent.setdefault(p, []).append(key)
            if rec["override_count"]:
                n_with_overrides += 1
            for name in rec["scalars"]:
                scalar_freq[name] = scalar_freq.get(name, 0) + 1
            for name in rec["vectors"]:
                vector_freq[name] = vector_freq.get(name, 0) + 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    payload = {
        "generated": __import__("datetime").date.today().isoformat(),
        "note": "Owner-authored MI parameter overrides (fold-in specimen).",
        "summary": {
            "instances": n_mi,
            "with_overrides": n_with_overrides,
            "parents": sorted(by_parent, key=lambda k: -len(by_parent[k])),
        },
        "scalar_frequency": sorted(scalar_freq.items(), key=lambda kv: -kv[1]),
        "vector_frequency": sorted(vector_freq.items(), key=lambda kv: -kv[1]),
        "instances": results,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print("WROTE|%s" % OUT)
    print("SUMMARY|instances=%d|with_overrides=%d" % (n_mi, n_with_overrides))
    print("TOP_SCALARS|%s" % json.dumps(payload["scalar_frequency"][:20]))
    print("TOP_VECTORS|%s" % json.dumps(payload["vector_frequency"][:10]))
    for p in payload["summary"]["parents"][:12]:
        print("PARENT|%d|%s" % (len(by_parent[p]), p))


if __name__ == "__main__":
    main()
