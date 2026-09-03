// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// FCppReflectQueryAdapter — registers the `cppreflect` namespace (6 actions)
// against the central FMonolithToolRegistry. Pure read-only handlers; no
// indexing happens here (that's FUHTArtefactReader / FAssetGraphJoiner).
//
// DEVIATION (vs plan §7 handler enumeration): plan §7 lists SIX handlers
// including `list_native_tags`. Phase 3a explicitly drops the native-tag
// surface — that needs the tree-sitter vendoring deferred to Phase 3b. The
// 6 actions shipped here are: get_uclass / list_uproperties / list_ufunctions
// / find_interface_impls / find_class_specifier / list_class_specifiers.
//
// v0.17.0 ergonomics adoption (same shape as decision_query + risk_query):
//   - `class_name` / `interface_name` / `specifier_name` are bare strings
//     (NOT path-typed; class names are not paths).
//   - `path_filter` would be DiskPath but no path-filter param is exposed
//     in this action surface (class-name based lookups dominate).
//   - Dispatcher annotated readOnlyHint=true + idempotentHint=true.
//   - `list_uproperties`, `list_ufunctions`, `find_class_specifier` adopt
//     cursor pagination — Monolith + project may yield hundreds of rows per
//     class for component-heavy CDOs.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class MONOLITHREFLECTIONINTEL_API FCppReflectQueryAdapter
{
public:
	/** Register all 6 cppreflect actions + dispatcher annotations. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Action handlers ---
	static FMonolithActionResult HandleGetUClass(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListUProperties(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListUFunctions(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindInterfaceImpls(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindClassSpecifier(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListClassSpecifiers(const TSharedPtr<FJsonObject>& Params);

	/** Shared DB accessor — routes through the module's cached query DB. */
	static class FSQLiteDatabase* GetRawDB();
};
