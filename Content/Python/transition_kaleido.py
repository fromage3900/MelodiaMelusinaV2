import unreal, os, re

print("=== KALEIDO NAVE TRANSITION ===\n")

# 1. Search disk files for Dreamstate references
print("--- Searching disk for Dreamstate references ---")
search_paths = [
    "C:/EnvironmentPortfolio/BS_GodFile/Content/MelodiaIntegration/Narrative",
    "C:/EnvironmentPortfolio/BS_GodFile/Config",
    "C:/EnvironmentPortfolio/BS_GodFile/Source/BS_GodFile/MelodiaIntegration",
]
dreamstate_refs = []
for sp in search_paths:
    if os.path.exists(sp):
        for root, dirs, files in os.walk(sp):
            for f in files:
                if any(f.endswith(ext) for ext in ['.qsc', '.ini', '.cpp', '.h', '.py']):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                            content = fh.read()
                            if 'dreamstate' in content.lower() or 'Dreamstate' in content or 'L_Melodia_Dreamstate' in content:
                                # Find lines
                                lines = content.split('\n')
                                for i, line in enumerate(lines):
                                    if 'dreamstate' in line.lower() or 'Dreamstate' in line:
                                        dreamstate_refs.append(f"{fp}:{i+1}: {line.strip()[:120]}")
                    except:
                        pass

print(f"  Found {len(dreamstate_refs)} Dreamstate references:")
for ref in dreamstate_refs[:20]:
    print(f"    {ref}")

# 2. Check DefaultGame.ini MapsToCook
print("\n--- DefaultGame.ini MapsToCook ---")
ini_path = "C:/EnvironmentPortfolio/BS_GodFile/Config/DefaultGame.ini"
if os.path.exists(ini_path):
    with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        import re
        # Find MapsToCook section
        maps_match = re.search(r'\[.*MapsToCook.*\](.*?)(?=\[/|$)', content, re.DOTALL)
        if maps_match:
            print("  Section found:")
            print(maps_match.group(0)[:500])
        else:
            print("  No MapsToCook section found in DefaultGame.ini")
else:
    print("  DefaultGame.ini not found")

# 3. KaleidoNave asset check
print("\n--- KaleidoNave Status ---")
eal = unreal.EditorAssetLibrary
kaleido_path = "/Game/EnvSandbox/Environments/L_KaleidoNave"
print(f"  {kaleido_path}: {'EXISTS' if eal.does_asset_exist(kaleido_path) else 'MISSING'}")

# Current maps in route
dreamstate_path = "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate"
print(f"  {dreamstate_path}: {'EXISTS' if eal.does_asset_exist(dreamstate_path) else 'MISSING'}")

print("\nDONE")