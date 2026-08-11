#!/usr/bin/env python3
"""
create_toon_profile_melusina.py — Create TP_Melusina Toon Profile with warm-violet ramp (#352D40).

Usage (editor open, Monolith running):
    python create_toon_profile_melusina.py

Headless:
    python run_headless.py --script "Content/Python/create_toon_profile_melusina.py"
"""
from __future__ import annotations
import json, sys
from pathlib import Path

MONOLITH = "http://127.0.0.1:9316/mcp"

def call_monolith(tool, args):
    body = json.dumps({"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":tool,"arguments":args}}).encode()
    import urllib.request
    req = urllib.request.Request(MONOLITH, data=body, headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())

def run_python(cmd):
    r = call_monolith("editor_query", {"action":"run_python","command":cmd})
    out = []
    for c in r.get("result",{}).get("content",[]):
        if c.get("type")=="text":
            data = json.loads(c["text"])
            for o in data.get("output",[]):
                out.append(o.get("output",""))
    return "\n".join(out)

def create_toon_profile():
    """Create TP_Melusina Toon Profile with warm-violet ramp (#352D40)."""
    profile_name = "TP_Melusina"
    profile_path = f"/Game/EnvSandbox/Materials/ToonProfiles/{profile_name}.{profile_name}"
    
    print(f"Creating Toon Profile: {profile_path}")
    
    # Check if already exists
    out = run_python(f"""
import unreal
eal = unreal.EditorAssetLibrary
exists = eal.does_asset_exist("{profile_path}")
print("EXISTS|" + str(exists))
""")
    
    if "EXISTS|True" in out:
        print(f"  Profile already exists at {profile_path}")
        return profile_path
    
    # Create the Toon Profile via Python
    cmd = f"""
import unreal

# Create the Toon Profile asset
factory = unreal.SubstrateToonProfileFactory()
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
profile = asset_tools.create_asset(
    asset_name="{profile_name}",
    package_path="/Game/EnvSandbox/Materials/ToonProfiles",
    asset_class=unreal.SubstrateToonProfile,
    factory=factory
)

if profile:
    # Configure the warm-violet ramp (#352D40)
    # Diffuse Ramp: 3-stop anime shadow
    # Key 0 (shadow): #352D40 (warm violet - Hoyo-style shadow replacement)
    # Key 1 (mid): base color
    # Key 2 (lit): base color + warm bias
    
    # Diffuse Ramp - 3 keys at NdotL 0.0, 0.3, 1.0
    # Using set_editor_property to set ramp keys
    profile.set_editor_property("DiffuseRampKeys", [
        unreal.SubstrateToonRampKey(n_dot_l=0.0, color=unreal.LinearColor(0.2078, 0.1765, 0.2510, 1.0)),  # #352D40
        unreal.SubstrateToonRampKey(n_dot_l=0.3, color=unreal.LinearColor(1.0, 1.0, 1.0, 1.0)),  # mid - base color
        unreal.SubstrateToonRampKey(n_dot_l=1.0, color=unreal.LinearColor(1.1, 1.05, 1.0, 1.0)),  # lit - warm bias
    ])
    
    # Specular Ramp: 1 narrow key at NdotL 0.9
    profile.set_editor_property("SpecularRampKeys", [
        unreal.SubstrateToonRampKey(n_dot_l=0.9, color=unreal.LinearColor(1.0, 1.0, 1.0, 1.0)),
    ])
    
    # Indirect Diffuse Intensity: 0.3
    profile.set_editor_property("IndirectDiffuseIntensity", 0.3)
    
    # Indirect Specular Intensity: 0.3
    profile.set_editor_property("IndirectSpecularIntensity", 0.3)
    
    # Shadow Hatching Pattern (for hero close-ups)
    # Note: T_HatchPattern needs to be created if not present
    # profile.set_editor_property("ShadowHatchingPattern", hatch_texture)
    # profile.set_editor_property("ShadowingExtinction", 0.3)
    
    print("CREATED|" + profile.get_path_name())
else:
    print("FAILED|Could not create profile")
"""
    out = run_python(cmd)
    for line in out.splitlines():
        if line.startswith("CREATED|"):
            path = line.split("|")[1]
            print(f"  Created: {path}")
            return path
        elif line.startswith("FAILED|"):
            print(f"  Failed to create profile")
            return None
    
    print(f"  Output: {out}")
    return None

def main():
    path = create_toon_profile()
    if path:
        print(f"\n✅ TP_Melusina created at {path}")
        print("   Next: Run assign_toon_profiles.py --apply to assign to M_Master_Nikki")
    else:
        print("\n❌ Failed to create TP_Melusina")
        print("   Fallback: Create manually in editor per TOON_PROFILES_GUIDE.md")

if __name__ == "__main__":
    create_toon_profile()