"""Viseme mapper ΓÇö phoneme-to-viseme lookup with auto-detection of rig blendshapes.

Subdivides the standard anime-style 15-viseme set into blendshape weight maps
for Pixar-style facial rigs. Auto-scans armature shape keys to bind visemes
to the actual blendshape names on the target rig.

Reference: Preston Blair phoneme set extended with anime mouth shapes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import ClassVar


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Standard phoneme ΓåÆ viseme mapping (Preston Blair + anime extended)
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

@dataclass
class VisemeDef:
    """One viseme: a named mouth shape with canonical blendshape name hints."""
    code: str                           # e.g. "AA", "EE", "M"
    label: str                          # human-readable
    shape_keys: list[str]               # blendshape name patterns (order = priority)
    jaw: float = 0.0                    # jaw open amount 0-1
    lips: float = 0.0                   # lip rounding 0-1
    tongue: float = 0.0                 # tongue visibility 0-1


# Canonical viseme set
VISEMES: ClassVar[list[VisemeDef]] = [
    VisemeDef("rest",  "Rest / Neutral",   ["Mouth_Rest", "Rest", "Neutral", "mouth_rest"]),
    VisemeDef("AA",    "Ah (father)",       ["Mouth_AA", "AA", "Ah", "Mouth_Ah", "mouth_aa", "mouth_ah", "Mouth_Open"],              jaw=0.9),
    VisemeDef("EE",    "Ee (see)",          ["Mouth_EE", "EE", "Ee", "Mouth_Ee", "mouth_ee", "Mouth_Smile", "Smile"],               lips=-0.3, jaw=0.2),
    VisemeDef("IH",    "Ih (sit)",          ["Mouth_IH", "IH", "Ih", "mouth_ih"],                                                    jaw=0.3),
    VisemeDef("EH",    "Eh (bed)",          ["Mouth_EH", "EH", "Eh", "mouth_eh"],                                                    jaw=0.4),
    VisemeDef("OO",    "Oo (boot)",         ["Mouth_OO", "OO", "Oo", "Mouth_Oo", "mouth_oo", "Mouth_Purse", "Purse"],               lips=0.9, jaw=0.1),
    VisemeDef("OH",    "Oh (boat)",         ["Mouth_OH", "OH", "Oh", "mouth_oh"],                                                    lips=0.5, jaw=0.4),
    VisemeDef("CH",    "Ch/J/Sh (cheese)",  ["Mouth_CH", "CH", "Ch", "Mouth_Sh", "mouth_ch", "mouth_sh"],                           lips=0.6, jaw=0.3),
    VisemeDef("TH",    "Th (thin)",         ["Mouth_TH", "TH", "Th", "mouth_th", "Mouth_Tongue"],                                   tongue=0.5, jaw=0.2),
    VisemeDef("F",     "F/V (five)",        ["Mouth_FV", "FV", "Mouth_F", "F", "mouth_f", "Mouth_LipBite", "LipBite"],              jaw=0.0),
    VisemeDef("L",     "L/D/T/N (let)",     ["Mouth_L", "L", "Mouth_D", "Mouth_T", "Mouth_N", "mouth_l", "mouth_d", "mouth_t"],     tongue=0.5, jaw=0.2),
    VisemeDef("MM",    "M/B/P (mom)",       ["Mouth_MM", "MM", "Mouth_M", "Mouth_B", "Mouth_P", "mouth_mm", "mouth_m", "mouth_b"],  jaw=0.0),
    VisemeDef("W",     "W/Q (wet)",         ["Mouth_W", "W", "mouth_w"],                                                            lips=0.8, jaw=0.2),
    VisemeDef("RR",    "R (red)",           ["Mouth_RR", "RR", "Mouth_R", "mouth_rr", "mouth_r"],                                   lips=0.4, jaw=0.2),
    VisemeDef("sil",   "Silence",           ["Mouth_Rest", "Rest", "mouth_rest"],                                                    jaw=0.0),
]


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Phoneme ΓåÆ viseme lookup
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

# Maps phoneme strings (from USTX lyrics) to viseme codes.
# Extended with common vowel/consonant variants and diphthongs.
PHONEME_TO_VISEME: dict[str, str] = {
    # Vowels
    "a": "AA", "ah": "AA", "aa": "AA",
    "e": "EH", "eh": "EH",
    "i": "IH", "ih": "IH",
    "ee": "EE", "ea": "EE", "y": "EE",
    "o": "OH", "oh": "OH", "oa": "OH",
    "u": "OO", "oo": "OO", "ou": "OO", "uu": "OO",
    "aw": "OH", "au": "OH",
    "ai": "AA", "ay": "AA",
    "oi": "OO",
    # Consonants
    "p": "MM", "b": "MM", "m": "MM", "mm": "MM",
    "f": "F", "v": "F",
    "th": "TH", "dh": "TH",
    "t": "L", "d": "L", "n": "L", "l": "L",
    "s": "CH", "z": "CH", "sh": "CH", "ch": "CH", "j": "CH", "zh": "CH",
    "k": "EE", "g": "EE", "ng": "EE",
    "r": "RR",
    "w": "W", "wh": "W", "qu": "W",
    "h": "AA", "hh": "AA",
    # Special
    "rest": "sil", "sil": "sil", "pause": "sil", "-": "sil",
    "_": "sil", " ": "sil", "": "sil",
    # Japanese kana (romaji)
    "ka": "AA", "ki": "IH", "ku": "OO", "ke": "EH", "ko": "OH",
    "sa": "AA", "shi": "CH", "su": "OO", "se": "EH", "so": "OH",
    "ta": "AA", "chi": "CH", "tsu": "OO", "te": "EH", "to": "OH",
    "na": "AA", "ni": "IH", "nu": "OO", "ne": "EH", "no": "OH",
    "ha": "AA", "hi": "IH", "fu": "F",   "he": "EH", "ho": "OH",
    "ma": "AA", "mi": "IH", "mu": "OO", "me": "EH", "mo": "OH",
    "ra": "AA", "ri": "IH", "ru": "OO", "re": "EH", "ro": "OH",
    "wa": "W",  "wo": "OH",
    "ga": "AA", "gi": "IH", "gu": "OO", "ge": "EH", "go": "OH",
    "za": "AA", "ji": "CH", "zu": "OO", "ze": "EH", "zo": "OH",
    "da": "AA", "di": "IH", "du": "OO", "de": "EH", "do": "OH",
    "ba": "AA", "bi": "IH", "bu": "OO", "be": "EH", "bo": "OH",
    "pa": "AA", "pi": "IH", "pu": "OO", "pe": "EH", "po": "OH",
    "n":  "L",  "nn": "L",
}


def phoneme_to_viseme_code(phoneme: str) -> str:
    """Resolve a phoneme string to the closest viseme code."""
    p = phoneme.lower().strip()
    return PHONEME_TO_VISEME.get(p, "rest")


def get_viseme_weights(phoneme: str) -> dict[str, float]:
    """Get viseme weight dict for a phoneme (sparse ΓÇö only active viseme is 1.0)."""
    code = phoneme_to_viseme_code(phoneme)
    weights: dict[str, float] = {v.code: 0.0 for v in VISEMES}
    weights[code] = 1.0
    return weights


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Rig auto-detection ΓÇö find blendshape names on the armature
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

@dataclass
class VisemeBinding:
    """Bound viseme: canonical code ΓåÆ actual blendshape key_block on the rig."""
    viseme_code: str
    viseme_label: str
    shape_key_name: str         # actual name on the mesh data block
    mesh_name: str              # which mesh this key_block belongs to
    key_block_index: int = -1


def detect_rig_blendshapes(armature_obj) -> list[VisemeBinding]:
    """Scan an armature + its children for mesh shape keys matching visemes.

    Returns a list of VisemeBindings for each matched viseme.
    If a viseme has multiple candidates, only the first matched shape key is returned.
    """
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return []

    bindings: list[VisemeBinding] = []
    found_visemes: set[str] = set()

    # Scan all mesh children of the armature for shape keys
    for child in armature_obj.children_recursive:
        if child.type != "MESH":
            continue
        data = child.data
        if not hasattr(data, "shape_keys") or data.shape_keys is None:
            continue
        key_blocks = data.shape_keys.key_blocks
        if not key_blocks:
            continue

        for kb in key_blocks:
            name_lower = kb.name.lower().replace(" ", "_").replace("-", "_")
            # Try to match against each viseme's shape_key patterns
            for vdef in VISEMES:
                if vdef.code in found_visemes:
                    continue
                for pattern in vdef.shape_keys:
                    pattern_lower = pattern.lower().replace(" ", "_").replace("-", "_")
                    if pattern_lower in name_lower or name_lower == pattern_lower:
                        bindings.append(VisemeBinding(
                            viseme_code=vdef.code,
                            viseme_label=vdef.label,
                            shape_key_name=kb.name,
                            mesh_name=child.name,
                        ))
                        found_visemes.add(vdef.code)
                        break
                if vdef.code in found_visemes:
                    break

    return bindings


def get_bound_viseme_map(armature_obj) -> dict[str, str]:
    """Return {viseme_code: shape_key_name} for the rig.

    Missing visemes are excluded from the dict.
    """
    bindings = detect_rig_blendshapes(armature_obj)
    return {b.viseme_code: b.shape_key_name for b in bindings}


def get_rig_mesh_targets(armature_obj) -> dict[str, str]:
    """Return {shape_key_name: mesh_name} for key_blockΓåÆmesh resolution."""
    targets: dict[str, str] = {}
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return targets
    for child in armature_obj.children_recursive:
        if child.type != "MESH":
            continue
        data = child.data
        if not hasattr(data, "shape_keys") or data.shape_keys is None:
            continue
        for kb in data.shape_keys.key_blocks:
            targets[kb.name] = child.name
    return targets


# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ
# Convenience: produce a summary for the UI
# ΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉΓòÉ

def rig_detection_report(armature_obj) -> str:
    """Return a human-readable report of detected viseme bindings."""
    if armature_obj is None or armature_obj.type != "ARMATURE":
        return "No armature selected."

    bindings = detect_rig_blendshapes(armature_obj)
    if not bindings:
        # List all available shape keys as a hint
        lines = ["No viseme blendshapes detected. Available shape keys:"]
        for child in armature_obj.children_recursive:
            if child.type != "MESH":
                continue
            data = child.data
            if not hasattr(data, "shape_keys") or data.shape_keys is None:
                continue
            if data.shape_keys.key_blocks:
                for kb in data.shape_keys.key_blocks:
                    lines.append(f"  [{child.name}] {kb.name}")
        return "\n".join(lines)

    lines = [f"Detected {len(bindings)} visemes on '{armature_obj.name}':"]
    for b in bindings:
        lines.append(f"  {b.viseme_code} ({b.viseme_label}) ΓåÆ {b.shape_key_name} [{b.mesh_name}]")
    missing = [v.code for v in VISEMES if v.code not in {b.viseme_code for b in bindings}]
    if missing:
        lines.append(f"Missing visemes ({len(missing)}): {', '.join(missing)}")
    return "\n".join(lines)
