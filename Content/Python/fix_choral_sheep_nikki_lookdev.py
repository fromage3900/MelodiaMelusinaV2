#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_choral_sheep_nikki_lookdev.py - Choral Sheep Nikki lookdev material repair
==============================================================================

Purpose (owner-facing):
  Bring the 12 chromatic Choral Sheep coat material instances onto the approved
  Nikki-derived character material path, and pin the cymatic layer to its REST
  state so editor/lookdev captures read as a soft creature first.

What it does (idempotent - safe to re-run):
  1. MI_ChoralSheep_Body : set scalar HarmonizeActive = 0.0 (REST at rest; the
     runtime MID drives Harmonize; a lit cymatic layer at rest fights the
     "lovable creature readability before VFX" rule).
  2. MI_ChoralSheep_Body_Chladni_C / _CE / _CEG : VERIFY (repair only if
     drifted): parent = MI_ChoralSheep_Body, HarmonizeActive 1.0,
     ChladniIntensity 2.5, ChladniEmissiveStrength 3.5, and their respective
     ChladniPatternTexture (T_Chladni_C_ROOT / T_Chladni_CE_ROOT /
     T_Chladni_CEG_ROOT, matched by asset NAME - two folder copies exist).
  3. 12 x MI_ChoralSheep_Coat_PC* : reparent M_Chorus_Wool_Master ->
     MI_ChoralSheep_Body, then explicitly re-apply every per-pitch-class
     parameter from the embedded COATS table below (values transcribed from the
     2026-10-19 coat audit; identical to the live readbacks), then
     update_material_instance + save_loaded_asset(only_if_is_dirty=False).
  4. Write a full before/after receipt (parent, scalars, vectors, textures) to
       Saved/Audit/choral_sheep_nikki_lookdev_20261019.json
     and print a JSON summary to stdout.

Canon:
  - Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md s3 (material authority:
    MI_ChoralSheep_Body -> M_Master_Toon_Character is the approved path;
    M_Chorus_Wool_Master is superseded - it is abandoned here, NOT deleted).
  - Docs/Semester/CHORAL_SHEEP_CAPSTONE_REVIEW_2026-09-08.md s2.5 (owner
    material authority lock: all final Sheep lookdev MUST use the Nikki path).

Run inside UE Editor Python:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/fix_choral_sheep_nikki_lookdev.py", encoding="utf-8").read())

Notes:
  - Texture paths for the coats are the canonical
    /Game/Melodia/Companions/ChoralSheep/Textures/Chladni/T_Chladni_PC_<Pitch>.
  - PCB never carried Character* overrides under M_Chorus_Wool_Master; its
    Character* values mirror its legacy Base/Sheen/Emissive/FabricSheen per the
    convention every other coat follows (CharacterBaseTint == BaseTint, etc.).
    CharacterRoughnessBlend is intentionally omitted for PCB (never carried).
  - Inert legacy overrides (Albedo/NormalMap/ORM/HeightMap/TextureWeight/...)
    may survive reparenting in the MI override arrays; they do not render under
    the new parent chain. They are recorded in the receipt, not deleted.
  - Never touches anything under Content/TurnBasedJRPGTemplate/Blueprints/Skills/
    (fatal Python-glue enum landmine) - this script only touches ChoralSheep MIs.
