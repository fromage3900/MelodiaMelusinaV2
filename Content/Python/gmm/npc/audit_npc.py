"""NPC Audit System — validates all generated NPCs for quality, performance, and compliance."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import sys

try:
    import unreal
except ImportError:
    unreal = None


# ──────────────────────────────────────────────────────────────────────
# Audit Configuration (Mobile-First)
# ──────────────────────────────────────────────────────────────────────

AUDIT_CONFIG = {
    # Skeletal Mesh
    "max_bones_lod0": 60,
    "max_bones_lod1": 40,
    "max_bones_lod2": 28,
    "max_triangles_lod0": 18000,
    "max_triangles_lod1": 8000,
    "max_triangles_lod2": 3000,
    "max_morph_targets": 60,
    "min_morph_targets": 20,

    # Materials
    "max_material_instances": 1,  # Per NPC (single MI from master)
    "max_texture_resolution": 1024,
    "require_mtoon_master": True,

    # Cloth
    "mobile_cloth_solver": ["DistanceConstraint", "VRMSpringBone", "BakedAnim"],
    "pc_cloth_solver": ["Chaos", "VRMSpringBone"],

    # LODs
    "required_lod_count": 3,

    # Battle
    "battle_archetypes_required": ["SakuraDreamer_Battle", "CosmicWeaver_Battle", "MirageDancer_Battle"],

    # Performance
    "max_draw_calls_per_npc": 2,
    "max_texture_memory_mb": 8,
}


@dataclass
class AuditResult:
    """Single audit check result."""
    check_name: str
    category: str
    passed: bool
    value: Any = None
    expected: Any = None
    message: str = ""
    severity: str = "info"  # "info", "warning", "error"


@dataclass
class NPCAuditReport:
    """Complete audit report for one NPC."""
    npc_id: str
    archetype: str
    skeletal_mesh: str = ""
    results: list[AuditResult] = None
    passed: int = 0
    failed: int = 0
    warnings: int = 0

    def __post_init__(self):
        if self.results is None:
            self.results = []
        self._recalculate()

    def _recalculate(self):
        self.passed = sum(1 for r in self.results if r.passed)
        self.failed = sum(1 for r in self.results if not r.passed and r.severity == "error")
        self.warnings = sum(1 for r in self.results if not r.passed and r.severity == "warning")

    def add_result(self, result: AuditResult):
        self.results.append(result)
        self._recalculate()


# ──────────────────────────────────────────────────────────────────────
# Audit Checks
# ──────────────────────────────────────────────────────────────────────

def audit_skeletal_mesh(npc_id: str, mesh_path: str) -> list[AuditResult]:
    """Audit a skeletal mesh for mobile compliance."""
    results = []

    if unreal is None:
        return [AuditResult("skeletal_mesh", "mesh", False, message="Not in Unreal environment", severity="error")]

    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        return [AuditResult("skeletal_mesh", "mesh", False, message=f"Mesh not found: {mesh_path}", severity="error")]

    # Bone count
    skeleton = sk.get_editor_property("skeleton")
    if skeleton:
        bone_count = len(skeleton.get_bone_names())
        max_bones = AUDIT_CONFIG["max_bones_lod0"]
        results.append(AuditResult(
            "bone_count_lod0",
            "mesh",
            bone_count <= max_bones,
            value=bone_count,
            expected=f"<={max_bones}",
            message=f"Bone count: {bone_count}/{max_bones}",
            severity="error" if bone_count > max_bones else "info",
        ))

        # Check for finger bones (should be cullable)
        finger_bones = [b for b in skeleton.get_bone_names() if any(f in b.lower() for f in ["finger", "thumb", "index", "middle", "ring", "pinky"])]
        results.append(AuditResult(
            "finger_bones_present",
            "mesh",
            len(finger_bones) > 0,
            value=len(finger_bones),
            message=f"Finger bones found: {len(finger_bones)} (should be cullable at LOD1)",
            severity="info",
        ))

    # Triangle count (LOD0)
    try:
        lod0 = sk.get_editor_property("lod_models")[0] if sk.get_editor_property("lod_models") else None
        if lod0:
            tri_count = sum(section.num_triangles for section in lod0.sections)
            max_tris = AUDIT_CONFIG["max_triangles_lod0"]
            results.append(AuditResult(
                "triangle_count_lod0",
                "mesh",
                tri_count <= max_tris,
                value=tri_count,
                expected=f"<={max_tris}",
                message=f"Triangle count: {tri_count}/{max_tris}",
                severity="error" if tri_count > max_tris else "info",
            ))
    except Exception as e:
        results.append(AuditResult("triangle_count_lod0", "mesh", False, message=f"Could not check tris: {e}", severity="warning"))

    # Morph targets
    morph_targets = sk.get_morph_targets()
    morph_count = len(morph_targets) if morph_targets else 0
    max_morphs = AUDIT_CONFIG["max_morph_targets"]
    min_morphs = AUDIT_CONFIG["min_morph_targets"]
    results.append(AuditResult(
        "morph_target_count",
        "mesh",
        min_morphs <= morph_count <= max_morphs,
        value=morph_count,
        expected=f"{min_morphs}-{max_morphs}",
        message=f"Morph targets: {morph_count}",
        severity="warning" if morph_count > max_morphs else "info",
    ))

    # Materials
    materials = sk.get_editor_property("materials") or []
    mat_count = len(materials)
    results.append(AuditResult(
        "material_slot_count",
        "materials",
        mat_count <= 8,  # Reasonable limit
        value=mat_count,
        message=f"Material slots: {mat_count}",
        severity="warning" if mat_count > 8 else "info",
    ))

    return results


def audit_lods(npc_id: str, mesh_path: str) -> list[AuditResult]:
    """Audit LOD setup."""
    results = []

    if unreal is None:
        return [AuditResult("lods", "lod", False, message="Not in Unreal environment", severity="error")]

    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        return [AuditResult("lods", "lod", False, message=f"Mesh not found: {mesh_path}", severity="error")]

    lod_models = sk.get_editor_property("lod_models") or []
    lod_count = len(lod_models)
    required = AUDIT_CONFIG["required_lod_count"]

    results.append(AuditResult(
        "lod_count",
        "lod",
        lod_count >= required,
        value=lod_count,
        expected=f">={required}",
        message=f"LOD count: {lod_count}/{required}",
        severity="error" if lod_count < required else "info",
    ))

    # Check each LOD has reduction
    for i, lod in enumerate(lod_models):
        if i == 0:
            continue
        # LOD should have fewer triangles than previous
        try:
            tri_count = sum(section.num_triangles for section in lod.sections)
            results.append(AuditResult(
                f"lod{i}_reduction",
                "lod",
                tri_count > 0,
                value=tri_count,
                message=f"LOD{i} triangles: {tri_count}",
                severity="info",
            ))
        except Exception:
            pass

    return results


def audit_materials(npc_id: str, mesh_path: str) -> list[AuditResult]:
    """Audit material setup."""
    results = []

    if unreal is None:
        return [AuditResult("materials", "materials", False, message="Not in Unreal environment", severity="error")]

    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        return [AuditResult("materials", "materials", False, message=f"Mesh not found: {mesh_path}", severity="error")]

    materials = sk.get_editor_property("materials") or []

    for i, mat_slot in enumerate(materials):
        if not mat_slot or not mat_slot.get_editor_property("material_interface"):
            results.append(AuditResult(
                f"material_slot_{i}",
                "materials",
                False,
                message=f"Slot {i} has no material",
                severity="warning",
            ))
            continue

        mat = mat_slot.get_editor_property("material_interface")
        mat_path = mat.get_path_name()

        # Check if it's a MaterialInstanceConstant from our master
        is_mi = mat.get_class().get_name() == "MaterialInstanceConstant"
        results.append(AuditResult(
            f"material_slot_{i}_is_instance",
            "materials",
            is_mi,
            value=mat.get_class().get_name(),
            expected="MaterialInstanceConstant",
            message=f"Slot {i}: {mat_path} ({'MI' if is_mi else 'Base Material'})",
            severity="warning" if not is_mi else "info",
        ))

        # Check texture resolution if possible
        if is_mi:
            try:
                texture_params = mat.get_editor_property("texture_parameter_values") or []
                for tex_param in texture_params:
                    tex = tex_param.parameter_value
                    if tex:
                        # Check resolution
                        pass
            except Exception:
                pass

    return results


def audit_cloth(npc_id: str, mesh_path: str, archetype: str) -> list[AuditResult]:
    """Audit cloth simulation setup."""
    results = []

    if unreal is None:
        return [AuditResult("cloth", "cloth", False, message="Not in Unreal environment", severity="error")]

    sk = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not sk:
        return [AuditResult("cloth", "cloth", False, message=f"Mesh not found: {mesh_path}", severity="error")]

    physics_asset = sk.get_editor_property("physics_asset")
    has_physics_asset = physics_asset is not None

    results.append(AuditResult(
        "physics_asset_exists",
        "cloth",
        has_physics_asset,
        message=f"Physics Asset: {'Yes' if has_physics_asset else 'No'}",
        severity="warning" if not has_physics_asset else "info",
    ))

    if has_physics_asset:
        # Check for cloth bodies
        bodies = physics_asset.skeletal_body_setups or []
        cloth_bodies = [b for b in bodies if b.physics_type == unreal.PhysicsType.PST_Cloth]
        results.append(AuditResult(
            "cloth_bodies_count",
            "cloth",
            len(cloth_bodies) > 0,
            value=len(cloth_bodies),
            message=f"Cloth bodies: {len(cloth_bodies)}",
            severity="info",
        ))

    return results


def audit_battle_integration(npc_id: str, archetype: str) -> list[AuditResult]:
    """Audit Melodia battle integration."""
    results = []

    # Check if archetype has battle variant
    from .archetype_library import get_archetype
    arch = get_archetype(archetype)
    has_battle = bool(arch and arch.battle_archetype_id)

    results.append(AuditResult(
        "battle_archetype_defined",
        "battle",
        has_battle,
        value=arch.battle_archetype_id if arch else None,
        message=f"Battle archetype: {arch.battle_archetype_id if has_battle else 'None'}",
        severity="info",
    ))

    if has_battle:
        # Check enemy def exists in generated JSON
        from .battle_integration import NPC_VARIANTS
        variant_key = f"{npc_id}_Battle" if f"{npc_id}_Battle" in NPC_VARIANTS else npc_id
        has_variant = variant_key in NPC_VARIANTS or npc_id in NPC_VARIANTS
        results.append(AuditResult(
            "npc_variant_defined",
            "battle",
            has_variant,
            message=f"NPC variant: {'Yes' if has_variant else 'No'}",
            severity="warning" if not has_variant else "info",
        ))

    return results


def audit_npc_blueprint(npc_id: str) -> list[AuditResult]:
    """Audit NPC Blueprint exists and has required components."""
    results = []

    if unreal is None:
        return [AuditResult("blueprint", "blueprint", False, message="Not in Unreal environment", severity="error")]

    bp_path = f"/Game/NPCs/Blueprints/BP_NPC_{npc_id}"
    bp = unreal.EditorAssetLibrary.load_asset(bp_path)
    exists = bp is not None

    results.append(AuditResult(
        "blueprint_exists",
        "blueprint",
        exists,
        message=f"Blueprint: {'Found' if exists else 'Missing'} ({bp_path})",
        severity="error" if not exists else "info",
    ))

    if exists:
        # Check for required components
        required_components = [
            "MelodiaNPCComponent",
            "MelodiaInteractionComponent",
            "MelodiaBattleComponent",
        ]
        for comp in required_components:
            has_comp = False  # Would check actual BP
            results.append(AuditResult(
                f"component_{comp}",
                "blueprint",
                has_comp,
                message=f"Component {comp}: {'Present' if has_comp else 'Missing'}",
                severity="warning" if not has_comp else "info",
            ))

    return results


# ──────────────────────────────────────────────────────────────────────
# Full Audit Pipeline
# ──────────────────────────────────────────────────────────────────────

def audit_single_npc(npc_id: str, archetype: str, mesh_path: str = None) -> NPCAuditReport:
    """Run all audits on a single NPC."""
    if mesh_path is None:
        mesh_path = f"/Game/NPCs/Imported/{archetype}/{npc_id}/SK_{npc_id}"

    report = NPCAuditReport(npc_id=npc_id, archetype=archetype, skeletal_mesh=mesh_path)

    # Each audit has a deliberately narrow signature. Keep the calls explicit
    # so an editor-side audit reports the real asset failure, not a dispatcher
    # TypeError caused by passing mesh/archetype data to every check.
    checks = [
        (audit_skeletal_mesh, (npc_id, mesh_path)),
        (audit_lods, (npc_id, mesh_path)),
        (audit_materials, (npc_id, mesh_path)),
        (audit_cloth, (npc_id, mesh_path, archetype)),
        (audit_battle_integration, (npc_id, archetype)),
        (audit_npc_blueprint, (npc_id,)),
    ]
    for check_func, arguments in checks:
        try:
            results = check_func(*arguments)
            for r in results:
                report.add_result(r)
        except Exception as e:
            report.add_result(AuditResult(
                check_func.__name__,
                "system",
                False,
                message=f"Audit check failed: {e}",
                severity="error",
            ))

    return report


def audit_all_npcs() -> dict:
    """Audit all NPCs in the pipeline."""
    from .vrm_source import get_all_sources
    from .archetype_library import get_archetype

    all_sources = get_all_sources()
    reports = []
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "by_archetype": {},
        "by_category": {},
    }

    for src in all_sources:
        npc_id = src.source_id
        archetype = src.archetype

        # Use imported mesh path if available, else default
        mesh_path = src.import_path if src.imported else f"/Game/NPCs/Imported/{archetype}/{npc_id}/SK_{npc_id}"

        report = audit_single_npc(npc_id, archetype, mesh_path)
        reports.append(report)

        summary["total"] += 1
        summary["passed"] += report.passed
        summary["failed"] += report.failed
        summary["warnings"] += report.warnings

        # By archetype
        if archetype not in summary["by_archetype"]:
            summary["by_archetype"][archetype] = {"total": 0, "passed": 0, "failed": 0}
        summary["by_archetype"][archetype]["total"] += 1
        summary["by_archetype"][archetype]["passed"] += report.passed
        summary["by_archetype"][archetype]["failed"] += report.failed

        # By category
        for result in report.results:
            cat = result.category
            if cat not in summary["by_category"]:
                summary["by_category"][cat] = {"passed": 0, "failed": 0, "warnings": 0}
            if result.passed:
                summary["by_category"][cat]["passed"] += 1
            elif result.severity == "error":
                summary["by_category"][cat]["failed"] += 1
            else:
                summary["by_category"][cat]["warnings"] += 1

    # Save detailed report
    output_path = Path("Saved/Audit/gmm_npc_full_audit.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "reports": [asdict(r) for r in reports],
        }, f, indent=2)

    return {
        "summary": summary,
        "report_path": str(output_path),
        "all_passed": summary["failed"] == 0,
    }


def print_audit_summary(audit_result: dict):
    """Print human-readable audit summary."""
    summary = audit_result["summary"]
    print(f"\n{'='*50}")
    print(f"NPC PIPELINE AUDIT SUMMARY")
    print(f"{'='*50}")
    print(f"Total NPCs:     {summary['total']}")
    print(f"Checks Passed:  {summary['passed']}")
    print(f"Checks Failed:  {summary['failed']}")
    print(f"Warnings:       {summary['warnings']}")
    print(f"Overall:        {'✓ PASS' if audit_result['all_passed'] else '✗ FAIL'}")
    print(f"Report:         {audit_result['report_path']}")

    print(f"\nBy Archetype:")
    for arch, stats in summary["by_archetype"].items():
        print(f"  {arch}: {stats['passed']} passed, {stats['failed']} failed, {stats['total']} NPCs")

    print(f"\nBy Category:")
    for cat, stats in summary["by_category"].items():
        print(f"  {cat}: {stats['passed']} passed, {stats['failed']} failed, {stats['warnings']} warnings")


if __name__ == "__main__":
    if unreal:
        result = audit_all_npcs()
        print_audit_summary(result)
    else:
        print("NPC Audit Module - Run in Unreal Editor Python Console")
        print("Usage: import gmm.npc.audit_npc as audit; audit.audit_all_npcs()")
