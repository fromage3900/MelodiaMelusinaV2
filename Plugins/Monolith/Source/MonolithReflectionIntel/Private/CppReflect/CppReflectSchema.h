// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// Internal-only schema accessors for the Phase 3a cppreflect tables. Mirrors the
// Phase 1 DecisionSchema.h / Phase 2 RiskSchema.h pattern — private headers, no
// other module needs the raw SQL strings; they exist so the UHT-artefact reader,
// the asset-graph joiner, and any future migration script share one source of
// truth.
//
// Six tables shipped in Phase 3a (Phase 3b deferred):
//   reflect_uclasses           — one row per UCLASS / UINTERFACE-companion class
//   reflect_uproperties        — one row per UPROPERTY field
//   reflect_ufunctions         — one row per UFUNCTION
//   reflect_uinterfaces        — one row per UINTERFACE (subset of UCLASSes; modelled
//                                separately so interface look-up stays cheap)
//   reflect_uinterface_impls   — class-implements-interface edge table
//   cpp_asset_edges            — UCLASS ↔ asset-on-disk relation rows
//
// Phase 3b (WISHLIST) will add `reflect_native_tag_decls` + `reflect_native_tag_externs`
// when tree-sitter vendoring lands — those need a real C++ AST walk, not a regex
// over UHT artefacts.

#pragma once

#include "CoreMinimal.h"

namespace MonolithCppReflectSchema
{
	// Core tables.
	const TCHAR* GetCreateUClassesTableSQL();
	const TCHAR* GetCreateUPropertiesTableSQL();
	const TCHAR* GetCreateUFunctionsTableSQL();
	const TCHAR* GetCreateUInterfacesTableSQL();
	const TCHAR* GetCreateUInterfaceImplsTableSQL();
	const TCHAR* GetCreateCppAssetEdgesTableSQL();

	// Helper indices (nice-to-have, non-fatal if they fail).
	const TCHAR* GetCreateUPropertiesIndexOwningClassSQL();
	const TCHAR* GetCreateUFunctionsIndexOwningClassSQL();
	const TCHAR* GetCreateUFunctionsIndexBlueprintCallableSQL();
	const TCHAR* GetCreateCppAssetEdgesIndexClassSQL();
	const TCHAR* GetCreateCppAssetEdgesIndexKindSQL();
}