"""

import json
import os
import unreal

TAG = "[sheep-lookdev]"

# ------------------------------------------------------------------ paths ---
CHORAL_SHEEP_DIR = "/Game/Melodia/Companions/ChoralSheep"
BODY_MI_PATH = CHORAL_SHEEP_DIR + "/MI_ChoralSheep_Body"
MATERIALS_DIR = CHORAL_SHEEP_DIR + "/Materials"
CHLADNI_TEX_DIR = CHORAL_SHEEP_DIR + "/Textures/Chladni"

OLD_COAT_MASTER = MATERIALS_DIR + "/M_Chorus_Wool_Master"
EXPECTED_BODY_PARENT = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Character"

RECEIPT_RELATIVE = "Saved/Audit/choral_sheep_nikki_lookdev_20261019.json"

REFERENCES = [
    "Docs/References/ChoralSheepCapstone/AGENT_CONTEXT.md#3-material-authority",
    "Docs/Semester/CHORAL_SHEEP_CAPSTONE_REVIEW_2026-09-08.md#25-owner-material-authority-lock",
    "coat audit 2026-10-19 (sheep_coat_and_ui_audit.json -> coat_dump)",
]

# ------------------------------------------------------------------ expected ---
TOLERANCE = 1e-3  # audit values are 4-decimal rounded; MIs store float32

# REST state for the hero body instance (runtime MID owns Harmonize in-game).
BODY_HARMONIZE_ACTIVE_REST = 0.0

# The three Chladni fleece consumers must stay lit for Harmonize proof captures.
CHLADNI_EXPECTED_SCALARS = {
    "HarmonizeActive": 1.0,
    "ChladniIntensity": 2.5,
    "ChladniEmissiveStrength": 3.5,
}

CHLADNI_MIS = [
    {"name": "MI_ChoralSheep_Body_Chladni_C", "texture_name": "T_Chladni_C_ROOT"},
    {"name": "MI_ChoralSheep_Body_Chladni_CE", "texture_name": "T_Chladni_CE_ROOT"},
    {"name": "MI_ChoralSheep_Body_Chladni_CEG", "texture_name": "T_Chladni_CEG_ROOT"},
]

# Shared cymatic parameter values re-applied on every coat (from the audit:
# identical across all 12 coats). HarmonizeActive 0.0 = REST; the runtime MID
# drives it so the cymatic layer only lights during Harmonize.
COAT_SHARED_SCALARS = {
    "ChladniIntensity": 1.0,
    "ChladniEmissiveStrength": 2.0,
    "ChladniSheenStrength": 0.5,
    "HarmonizeActive": BODY_HARMONIZE_ACTIVE_REST,
}

COAT_GENERIC_SCALARS = {
    "CharacterRoughnessBlend": 1.0,
    "RoughnessScale": 1.0,
    "ChladniUVTiling": 1.0,
    "BeatAccent": 1.0,
    "TextureWeight": 1.3944,
}

# PCB is the one coat that never carried the full chromatic parameter set.
COAT_GENERIC_SCALARS_PCB = {
    "RoughnessScale": 1.0,
    "ChladniUVTiling": 1.0,
    "BeatAccent": 1.0,
    "TextureWeight": 1.3944,
    "Roughness": 0.954,
}

PCB_NOTE = (
    "PCB had no Character* overrides under M_Chorus_Wool_Master; Character* "
    "values mirror its legacy Base/Sheen/Emissive/FabricSheen per the "
    "convention every other coat follows (CharacterBaseTint==BaseTint, "
    "CharacterHeroSheenColor==SheenTint, CharacterEmissiveBase==EmissiveMapTint, "
    "CharacterHeroSheenStrength==FabricSheen). CharacterRoughnessBlend "
    "intentionally omitted (never carried)."
)

PCC_EXTRA_VECTORS = {
    "ChladniPearlSilkColor": (0.96, 0.91, 0.96, 1.0),
    "ChladniLilacHaloColor": (0.58, 0.4, 0.72, 1.0),
}


def _coat(name, pitch, sheen, base_tint, hero_sheen, emissive,
          generic=None, extra_vectors=None, note=None):
    """Build one coat's expected-parameter entry.

    Every coat follows the audit's mirror convention:
      CharacterBaseTint == BaseTint, CharacterHeroSheenColor == SheenTint,
      CharacterEmissiveBase == EmissiveMapTint, CharacterHeroSheenStrength == FabricSheen.
    """
    generics = dict(COAT_GENERIC_SCALARS_PCB if name.endswith("_PCB") else COAT_GENERIC_SCALARS)
    if generic:
        generics.update(generic)
    return {
        "name": name,
        "object_path": MATERIALS_DIR + "/" + name,
        "old_parent": OLD_COAT_MASTER,
        "pitch": pitch,
        "texture_name": "T_Chladni_PC_" + pitch,
        "texture_object_path": CHLADNI_TEX_DIR + "/T_Chladni_PC_" + pitch,
        "scalars": dict(
            {
                "CharacterHeroSheenStrength": sheen,
                "FabricSheen": sheen,
            },
            **generics,
            **COAT_SHARED_SCALARS,
        ),
        "vectors": dict(
            {
                "CharacterBaseTint": tuple(base_tint),
                "BaseTint": tuple(base_tint),
                "CharacterHeroSheenColor": tuple(hero_sheen),
                "SheenTint": tuple(hero_sheen),
                "CharacterEmissiveBase": tuple(emissive),
                "EmissiveMapTint": tuple(emissive),
            },
            **(extra_vectors or {}),
        ),
        "note": note or "",
    }


# Chromatic circle order (A, As, B, C, Cs, D, Ds, E, F, Fs, G, Gs) - all 12
# pitch classes from the 2026-10-19 audit.
COATS = [
    _coat("MI_ChoralSheep_Coat_PCA", "A", 0.595,
          (0.8239, 0.7277, 0.92, 1.0), (0.7899, 0.6046, 0.9752, 1.0), (0.158, 0.1209, 0.195, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCAs", "As", 0.61,
          (0.9196, 0.7277, 0.92, 1.0), (0.9745, 0.6046, 0.9752, 1.0), (0.1949, 0.1209, 0.195, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCB", "B", 0.625,
          (0.92, 0.7277, 0.8235, 1.0), (0.9752, 0.6046, 0.7892, 1.0), (0.195, 0.1209, 0.1578, 1.0),
          note=PCB_NOTE),
    _coat("MI_ChoralSheep_Coat_PCC", "C", 0.46,
          (0.92, 0.7277, 0.7277, 1.0), (0.9752, 0.6046, 0.6046, 1.0), (0.195, 0.1209, 0.1209, 1.0),
          extra_vectors=PCC_EXTRA_VECTORS),
    _coat("MI_ChoralSheep_Coat_PCCs", "Cs", 0.475,
          (0.92, 0.8235, 0.7277, 1.0), (0.9752, 0.7892, 0.6046, 1.0), (0.195, 0.1578, 0.1209, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCD", "D", 0.49,
          (0.9196, 0.92, 0.7277, 1.0), (0.9745, 0.9752, 0.6046, 1.0), (0.1949, 0.195, 0.1209, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCDs", "Ds", 0.505,
          (0.8239, 0.92, 0.7277, 1.0), (0.7899, 0.9752, 0.6046, 1.0), (0.158, 0.195, 0.1209, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCE", "E", 0.52,
          (0.7281, 0.92, 0.7277, 1.0), (0.6054, 0.9752, 0.6046, 1.0), (0.1211, 0.195, 0.1209, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCF", "F", 0.535,
          (0.7277, 0.92, 0.8242, 1.0), (0.6046, 0.9752, 0.7907, 1.0), (0.1209, 0.195, 0.1581, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCFs", "Fs", 0.55,
          (0.7277, 0.92, 0.92, 1.0), (0.6046, 0.9752, 0.9752, 1.0), (0.1209, 0.195, 0.195, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCG", "G", 0.565,
          (0.7277, 0.8242, 0.92, 1.0), (0.6046, 0.7907, 0.9752, 1.0), (0.1209, 0.1581, 0.195, 1.0)),
    _coat("MI_ChoralSheep_Coat_PCGs", "Gs", 0.58,
          (0.7281, 0.7277, 0.92, 1.0), (0.6054, 0.6046, 0.9752, 1.0), (0.1211, 0.1209, 0.195, 1.0)),
]

# ------------------------------------------------------------------ readbacks ---


def _field(struct, prop, default=None):
    try:
        return struct.get_editor_property(prop)
    except Exception:
        return default


def _obj_path(obj):
    """Object path ('/Game/.../Asset') without the '.SubObject' suffix."""
    if obj is None:
        return None
    try:
        full = obj.get_path_name()
    except Exception:
        full = str(obj)
    return full.split(".")[0] if full else None


def _param_name(param):
    try:
        info = param.get_editor_property("parameter_info")
        if info is not None:
            return str(info.name)
    except Exception:
        pass
    return str(_field(param, "parameter_name", "") or "")


def read_full_mi_state(mi):
    """Full override readback: parent + scalars + vectors + textures.

    Reads the MI's own override arrays (parameters set *on* this instance);
    values inherited from the parent chain are simply absent here.
    """
    state = {"parent": None, "scalars": {}, "vectors": {}, "textures": {}}
    try:
        state["parent"] = _obj_path(mi.get_editor_property("parent"))
    except Exception as exc:
        state["parent_error"] = str(exc)
    try:
        for sp in mi.get_editor_property("scalar_parameter_values"):
            pname = _param_name(sp)
            if pname:
                state["scalars"][pname] = float(_field(sp, "parameter_value", 0.0) or 0.0)
    except Exception as exc:
        state["scalars_error"] = str(exc)
    try:
        for vp in mi.get_editor_property("vector_parameter_values"):
            pname = _param_name(vp)
            col = _field(vp, "parameter_value", None)
            if pname and col is not None:
                state["vectors"][pname] = [
                    float(col.r), float(col.g), float(col.b), float(col.a),
                ]
    except Exception as exc:
        state["vectors_error"] = str(exc)
    try:
        for tp in mi.get_editor_property("texture_parameter_values"):
            pname = _param_name(tp)
            tex = _field(tp, "parameter_value", None)
            if pname:
                state["textures"][pname] = _obj_path(tex)
    except Exception as exc:
        state["textures_error"] = str(exc)
    return state


def _close(actual, expected, tol=TOLERANCE):
    return actual is not None and abs(float(actual) - float(expected)) <= tol


def _vectors_match(actual, expected_rgba, tol=TOLERANCE):
    return (
        isinstance(actual, (list, tuple))
        and len(actual) == 4
        and all(abs(float(a) - float(e)) <= tol for a, e in zip(actual, expected_rgba))
    )


def _tex_name(object_path):
    if not object_path:
        return None
    return object_path.rstrip("/").rsplit("/", 1)[-1]


def verify_entry(state, expected_parent, expected_scalars, expected_vectors,
                 expected_texture_name=None, expected_texture_path=None):
    """Compare a readback state against expectations -> {..ok flags.., 'pass'}."""
    result = {"scalars": {}, "vectors": {}, "textures": {}}
    ok = True

    result["parent_expected"] = expected_parent
    result["parent_actual"] = state.get("parent")
    result["parent_ok"] = state.get("parent") == expected_parent
    ok = ok and result["parent_ok"]

    for name, expected in expected_scalars.items():
        actual = state["scalars"].get(name)
        good = _close(actual, expected)
        result["scalars"][name] = {"expected": expected, "actual": actual, "ok": good}
        ok = ok and good

    for name, expected in expected_vectors.items():
        actual = state["vectors"].get(name)
        good = _vectors_match(actual, expected)
        result["vectors"][name] = {"expected": list(expected), "actual": actual, "ok": good}
        ok = ok and good

    if expected_texture_name is not None:
        actual = state["textures"].get("ChladniPatternTexture")
        # ROOT textures exist as duplicates in Textures/ and Textures/Chladni/;
        # match by asset NAME so either canonical copy passes.
        good = _tex_name(actual) == expected_texture_name
        result["textures"]["ChladniPatternTexture"] = {
            "expected_name": expected_texture_name, "actual": actual, "ok": good,
        }
        ok = ok and good
    elif expected_texture_path is not None:
        actual = state["textures"].get("ChladniPatternTexture")
        good = actual == expected_texture_path
        result["textures"]["ChladniPatternTexture"] = {
            "expected": expected_texture_path, "actual": actual, "ok": good,
        }
        ok = ok and good

    result["pass"] = ok
    return result


# ------------------------------------------------------------------ actions ---


def load_asset(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        unreal.log_warning("%s ERROR: asset not found: %s" % (TAG, path))
    return asset


def apply_scalar(mi, name, value):
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, name, float(value))


def apply_vector(mi, name, rgba):
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        mi, name, unreal.LinearColor(rgba[0], rgba[1], rgba[2], rgba[3]))


def apply_texture(mi, name, texture_object):
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, name, texture_object)


def fix_body_mi(receipt):
    """HarmonizeActive = 0.0 at REST on MI_ChoralSheep_Body."""
    mi = load_asset(BODY_MI_PATH)
    if mi is None:
        receipt["body_mi"] = {"path": BODY_MI_PATH, "error": "load failed"}
        return None
    before = read_full_mi_state(mi)
    apply_scalar(mi, "HarmonizeActive", BODY_HARMONIZE_ACTIVE_REST)
    unreal.MaterialEditingLibrary.update_material_instance(mi)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(mi, False)
    after = read_full_mi_state(mi)
    verification = verify_entry(
        after,
        expected_parent=EXPECTED_BODY_PARENT,
        expected_scalars={"HarmonizeActive": BODY_HARMONIZE_ACTIVE_REST},
        expected_vectors={},
    )
    entry = {
        "path": BODY_MI_PATH,
        "action": "set HarmonizeActive=%s (REST; runtime MID drives it)" % BODY_HARMONIZE_ACTIVE_REST,
        "before": before,
        "after": after,
        "saved": bool(saved),
        "verification": verification,
        "note": "parent is verify-only: expected M_Master_Toon_Character per canon; not reparented here.",
    }
    receipt["body_mi"] = entry
    unreal.log("%s MI_ChoralSheep_Body HarmonizeActive -> %s" % (TAG, BODY_HARMONIZE_ACTIVE_REST))
    return mi


def fix_chladni_mi(entry_spec, mi_body, receipt):
    """Verify (repair only if drifted) one MI_ChoralSheep_Body_Chladni_*."""
    path = CHORAL_SHEEP_DIR + "/" + entry_spec["name"]
    mi = load_asset(path)
    if mi is None:
        receipt["chladni_instances"].append(
            {"path": path, "error": "load failed", "verification": {"pass": False}})
        return None
    before = read_full_mi_state(mi)
    repairs = []

    if before.get("parent") != BODY_MI_PATH:
        unreal.MaterialEditingLibrary.set_material_instance_parent(mi, mi_body)
        repairs.append("parent -> %s" % BODY_MI_PATH)

    for pname, expected in sorted(CHLADNI_EXPECTED_SCALARS.items()):
        if not _close(before["scalars"].get(pname), expected):
            apply_scalar(mi, pname, expected)
            repairs.append("scalar %s=%s" % (pname, expected))

    tex_actual = before["textures"].get("ChladniPatternTexture")
    if _tex_name(tex_actual) != entry_spec["texture_name"]:
        tex = None
        for candidate in (
            CHLADNI_TEX_DIR + "/" + entry_spec["texture_name"],
            CHORAL_SHEEP_DIR + "/Textures/" + entry_spec["texture_name"],
        ):
            tex = load_asset(candidate)
            if tex is not None:
                break
        if tex is not None:
            apply_texture(mi, "ChladniPatternTexture", tex)
            repairs.append("ChladniPatternTexture -> %s" % entry_spec["texture_name"])
        else:
            repairs.append("WARNING: texture %s not found, left untouched" % entry_spec["texture_name"])

    saved = False
    if repairs:
        unreal.MaterialEditingLibrary.update_material_instance(mi)
        saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(mi, False))

    after = read_full_mi_state(mi)
    verification = verify_entry(
        after,
        expected_parent=BODY_MI_PATH,
        expected_scalars=CHLADNI_EXPECTED_SCALARS,
        expected_vectors={},
        expected_texture_name=entry_spec["texture_name"],
    )
    result = {
        "path": path,
        "before": before,
        "after": after,
        "repairs": repairs,
        "saved": saved,
        "verification": verification,
    }
    receipt["chladni_instances"].append(result)
    unreal.log("%s %s verified (repairs: %s)" % (TAG, entry_spec["name"], repairs or "none"))
    return mi


def fix_coat(entry, mi_body, receipt):
    """Reparent one coat onto MI_ChoralSheep_Body and re-apply its parameters."""
    mi = load_asset(entry["object_path"])
    if mi is None:
        receipt["coat_instances"].append(
            {"path": entry["object_path"], "error": "load failed", "verification": {"pass": False}})
        return None
    before = read_full_mi_state(mi)
    actions = []

    if before.get("parent") != BODY_MI_PATH:
        unreal.MaterialEditingLibrary.set_material_instance_parent(mi, mi_body)
        actions.append("parent %s -> %s" % (before.get("parent"), BODY_MI_PATH))

    for pname, value in sorted(entry["scalars"].items()):
        apply_scalar(mi, pname, value)
        actions.append("scalar %s=%s" % (pname, value))

    for pname, rgba in sorted(entry["vectors"].items()):
        apply_vector(mi, pname, rgba)
        actions.append("vector %s=%s" % (pname, tuple(round(c, 4) for c in rgba)))

    tex = load_asset(entry["texture_object_path"])
    if tex is not None:
        apply_texture(mi, "ChladniPatternTexture", tex)
        actions.append("ChladniPatternTexture -> %s" % entry["texture_name"])
    else:
        actions.append("WARNING: texture not found: %s" % entry["texture_object_path"])

    unreal.MaterialEditingLibrary.update_material_instance(mi)
    saved = bool(unreal.EditorAssetLibrary.save_loaded_asset(mi, False))

    after = read_full_mi_state(mi)
    verification = verify_entry(
        after,
        expected_parent=BODY_MI_PATH,
        expected_scalars=entry["scalars"],
        expected_vectors=entry["vectors"],
        expected_texture_path=entry["texture_object_path"],
    )
    result = {
        "path": entry["object_path"],
        "pitch": entry["pitch"],
        "before": before,
        "after": after,
        "actions": actions,
        "saved": saved,
        "verification": verification,
        "note": entry["note"],
    }
    receipt["coat_instances"].append(result)
    unreal.log("%s %s done (parent changed: %s, verify pass: %s)" % (
        TAG, entry["name"], "yes" if "parent" in " ".join(actions) else "no",
        verification["pass"]))
    return mi


# ------------------------------------------------------------------ receipt ---


def _receipt_abs_path():
    for getter in (lambda: unreal.Paths.project_dir(), lambda: unreal.Paths.project_saved_dir()):
        try:
            base = getter()
            if base:
                base = base.rstrip("/")
                if base.endswith("Saved"):
                    return os.path.abspath(base + "/Audit/" + os.path.basename(RECEIPT_RELATIVE))
                return os.path.abspath(base + "/" + RECEIPT_RELATIVE)
        except Exception:
            continue
    return os.path.abspath(RECEIPT_RELATIVE)


def write_receipt(receipt):
    path = _receipt_abs_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, default=str)
    return path


def build_summary(receipt):
    coats = receipt.get("coat_instances", [])
    chladni = receipt.get("chladni_instances", [])
    body = receipt.get("body_mi", {})
    return {
        "receipt": receipt["receipt"],
        "receipt_path": receipt["written_to"],
        "body_mi": {
            "path": body.get("path"),
            "harmonize_active_after": (body.get("after") or {}).get("scalars", {}).get("HarmonizeActive"),
            "saved": body.get("saved"),
            "verify_pass": (body.get("verification") or {}).get("pass"),
        },
        "chladni_instances": {
            "total": len(chladni),
            "repaired": sum(1 for c in chladni if c.get("repairs")),
            "verify_pass": all((c.get("verification") or {}).get("pass") for c in chladni) if chladni else False,
        },
        "coats": {
            "total": len(coats),
            "reparented_to_body": sum(
                1 for c in coats if (c.get("after") or {}).get("parent") == BODY_MI_PATH),
            "verify_pass": all((c.get("verification") or {}).get("pass") for c in coats) if coats else False,
        },
        "all_pass": (
            all((c.get("verification") or {}).get("pass") for c in coats + chladni)
            and bool((body.get("verification") or {}).get("pass"))
        ),
    }


# ------------------------------------------------------------------ main ---


def main():
    receipt = {
        "receipt": "choral_sheep_nikki_lookdev_20261019",
        "script": "Content/Python/fix_choral_sheep_nikki_lookdev.py",
        "references": REFERENCES,
        "body_mi": {},
        "chladni_instances": [],
        "coat_instances": [],
    }

    unreal.log("%s === Choral Sheep Nikki lookdev repair: start ===" % TAG)

    mi_body = fix_body_mi(receipt)
    if mi_body is None:
        unreal.log_error("%s Cannot proceed without MI_ChoralSheep_Body." % TAG)
        return None

    for entry_spec in CHLADNI_MIS:
        fix_chladni_mi(entry_spec, mi_body, receipt)

    for entry in COATS:
        fix_coat(entry, mi_body, receipt)

    receipt["written_to"] = _receipt_abs_path()
    receipt_path = write_receipt(receipt)
    summary = build_summary(receipt)

    unreal.log("%s === done. receipt: %s ===" % (TAG, receipt_path))
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
