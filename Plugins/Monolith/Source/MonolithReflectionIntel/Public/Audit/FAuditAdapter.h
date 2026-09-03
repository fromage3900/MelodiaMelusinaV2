// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FAuditAdapter — registers FOUR audit actions against EXISTING namespaces
// (material, niagara, blueprint, project) against the central
// FMonolithToolRegistry. Multi-module registration against one namespace is
// supported by FMonolithToolRegistry (registry keys are `namespace.action`),
// so these live in MonolithReflectionIntel while extending the namespaces
// owned by sibling Monolith modules. Same pattern as Phase 2's
// `source_query("audit_module_dep_reality")`.
//
// Action surfaces (Phase 4a):
//   material_query("audit_orphan_materials", {limit?, cursor?})
//     Lists `/Game/.../*.uasset` materials with zero IAssetRegistry::GetReferencers
//     hits — no other asset references this material. Excludes engine-only and
//     test materials.
//
//   niagara_query("audit_cross_asset_refs", {limit?, cursor?})
//     Lists Niagara systems referencing C++ classes that no longer exist
//     (asset_path → cpp_class JOIN where reflect_uclasses has no match). Uses
//     Phase 3a's cpp_asset_edges. Common after a class rename/removal where
//     the asset still points at the dead class.
//
//   blueprint_query("audit_cdo_drift", {class_filter?, limit?, cursor?})
//     Surfaces UCLASS UPROPERTYs whose native parent's CDO default differs
//     from the BP child's CDO override. Phase 4a flags ANY edge of drift on
//     the BP-visible specifier; Phase 4b will deepen to typed-aware comparison.
//
//   project_query("audit_orphan_assets", {asset_class_filter?, limit?, cursor?})
//     Assets with zero referrers in IAssetRegistry's dependency graph AND
//     zero `cpp_asset_edges`-side referrers. Strictest orphan signal. Useful
//     for pre-release cleanup audits.
//
// All four are read-only + idempotent, decorated for v0.17.0 ergonomics, and
// participate in cursor pagination. None mutate state.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class MONOLITHREFLECTIONINTEL_API FAuditAdapter
{
public:
	/** Register all 4 cross-namespace audit actions. Does NOT touch dispatcher
	 *  annotations on the host namespaces — those are owned by the sibling
	 *  Monolith modules that primarily populate the namespace. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Action handlers ---
	static FMonolithActionResult HandleAuditOrphanMaterials(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAuditNiagaraCrossAssetRefs(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAuditCdoDrift(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleAuditOrphanAssets(const TSharedPtr<FJsonObject>& Params);

	/** Shared DB accessor — routes through the module's cached query DB. */
	static class FSQLiteDatabase* GetRawDB();
};
