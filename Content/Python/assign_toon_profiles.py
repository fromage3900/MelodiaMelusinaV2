#!/usr/bin/env python3
"""
assign_toon_profiles.py — Assign Toon Profiles to master materials.

Toon Profiles must be created manually in-editor first (see TOON_PROFILES_GUIDE.md).
Once they exist, this script assigns them to the right master materials.

Usage (editor open, Monolith running):
    python assign_toon_profiles.py --list             # show current assignments
    python assign_toon_profiles.py --apply            # apply schema assignments
    python assign_toon_profiles.py --apply --dry-run  # show what would change

Headless:
    python run_headless.py --script "Content/Python/assign_toon_profiles.py" -- --apply
"""
from __future__ import annotations
import json, sys, os
from pathlib import Path

MONOLITH = "http://127.0.0.1:9316/mcp"
HEADLESS = "--headless" in sys.argv

# ── Canonical Toon Profile assignments ────────────────────────────────
# Profile names as they appear in the Content Browser after manual creation.
# When a profile asset is created at /Game/EnvSandbox/Materials/ToonProfiles/TP_Character,
# its in-engine name is "TP_Character" (the asset's FName).
# TP_Melusina uses warm-violet ramp (#352D40) for found-family warmth + melancholic depth.
PROFILE_ASSIGNMENTS = {
    "M_Master_Toon_Universal": {
        "path": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal",
        "bsdf_expr": "MaterialExpressionSubstrateToonBSDF_4",
        "profile": "TP_Melusina",  # Warm-violet surreal ramp for Melusina
    },
    "M_Master_Nikki": {
        "path": "/Game/EnvSandbox/Materials/_Scratch/M_Master_Nikki",
        "bsdf_expr": "MaterialExpressionSubstrateToonBSDF_1",
        "profile": "TP_Character",  # Nikki gets character shading
    },
    "M_Master_Toon_Landscape_HeightBlend": {
        "path": "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend",
        "bsdf_expr": "MaterialExpressionSubstrateToonBSDF_0",
        "profile": "TP_Foliage",  # Landscape gets foliage shading
    },
}

# ── Profile Discovery ─────────────────────────────────────────────────
# Checker validates that each profile asset exists; adds TP_Melusina support.
def find_profile_asset(profile_name):
    """Find a toon profile asset by name, checking multiple possible paths."""
    candidates = [
        "/Game/EnvSandbox/Materials/ToonProfiles/{profile}.{profile}",
        "/Game/EnvSandbox/Materials/Masters/ToonProfiles/{profile}.{profile}",
        "/Game/Melodia/_PROJECT/04_Materials/ToonProfiles/{profile}.{profile}",
        # TP_Melusina-specific: warm-violet profile created in-editor
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina",
    ]
    import unreal
    eal = unreal.EditorAssetLibrary
    for c in candidates:
        if eal.does_asset_exist(c.format(profile=profile_name)):
            return c.format(profile=profile_name)
    return None

# ── Backend ──────────────────────────────────────────────────────────
def call_monolith(tool, args):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}}).encode()
    import urllib.request
    req = urllib.request.Request(MONOLITH, data=body, headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())

def run_python(cmd):
    if HEADLESS:
        import io, contextlib
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exec(cmd, {"unreal": __import__("unreal")})
        return stdout.getvalue()
    r = call_monolith("editor_query", {"action":"run_python","command":cmd})
    out = []
    for c in r.get("result",{}).get("content",[]):
        if c.get("type")=="text":
            data = json.loads(c["text"])
            for o in data.get("output",[]):
                out.append(o.get("output",""))
    return "\n".join(out)

# ── Actions ──────────────────────────────────────────────────────────
def list_current():
    """Show current Toon Profile on each master."""
    print("=== Current Toon Profile Assignments ===")
    for key, info in PROFILE_ASSIGNMENTS.items():
        out = run_python(f"""
import unreal
MEL = unreal.MaterialEditingLibrary
mat = unreal.load_asset("{info['path']}")
if mat:
    for expr in MEL.get_material_expressions(mat) or []:
        if type(expr).__name__ == "MaterialExpressionSubstrateToonBSDF":
            try:
                # Try to read toon_profile property
                tp = expr.get_editor_property("toon_profile")
                tp_name = str(tp.get_name()) if tp else "None (default)"
                print("PROFILE|{key}|" + tp_name)
            except:
                # Property may not exist in this version
                print("PROFILE|{key}|UNAVAILABLE")
else:
    print("PROFILE|{key}|MISSING")
""")
        for line in out.splitlines():
            if line.startswith("PROFILE|"):
                parts = line.split("|")
                print(f"  {parts[1]:30s} -> {parts[2]}")

def apply_assignments(dry_run: bool = False):
    """Assign Toon Profiles from schema."""
    print(f"=== {'[DRY RUN] ' if dry_run else ''}Applying Toon Profile Assignments ===")
    for key, info in PROFILE_ASSIGNMENTS.items():
        profile = info["profile"]
        if profile == "TP_Default":
            print(f"  {key:30s} -> {profile} (default, skipping)")
            continue

        # Check if the profile asset exists first
        out = run_python(f"""
import unreal
eal = unreal.EditorAssetLibrary
# The profile might be at various locations - check common places
    candidates = [
        "/Game/EnvSandbox/Materials/ToonProfiles/{profile}.{profile}",
        "/Game/EnvSandbox/Materials/Masters/ToonProfiles/{profile}.{profile}",
        "/Game/Melodia/_PROJECT/04_Materials/ToonProfiles/{profile}.{profile}",
        # TP_Melusina-specific: also check the new warm-violet profile
        "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina",
    ]
found = None
for c in candidates:
    if eal.does_asset_exist(c):
        found = c
        break
print("FOUND|{key}|" + str(found))
""")
        profile_path = None
        for line in out.splitlines():
            if line.startswith("FOUND|"):
                p = line.split("|")[2]
                if p != "None":
                    profile_path = p

        if not profile_path:
            print(f"  {key:30s} -> {profile} NOT FOUND - create asset first")
            print(f"             Expected at: /Game/EnvSandbox/Materials/ToonProfiles/{profile}")
            continue

        if dry_run:
            print(f"  {key:30s} -> {profile} (would assign)")
            continue

        # Assign via set_expression_property
        r = call_monolith("material_query", {"action": "set_expression_property",
            "asset_path": info["path"],
            "expression_name": info["bsdf_expr"],
            "property_name": "ToonProfile",
            "value": profile_path
        })
        result_text = ""
        for c in r.get("result",{}).get("content",[]):
            if c.get("type")=="text": result_text = c["text"]
        if "error" in result_text.lower():
            print(f"  {key:30s} -> {profile} FAILED: {result_text[:100]}")
        else:
            # Save material
            run_python(f"import unreal; unreal.EditorAssetLibrary.save_asset('{info['path']}')")
            print(f"  {key:30s} -> {profile} ASSIGNED AND SAVED")

def main():
    if "--list" in sys.argv:
        list_current()
    elif "--apply" in sys.argv:
        dry = "--dry-run" in sys.argv
        apply_assignments(dry_run=dry)
    else:
        print("Toon Profile Assignment Tool")
        print(f"  --list         Show current assignments")
        print(f"  --apply        Apply schema assignments")
        print(f"  --apply --dry-run  Preview without changes")
        print(f"  --headless     Run inside UE-Cmd")

if __name__ == "__main__":
    main()
