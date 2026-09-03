// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FModuleDepRealityAdapter — registers a single action against the EXISTING
// `source` namespace (the same namespace MonolithSource owns), surfacing the
// module-dep-reality audit. Multi-module registration against one namespace is
// supported by FMonolithToolRegistry (registry keys are `namespace.action`),
// so this lives in MonolithReflectionIntel while extending source_query.
//
// Action surface:
//   source_query("audit_module_dep_reality", {scan_root?, limit?, cursor?})
//
// Bug class caught: `feedback_softptr_uproperty_needs_module_dep.md`
// (UPROPERTY edits using TSoftObjectPtr<UMyClass> where UMyClass lives in a
// module NOT in PrivateDependencyModuleNames). Catch rate is heuristic —
// regex-only; misses indirect typedef'd cases and macro-defined types.
//
// Algorithm (FModuleDepRealityAdapter.cpp):
//   1. Walk Source/* + Plugins/*/Source/* recursively for `.Build.cs` files.
//      Parse the C# `Private|PublicDependencyModuleNames.Add(Range)` string
//      list contents via regex. Build: module_dir → declared_modules set.
//   2. For every `.h` / `.cpp` under that module_dir, regex-extract identifier
//      patterns matching `[FUAEI][A-Z][A-Za-z0-9_]+` (UE naming convention).
//      These are CANDIDATE symbols.
//   3. Resolve each candidate to its declaring module via the existing
//      MonolithSource `symbols` × `files` × `modules` join. Skip candidates
//      that don't resolve (the project's own types are over-counted by the
//      regex — Build.cs would not need to list its own module).
//   4. Emit a violation row when:
//          declaring_module != current_module
//          AND declaring_module NOT IN declared_modules_for_current_module.
//
// False-positive mitigation:
//   - Skip if declaring_module == current_module (own-module use, not a dep).
//   - Skip well-known engine modules already implicit in any UE module
//     (`Core`, `CoreUObject`, `Engine`).
//   - Skip identifiers that hit multiple modules (ambiguous resolution).
//
// Read-only + idempotent. Game-thread only.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class MONOLITHREFLECTIONINTEL_API FModuleDepRealityAdapter
{
public:
	/** Register `source_query("audit_module_dep_reality")` + `source_query("suggest_build_cs_deps")`. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	static FMonolithActionResult HandleAuditModuleDepReality(const TSharedPtr<FJsonObject>& Params);

	/**
	 * Item 6 (Phase 2): forward direction of audit_module_dep_reality. Given a
	 * `file_path` (or `symbols[]`), resolve the DECLARING module path-first from
	 * the file_path (`Source/<Module>/...` / `Plugins/<X>/Source/<Module>/...`),
	 * read its `<Module>.Build.cs` from DISK (works on uncommitted/unindexed files),
	 * extract used UE types, resolve each used type's OWNING module via the
	 * EngineSource.db symbols/files/modules join, diff against the declared deps
	 * (apply the implicit Core/CoreUObject/Engine whitelist), and return
	 * required_modules[] + missing[]. RI/live-only — NOT offline-served (matches
	 * audit_module_dep_reality). Read-only, game-thread.
	 */
	static FMonolithActionResult HandleSuggestBuildCsDeps(const TSharedPtr<FJsonObject>& Params);

	/** Shared DB accessor — routes through the module's cached query DB. */
	static class FSQLiteDatabase* GetRawDB();

	/**
	 * Resolve the source subsystem's FMonolithSourceDatabase wrapper (NOT the raw
	 * handle). Exposes GetLock() so a borrower of GetRawHandle() can serialise its
	 * statement use per the borrow contract (MonolithSourceDatabase.h:116-120).
	 * Returns nullptr when the editor / subsystem / DB is unavailable. Game-thread
	 * only. Used by suggest_build_cs_deps to lock the borrow correctly.
	 */
	static class FMonolithSourceDatabase* GetSharedSourceDb();
};
