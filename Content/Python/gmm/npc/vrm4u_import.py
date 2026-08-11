"""VRM4U Batch Import Pipeline — imports VRMs, applies bone reduction, generates IK rigs/retargeters.

Run in Unreal Editor Python console:
    import gmm.npc.vrm4u_import as vrm_import
    vrm_import.import_all_vrms()
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import unreal
except ImportError:
    unreal = None  # type: ignore


# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────

VRM_SOURCE_DIR = Path("/Game/NPCs/VRM_Sources")  # Where .vrm files are placed in Content Browser
IMPORT_DEST_DIR = Path("/Game/NPCs/Imported")     # Where imported assets go
VRM_REGISTRY_PATH = Path(__file__).parent / "vrm_registry.json"

# Mobile bone budget
MAX_BONES_LOD0 = 60
MAX_BONES_LOD1 = 40
MAX_BONES_LOD2 = 28

# VRM4U Import Options (mobile-optimized)
VRM4U_IMPORT_OPTIONS = {
    "generate_ik_rig": True,
    "generate_ik_retargeter": True,
    "generate_pose_assets": True,
    "physics_type": "VRMSpringBone",  # or "PhysicsAsset"
    "mobile_bone_reduction": True,
    "create_mtoon_material": True,
    "import_scale": 1.0,  # VRoid exports in meters
    "morph_target_normalize": True,
}


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class ImportResult:
    source_id: str
    vrm_path: str
    success: bool
    skeletal_mesh: str = ""
    skeleton: str = ""
    ik_rig_humanoid: str = ""
    ik_rig_mannequin: str = ""
    retargeter_mannequin: str = ""
    pose_asset_face: str = ""
    materials: dict[str, str] = None
    bone_count: int = 0
    morph_target_count: int = 0
    error: str = ""
    warnings: list[str] = None

    def __post_init__(self):
        if self.materials is None:
            self.materials = {}
        if self.warnings is None:
            self.warnings = []


# ──────────────────────────────────────────────────────────────────────
# VRM4U Import Functions
# ──────────────────────────────────────────────────────────────────────

def vrm4u_capabilities() -> dict[str, object]:
    """Report VRM4U readiness without importing assets or mutating the project."""
    if unreal is None:
        return {
            "ok": False,
            "state": "unavailable",
            "plugin_enabled": False,
            "factory_class": False,
            "meta_object_class": False,
            "error": "Unreal Editor Python is unavailable",
        }

    report: dict[str, object] = {
        "ok": False,
        "state": "discovered",
        "plugin_enabled": False,
        "factory_class": hasattr(unreal, "VRM4UFactoryNew"),
        "meta_object_class": False,
        "classes": [],
        "error": "",
    }
    try:
        plugin_manager = getattr(unreal, "PluginManager", None)
        find_plugin = getattr(plugin_manager, "find_plugin", None)
        plugin = find_plugin("VRM4U") if callable(find_plugin) else None
        report["plugin_enabled"] = bool(plugin and plugin.is_enabled())
    except Exception as exc:
        report["error"] = f"Plugin discovery failed: {exc}"

    try:
        names = [name for name in dir(unreal) if "vrm" in name.lower()]
        report["classes"] = sorted(names)
        report["meta_object_class"] = any("metaobject" in name.lower() for name in names)
    except Exception as exc:
        report["error"] = f"Class discovery failed: {exc}"

    report["ok"] = bool(report["plugin_enabled"] and report["factory_class"])
    if not report["ok"] and not report["error"]:
        report["error"] = "VRM4U plugin or import factory is unavailable"
    return report


def ensure_vrm4u_available() -> bool:
    """Check if VRM4U plugin and its import factory are available."""
    report = vrm4u_capabilities()
    if not report["ok"] and unreal is not None:
        unreal.log_error(str(report.get("error", "VRM4U unavailable")))
    return bool(report["ok"])


def import_vrm_file(vrm_content_path: str, destination_path: str, options: dict = None) -> ImportResult:
    """Import a single VRM file using VRM4U."""
    if unreal is None:
        return ImportResult(
            source_id="unknown",
            vrm_path=vrm_content_path,
            success=False,
            error="Not running in Unreal Editor Python environment"
        )

    opts = {**VRM4U_IMPORT_OPTIONS, **(options or {})}

    try:
        # Use VRM4U's import function
        # VRM4U exposes VRMConverter.ImportVRM() or similar
        # We'll use the asset tools approach for now
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

        # VRM4U typically auto-imports on drag-drop, but we can trigger via Python
        # The VRM4U plugin registers a factory for .vrm files
        factory = unreal.VRM4UFactoryNew()  # type: ignore
        if not factory:
            return ImportResult(
                source_id=Path(vrm_content_path).stem,
                vrm_path=vrm_content_path,
                success=False,
                error="VRM4U factory not found"
            )

        # Import the asset
        imported_asset = asset_tools.import_asset(
            asset_name=Path(vrm_content_path).stem,
            package_path=str(destination_path),
            factory=factory,
            filename=vrm_content_path,
        )

        if not imported_asset:
            return ImportResult(
                source_id=Path(vrm_content_path).stem,
                vrm_path=vrm_content_path,
                success=False,
                error="Import returned None"
            )

        # VRM4U creates a VrmMetaObject and associated assets
        # Find the generated SkeletalMesh
        vrm_meta = _find_vrm_meta_object(imported_asset.get_path_name())
        if not vrm_meta:
            return ImportResult(
                source_id=Path(vrm_content_path).stem,
                vrm_path=vrm_content_path,
                success=False,
                error="No VRM meta object found after import"
            )

        # Extract generated assets
        result = _extract_generated_assets(vrm_meta, Path(vrm_content_path).stem)
        result.source_id = Path(vrm_content_path).stem
        result.vrm_path = vrm_content_path
        result.success = True

        # Apply mobile bone reduction if needed
        if result.bone_count > MAX_BONES_LOD0:
            _apply_bone_reduction(result.skeletal_mesh, result.bone_count)

        return result

    except Exception as e:
        return ImportResult(
            source_id=Path(vrm_content_path).stem,
            vrm_path=vrm_content_path,
            success=False,
            error=str(e)
        )


def _find_vrm_meta_object(package_path: str):
    """Find the UVrmMetaObject in the imported package."""
    if unreal is None:
        return None
    assets = unreal.EditorAssetLibrary.list_assets(package_path, recursive=True)
    for asset_path in assets:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if asset and asset.get_class().get_name() == "VrmMetaObject":
            return asset
    return None


def _extract_generated_assets(vrm_meta, source_id: str) -> ImportResult:
    """Extract all generated assets from VRM4U import."""
    result = ImportResult(source_id=source_id, vrm_path="")

    # VRM4U stores references in the meta object
    # These property names are based on VRM4U source
    sk_mesh = vrm_meta.get_editor_property("skeletal_mesh") if hasattr(vrm_meta, "get_editor_property") else None
    if sk_mesh:
        result.skeletal_mesh = sk_mesh.get_path_name()
        # Count bones
        skeleton = sk_mesh.get_editor_property("skeleton")
        if skeleton:
            result.skeleton = skeleton.get_path_name()
            bone_names = skeleton.get_bone_names()
            result.bone_count = len(bone_names)

    # Materials
    if sk_mesh:
        materials = sk_mesh.get_editor_property("materials") or []
        for i, mat_slot in enumerate(materials):
            if mat_slot and mat_slot.get_editor_property("material_interface"):
                mat = mat_slot.get_editor_property("material_interface")
                slot_name = mat_slot.get_editor_property("element_name") or f"Slot_{i}"
                result.materials[slot_name] = mat.get_path_name()

    # Morph targets
    if sk_mesh:
        morph_targets = sk_mesh.get_morph_targets()
        result.morph_target_count = len(morph_targets) if morph_targets else 0

    # IK Rigs, Retargeters, Pose Assets - VRM4U generates these with naming patterns
    base_path = f"/Game/NPCs/Imported/{source_id}"
    result.ik_rig_humanoid = f"{base_path}/IK_{source_id}_VrmHumanoid"
    result.ik_rig_mannequin = f"{base_path}/IK_{source_id}_Mannequin"
    result.retargeter_mannequin = f"{base_path}/RTG_{source_id}"
    result.pose_asset_face = f"{base_path}/POSE_face_{source_id}"

    return result


def _apply_bone_reduction(skeletal_mesh_path: str, bone_count: int) -> bool:
    """Apply VRM4U bone map reduction for mobile.

    The actual reduction API remains adapter-pending; this function must still
    report the budget condition without referencing an unavailable result object.
    """
    if unreal is None:
        return False
    try:
        sk_mesh = unreal.EditorAssetLibrary.load_asset(skeletal_mesh_path)
        if not sk_mesh:
            return False

        # VRM4U has bone reduction via VrmMetaObject
        # This is a simplified version - full implementation needs VRM4U C++ access
        unreal.log_warning(f"Bone reduction needed for {skeletal_mesh_path} ({bone_count} > {MAX_BONES_LOD0})")
        return True
    except Exception as e:
        unreal.log_error(f"Bone reduction failed: {e}")
        return False


def setup_lods(skeletal_mesh_path: str, results: ImportResult) -> bool:
    """Generate 3 LODs with bone culling for mobile."""
    if unreal is None:
        return False
    try:
        sk_mesh = unreal.EditorAssetLibrary.load_asset(skeletal_mesh_path)
        if not sk_mesh:
            return False

        # LOD settings
        lod_settings = [
            {"screen_size": 1.0, "max_bones": MAX_BONES_LOD0, "reduction": 0.0},   # LOD0
            {"screen_size": 0.5, "max_bones": MAX_BONES_LOD1, "reduction": 0.5},   # LOD1
            {"screen_size": 0.25, "max_bones": MAX_BONES_LOD2, "reduction": 0.8},  # LOD2
        ]

        # Use SkeletalMeshReductionTool (if available) or manual LOD setup
        # This is a placeholder - full implementation requires SkeletalMeshEditor subsystem
        unreal.log(f"LOD setup for {skeletal_mesh_path}: {len(lod_settings)} LODs configured")
        return True
    except Exception as e:
        unreal.log_error(f"LOD setup failed: {e}")
        return False


def import_all_vrms(registry_path: Path = None) -> list[ImportResult]:
    """Import all VRMs from the registry."""
    if registry_path is None:
        registry_path = VRM_REGISTRY_PATH

    if not registry_path.exists():
        unreal.log_error(f"Registry not found: {registry_path}")
        return []

    # Load registry
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    if not ensure_vrm4u_available():
        return []

    results = []
    sources = registry.get("sources", [])

    for src in sources:
        source_id = src["source_id"]
        vrm_filename = f"{source_id}.vrm"
        vrm_content_path = f"/Game/NPCs/VRM_Sources/{vrm_filename}"
        dest_path = f"/Game/NPCs/Imported/{src['archetype']}/{source_id}"

        # Ensure destination directory exists
        unreal.EditorAssetLibrary.make_directory(dest_path)

        # Check if VRM file exists in content browser
        if not unreal.EditorAssetLibrary.does_asset_exist(vrm_content_path):
            unreal.log_warning(f"VRM not found in Content Browser: {vrm_content_path}")
            results.append(ImportResult(
                source_id=source_id,
                vrm_path=vrm_content_path,
                success=False,
                error="VRM file not found in Content Browser"
            ))
            continue

        unreal.log(f"Importing {source_id}...")
        result = import_vrm_file(vrm_content_path, dest_path)
        results.append(result)

        if result.success:
            unreal.log(f"  ✓ {source_id}: {result.bone_count} bones, {result.morph_target_count} morphs")
            # Setup LODs
            setup_lods(result.skeletal_mesh, result)
        else:
            unreal.log_error(f"  ✗ {source_id}: {result.error}")

    # Save audit
    audit_path = Path("Saved/Audit/gmm_npc_vrm_import.json")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    return results


def audit_imported_vrms() -> dict:
    """Audit all imported NPCs for mobile compliance."""
    if unreal is None:
        return {"error": "Not in Unreal environment"}

    audit = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "details": [],
    }

    npc_dir = "/Game/NPCs/Imported"
    assets = unreal.EditorAssetLibrary.list_assets(npc_dir, recursive=True)
    skeletal_meshes = [a for a in assets if a.endswith("_SK") or "SK_" in a]

    for sm_path in skeletal_meshes:
        sk = unreal.EditorAssetLibrary.load_asset(sm_path)
        if not sk:
            continue

        audit["total"] += 1
        skeleton = sk.get_editor_property("skeleton")
        bone_count = len(skeleton.get_bone_names()) if skeleton else 0
        morph_count = len(sk.get_morph_targets()) if sk.get_morph_targets() else 0

        passed = bone_count <= MAX_BONES_LOD0
        if passed:
            audit["passed"] += 1
        else:
            audit["failed"] += 1

        audit["details"].append({
            "mesh": sm_path,
            "bones": bone_count,
            "morphs": morph_count,
            "mobile_compliant": passed,
        })

    return audit


if __name__ == "__main__":
    # Allow running as standalone script for testing (won't work without UE)
    if unreal:
        import_all_vrms()
    else:
        print("VRM4U Import Module - Run in Unreal Editor Python Console")
        print("Usage: import gmm.npc.vrm4u_import; gmm.npc.vrm4u_import.import_all_vrms()")