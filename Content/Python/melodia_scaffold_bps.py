"""melodia_scaffold_bps.py — scaffold the long-term Melodia Blueprint systems.

Run inside the editor via Monolith:
    editor_query run_python -> Content/Python/melodia_scaffold_bps.py

    scaffold_all()                 # create anything missing
    scaffold_all(dry_run=True)     # report what it WOULD create, touch nothing
    cleanup_stray_traversal()      # remove the misnamed BP from 2026-08-14

WHAT THIS BUILDS, AND WHY EACH IS SHAPED THIS WAY

1. BP_MelodiaPortal — a *visible* traversal portal.
   It COMPOSES the existing, working pieces rather than reimplementing them:
   a UBoxComponent plus UMelodiaMapTransitionComponent. That component already
   self-binds to the owner's box in BeginPlay (MelodiaMapTransitionComponent.cpp:27)
   and routes through UMelodiaTravelSubsystem::TravelTo (.cpp:47), which buys
   allowlist validation and arrival-tag placement for free (Decision 023).
   BP_MelodiaTravelVolume is the invisible version of this and is NOT broken --
   its empty EventGraph is just UE's default disabled boilerplate. The only thing
   this adds is presentation: a mesh and an effect slot so a portal reads as a
   portal instead of an invisible trigger.

2. BP_MelodiaPhysicsProp — a swaying prop base class.
   SkeletalMeshComponent + an AnimBP slot, intended to carry a KawaiiPhysics bone
   chain for banners, chains, hanging lanterns and plants. Kawaii is
   AnimNode_KawaiiPhysics -- an AnimGraph node for secondary bone motion. It is the
   right tool for props that should *move*, and it cannot place anything: for
   settling props onto the ground use Content/Python/melodia_settle_props.py, which
   is plain rigid-body simulation. The two are complementary.

3. BP_MelodiaEncounterDef + BP_MelodiaBattleObserver — Melodia-facing RPG wrappers.
   Deliberately THIN. The stock TurnBasedJRPGTemplate keeps turn/target/damage/result
   authority (Decision 009, and AGENTS.md "Ownership"). These do not subclass the
   stock battle Blueprints, because AGENTS.md records that child BPs shadowing parent
   events is exactly how BP_MelodiaBattleUI ended up with ten empty overrides and no
   battle UI. The observer is presentation/diagnostics ONLY -- per the safe-hook
   contract it must never call CompleteBattle, never resume Quill, and never
   fabricate a result.

SAFETY
- Idempotent: every asset is checked first and skipped if it exists. Re-running is a
  no-op, so this is safe to run repeatedly while iterating.
- dry_run=True reports and changes nothing.
- Creates only NEW assets. Nothing existing is modified, so there is no graph to
  fingerprint and no rollback record needed.
"""
from __future__ import annotations

import unreal

PKG = "/Game/MelodiaIntegration/Blueprints"
TRAVERSAL = f"{PKG}/Traversal"
PROPS = "/Game/Melodia/Blueprints/Props"
RPG = f"{PKG}/RPG"

# The misnamed asset created 2026-08-14 by a create_blueprint call whose
# `asset_name` param was silently ignored, making `save_path` the whole path.
STRAY = f"{PKG}/Traversal"


def _exists(path: str) -> bool:
    return unreal.EditorAssetLibrary.does_asset_exist(path)


def _make_bp(folder: str, name: str, parent: type, dry_run: bool):
    path = f"{folder}/{name}"
    if _exists(path):
        unreal.log(f"[scaffold] SKIP {name} — already exists")
        return None
    if dry_run:
        unreal.log(f"[scaffold] would create {path} (parent {parent.__name__})")
        return None

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name=name, package_path=folder, asset_class=unreal.Blueprint,
        factory=factory)
    if not bp:
        unreal.log_error(f"[scaffold] FAILED to create {path}")
        return None
    unreal.log(f"[scaffold] created {path}")
    return bp


def _add_component(bp, comp_class, comp_name: str):
    """Add a component to a Blueprint's SCS. Returns the new node or None."""
    try:
        subsystem = unreal.get_editor_subsystem(unreal.SubobjectDataSubsystem)
        handles = subsystem.k2_gather_subobject_data_for_blueprint(bp)
        if not handles:
            unreal.log_warning(f"[scaffold] no root subobject on {bp.get_name()}")
            return None
        _, new_handle = subsystem.add_new_subobject(
            unreal.AddNewSubobjectParams(
                parent_handle=handles[0], new_class=comp_class, blueprint_context=bp))
        subsystem.rename_subobject(handle=new_handle, new_name=comp_name)
        return new_handle
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[scaffold] could not add {comp_name}: {exc}")
        return None


def cleanup_stray_traversal(dry_run: bool = False):
    """Remove the misnamed 'Traversal' Blueprint created 2026-08-14.

    Deleted through the editor rather than off disk on purpose: AGENTS.md records
    that removing a .uasset from the filesystem leaves a dead redirector that then
    looks exactly like file corruption.
    """
    if not _exists(STRAY):
        unreal.log("[scaffold] no stray 'Traversal' asset — nothing to clean.")
        return False
    refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(STRAY, False)
    if refs:
        unreal.log_warning(f"[scaffold] '{STRAY}' has {len(refs)} referencer(s); NOT deleting. {refs[:5]}")
        return False
    if dry_run:
        unreal.log(f"[scaffold] would delete unreferenced stray {STRAY}")
        return False
    unreal.EditorAssetLibrary.delete_asset(STRAY)
    unreal.log(f"[scaffold] deleted stray {STRAY}")
    return True


def scaffold_all(dry_run: bool = False):
    created = []

    # --- 1. Visible traversal portal --------------------------------------
    bp = _make_bp(TRAVERSAL, "BP_MelodiaPortal", unreal.Actor, dry_run)
    if bp:
        _add_component(bp, unreal.SceneComponent, "PortalRoot")
        _add_component(bp, unreal.StaticMeshComponent, "PortalFrame")
        _add_component(bp, unreal.BoxComponent, "TravelVolume")
        # The component that does the actual work. It finds the box itself.
        mt = unreal.load_class(None, "/Script/BS_GodFile.MelodiaMapTransitionComponent")
        if mt:
            _add_component(bp, mt, "MelodiaMapTransition")
        else:
            unreal.log_warning("[scaffold] MelodiaMapTransitionComponent not found — "
                               "is the BS_GodFile module built? Portal will not travel.")
        _add_component(bp, unreal.NiagaraComponent, "PortalFX")
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        created.append("BP_MelodiaPortal")

    # --- 2. Kawaii swaying prop base --------------------------------------
    bp = _make_bp(PROPS, "BP_MelodiaPhysicsProp", unreal.Actor, dry_run)
    if bp:
        _add_component(bp, unreal.SceneComponent, "PropRoot")
        # Skeletal, not static: KawaiiPhysics drives bone chains, so a sway prop
        # must have a skeleton even when it is scenery.
        _add_component(bp, unreal.SkeletalMeshComponent, "PropMesh")
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        created.append("BP_MelodiaPhysicsProp")

    # --- 3. Melodia-facing RPG wrappers -----------------------------------
    bp = _make_bp(RPG, "BP_MelodiaEncounterDef", unreal.DataAsset, dry_run)
    if bp:
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        created.append("BP_MelodiaEncounterDef")

    bp = _make_bp(RPG, "BP_MelodiaBattleObserver", unreal.Actor, dry_run)
    if bp:
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        created.append("BP_MelodiaBattleObserver")

    unreal.log(f"[scaffold] done. created={created or 'nothing (all present)'}")
    return created
