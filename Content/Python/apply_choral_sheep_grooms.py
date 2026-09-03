"""
Wire Choral Sheep grooms to UE Groom components (optional LOD).

Reads Saved/Audit/choral_sheep/grooms/groom_ingest_manifest.json
Checks for real Alembic vs placeholder, and reports UE import status.

Run inside UE Editor Python:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/apply_choral_sheep_grooms.py", encoding="utf-8").read())

Groom is OPTIONAL per ChoralSheepDefinition.json groom_policy:
"Missing Groom must not prevent the base skeletal mesh from loading or companion from following."
So this script never errors if grooms are still placeholders — it just reports.
"""
import json
from pathlib import Path
import unreal

MANIFEST = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/choral_sheep/grooms/groom_ingest_manifest.json")
SPEC = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Tools/Houdini/choral_groom_variants_spec.json")
UE_GROOM_DIR = "/Game/Melodia/Companions/ChoralSheep/Grooms/"

def main():
    if not MANIFEST.is_file():
        print(f"[groom] no manifest at {MANIFEST} — run python Tools/Houdini/ingest_grooms.py --verify")
        return
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    spec = json.loads(SPEC.read_text(encoding="utf-8")) if SPEC.is_file() else {}
    print(f"[groom] manifest {MANIFEST} — {len(data.get('tracks',[]))} tracks")
    for t in data.get("tracks", []):
        label = t.get("label")
        abc = Path(t.get("abc",""))
        real = t.get("real")
        ue_groom = UE_GROOM_DIR + f"Groom_ChoralSheep_PC_{label}"
        exists = unreal.EditorAssetLibrary.does_asset_exist(ue_groom)
        status = "REAL" if real else "PLACEHOLDER"
        print(f"  PC_{label:2s} {status:12s} abc {abc.name} -> UE {ue_groom} {'EXISTS' if exists else 'not imported'}")

        # if real ABC exists on disk, try to auto-import via Interchange if not already in UE
        if real and abc.is_file() and not exists:
            try:
                # Attempt Alembic Groom import
                task = unreal.AssetImportTask()
                task.filename = str(abc)
                task.destination_path = UE_GROOM_DIR.rstrip("/")
                task.destination_name = f"Groom_ChoralSheep_PC_{label}"
                task.automated = True
                task.save = True
                task.replace_existing = False
                # Groom import uses HairStrands factory if available
                unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
                print(f"    -> imported {abc.name} -> {ue_groom}")
            except Exception as e:
                print(f"    -> auto-import failed (import Grooms manually): {e}")

    # Report LOD binding expectation
    lod_bands = spec.get("base", {}).get("lod_bands_cm", [])
    print(f"[groom] LOD bands (from spec): {lod_bands}")
    print(f"[groom] GroomComps bind on AMelodiaChoralSheepActor; per ChoralSheepDefinition fur.groom_asset_tag")
    print(f"[groom] To test: Place BP_ChoralSheep in /Game/_PROJECT/Levels/RenderTests/L_ChoralSheep_Prototype, assign")
    print(f"        Groom_ChoralSheep_PC_C in GroomComponent; missing groom is OK (mesh still follows).")
    print(f"[groom] For real strands: hython Tools/Houdini/build_choral_groom_hip.py && hython Tools/Houdini/cook_groom_variants.py")

try:
    main()
except Exception as e:
    import traceback; traceback.print_exc(); print(f"[groom] error: {e}")
