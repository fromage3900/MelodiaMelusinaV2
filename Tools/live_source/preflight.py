"""Per-source preflight checks. Each returns {check: pass|fail|unverified}.

Contracts enforced here (do not loosen without changing the authority doc):
- Rokoko FBX  : Docs/ROKOKO_MELUSINA_MOCAP.md
                (verb-named FBX in Imports/Mocap/Rokoko/Inbox; source/quarantine
                only — never production Melusina paths)
- Cascadeur FBX: Docs/CASCADEUR_MELUSINA_PIPELINE_2026-08-07.md §3
                (CAS_Melusina_<Action>_<Variant>.fbx; an optional A_ intake prefix
                is accepted; offline scan gate §4 is
                delegated to Tools/scan_cascadeur_fbx.py when Blender exists)
- OBSBOT MP4  : Docs/Handoffs/MELUSINA_MEET2_OBSBOT_STUDIO_2026-09-08.md
                MOCAP preset: 1920x1080 @ 60fps, fixed cam. Deviations are
                warnings, not hard fails — acting-reference takes are legal.
"""

from __future__ import annotations

import os
import re
import shutil
import struct
import subprocess

ROKOKO_INBOX = os.path.join(os.path.dirname(__file__), "..", "..",
                            "Imports", "Mocap", "Rokoko", "Inbox")
CAS_INBOX = os.path.join(os.path.dirname(__file__), "..", "..",
                         "Imports", "Animations", "Cascadeur", "Inbox")

CAS_NAME = re.compile(
    r"^(?:A_)?CAS_Melusina_[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*\.fbx$")
VERB_NAME = re.compile(
    r"^(?:A_Rokoko_)?[A-Z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*\.fbx$")

# Melusina production surfaces a capture file must NEVER sit in.
PROTECTED_PATH_FRAGMENTS = (
    "Melodia/Characters/Melusina",
    "MelodiaIntegration/Blueprints",
)


def classify(path: str) -> str:
    p = path.replace("\\", "/")
    low = p.lower()
    if low.endswith(".fbx") and "/mocap/rokoko/" in low:
        return "ROKOKO"
    if low.endswith(".fbx") and "cascadeur" in low:
        return "CASCADEUR"
    if low.endswith(".mp4"):
        return "OBSBOT"
    if low.endswith(".fbx"):
        return "UNKNOWN_FBX"
    return "UNKNOWN"


def _protected_check(path: str) -> bool:
    return not any(frag in path.replace("\\", "/") for frag in PROTECTED_PATH_FRAGMENTS)


def check_rokoko(path: str) -> dict:
    checks = {}
    checks["not_protected_surface"] = _protected_check(path)
    name = os.path.basename(path)
    checks["verb_naming"] = bool(VERB_NAME.match(name))
    in_inbox = os.path.dirname(os.path.abspath(path)) == os.path.abspath(ROKOKO_INBOX)
    checks["in_rokoko_inbox"] = in_inbox
    checks["file_nonempty"] = os.path.getsize(path) > 0 if os.path.exists(path) else False
    # Skeleton/armature verification needs Blender or the UE import step —
    # labeled, not assumed.
    checks["skeleton_verified"] = "UNVERIFIED"
    return checks


def check_cascadeur(path: str) -> dict:
    checks = {}
    checks["not_protected_surface"] = _protected_check(path)
    checks["cas_naming"] = bool(CAS_NAME.match(os.path.basename(path)))
    checks["in_cascadeur_inbox"] = (
        os.path.dirname(os.path.abspath(path)) == os.path.abspath(CAS_INBOX))
    checks["file_nonempty"] = os.path.getsize(path) > 0 if os.path.exists(path) else False
    # §4 offline scan gate — delegate, never reimplement.
    blender = shutil.which("blender")
    if blender and os.path.exists(os.path.join(
            os.path.dirname(__file__), "..", "scan_cascadeur_fbx.py")):
        r = subprocess.run(
            [blender, "--background", "--python",
             os.path.join(os.path.dirname(__file__), "..", "scan_cascadeur_fbx.py"),
             "--", path, os.devnull],
            capture_output=True, timeout=300)
        checks["offline_scan"] = r.returncode == 0
    else:
        checks["offline_scan"] = "UNVERIFIED"
    return checks


def check_obsbot(path: str) -> dict:
    from mp4probe import probe_mp4, Mp4ProbeError
    checks = {"file_nonempty": os.path.getsize(path) > 0 if os.path.exists(path) else False}
    try:
        info = probe_mp4(path)
    except (Mp4ProbeError, OSError, struct.error) as e:  # noqa: F821
        checks["mp4_parseable"] = False
        checks["parse_error"] = str(e)
        return checks
    checks["mp4_parseable"] = True
    checks["seconds"] = info["seconds"]
    checks["resolution"] = f'{info["width"]}x{info["height"]}'
    checks["fps"] = info["fps"]
    # MOCAP preset per MEET2 studio doc — deviations warn, not fail.
    checks["preset_1080p60"] = (info["width"] == 1920 and info["height"] == 1080
                                and info["fps"] is not None and abs(info["fps"] - 60.0) < 1.0)
    return checks


def preflight(path: str) -> dict:
    kind = classify(path)
    if kind == "ROKOKO":
        return {"source": kind, "checks": check_rokoko(path)}
    if kind == "CASCADEUR":
        return {"source": kind, "checks": check_cascadeur(path)}
    if kind == "OBSBOT":
        return {"source": kind, "checks": check_obsbot(path)}
    return {"source": kind, "checks": {},
            "error": f"unrecognized source for {path!r} "
                     f"(expect Rokoko-inbox FBX, Cascadeur-inbox FBX, or OBSBOT MP4)"}
