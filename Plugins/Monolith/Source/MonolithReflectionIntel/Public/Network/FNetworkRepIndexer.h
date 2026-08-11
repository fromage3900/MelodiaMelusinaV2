// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FNetworkRepIndexer — sweeps the same UHT artefact corpus Phase 3a touches
// (Intermediate/Build/<Platform>/<Target>/Inc/<Module>/UHT/*.gen.cpp) for
// replication metadata and populates reflect_replicated_properties.
//
// Why a SECOND indexer pass instead of extending FUHTArtefactReader?
//   - Phase 3a is shipped and frozen. Re-touching it risks regressions in
//     Phase 1/2/3a query surfaces.
//   - Phase 4a's signal lives in the property-level *MetaData blocks Phase 3a
//     deliberately skipped (deviation #6 — reflect_uproperties.specifiers is
//     empty in Phase 3a). Adding a second sweeper keeps Phase 3a/4a code paths
//     independent — Phase 4b can either replace Phase 3a's regex sweep with
//     tree-sitter or extend this indexer; either evolution is mechanical.
//
// Replication signals observed in UHT `.gen.cpp` output (verified against
// engine reference output for `AActor` + project `ALeviathanCharacterBase`):
//
//   1. Per-property `NewProp_<Name>_MetaData[]` block containing pairs:
//        { "ReplicatedUsing", "OnRep_<Func>" }   — triggers ReplicatedUsing
//
//   2. The class's `Statics::PropPointers[]` array, with a per-property entry
//      tagged with `EPropertyGenFlags::Bit::PropertyIsRepNotify` — additional
//      "Replicated" signal even without OnRep.
//
//   3. The `Class_RepNotifyFuncs[]` array enumerates the RepNotify function
//      names referenced by a class. Useful cross-check for OnRep coverage
//      auditing but not REQUIRED — the per-property MetaData block is
//      authoritative for (property → rep_notify_func) edges.
//
// Phase 4a's regex sweep captures (1) directly (cheap, deterministic) and uses
// it as the sole signal source. Property names that appear in (2) without a
// MetaData match are flagged with rep_kind = "Replicated" + empty rep_notify_func.
//
// Idempotent — wipes + rewrites reflect_replicated_properties each Run().
// Game-thread only. PRAGMA journal_mode=DELETE is the caller's responsibility
// (matches the Phase 3a UHT reader contract).

#pragma once

#include "CoreMinimal.h"
#include "Containers/Array.h"
#include "Containers/Map.h"
#include "Internationalization/Regex.h"

class FSQLiteDatabase;

/** One extracted replicated-property row, buffered between scan and write. */
struct FNetworkRepPropertyRow
{
	FString OwningClass;
	FString PropertyName;
	FString CppModule;
	FString RepKind;        // "Replicated" or "ReplicatedUsing"
	FString RepNotifyFunc;  // OnRep_<Func> when ReplicatedUsing; empty otherwise
	FString SourcePath;     // ModuleRelativePath when known; empty otherwise
};

/** Aggregate per-artefact batch. */
struct FNetworkArtefactBatch
{
	TArray<FNetworkRepPropertyRow> ReplicatedProperties;
};

class MONOLITHREFLECTIONINTEL_API FNetworkRepIndexer
{
public:
	FNetworkRepIndexer();

	/**
	 * Walk `ArtefactRoots` for `*.gen.cpp` files, parse each, and write the
	 * reflect_replicated_properties table.
	 *
	 * @param DB              Open writable handle. Caller has enforced
	 *                        `PRAGMA journal_mode=DELETE`.
	 * @param ArtefactRoots   Absolute or project-relative directories. Empty
	 *                        array → auto-resolve via
	 *                        FPaths::ProjectIntermediateDir() / "Build".
	 * @param bIncludeEnginePlugins When true, also sweeps engine plugin Inc/
	 *                        directories.
	 * @param bAllowMarketplacePaths When true, the `/Engine/` skip filter makes
	 *                        a narrow exception for `/Plugins/Marketplace/`
	 *                        paths (engine-installed marketplace plugins live
	 *                        physically under /Engine/ but are NOT Epic
	 *                        built-ins). All OTHER /Engine/ paths stay blocked
	 *                        unless bIncludeEnginePlugins is set. Off by default.
	 * @param OutStatus       One-line summary printed to log + returned to MCP.
	 * @return true on schema success and at least one artefact scanned
	 *         (graceful degradation: zero artefacts = log warning + return
	 *         true with zero rows).
	 */
	bool Run(FSQLiteDatabase& DB,
		const TArray<FString>& ArtefactRoots,
		bool bIncludeEnginePlugins,
		bool bAllowMarketplacePaths,
		FString& OutStatus,
		/** Optional — receives the resolved absolute roots that DirectoryExists()
		 *  accepted (the ones actually walked). Default nullptr preserves the
		 *  existing API. */
		TArray<FString>* OutScannedRoots = nullptr,
		/** Optional — {AbsolutePath, Reason} pairs for any roots that were
		 *  SKIPPED at the DirectoryExists() gate. Surfaced by
		 *  `rebuild_reflection_index` so silent skips never recur. */
		TArray<TPair<FString, FString>>* OutSkippedRoots = nullptr);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);
	void WipeTables(FSQLiteDatabase& DB);

	/** Single-file scan. Reads the `.gen.cpp` into FileText, runs the regex
	 *  passes, fills OutBatch. */
	void ScanArtefact(const FString& AbsArtefactPath,
		const FString& ModuleName,
		FNetworkArtefactBatch& OutBatch);

	bool WriteBatch(FSQLiteDatabase& DB, const FNetworkArtefactBatch& Batch);

	/** Walk a root for `<Anywhere>/Inc/<Module>/UHT/*.gen.cpp`. Mirrors
	 *  Phase 3a's helper — duplication is intentional so Phase 4b can
	 *  consolidate without coupling.
	 *  bAllowMarketplacePaths opens a narrow /Plugins/Marketplace/ exception to
	 *  the /Engine/ skip filter — see Run() docs. */
	void CollectArtefacts(const FString& RootAbs, bool bIncludeEnginePlugins,
		bool bAllowMarketplacePaths,
		TArray<TPair<FString, FString>>& OutModuleAndArtefactPairs);

	// Phase 2 code-quality non-negotiable item 4 — FRegexPattern hoisted to
	// member scope. Re-used per file; FRegexMatcher per-text-input is what
	// binds to a specific buffer.
	FRegexPattern IwyuIncludePattern;        // grabs source header from "// IWYU pragma: private, include "<path>""
	FRegexPattern BeginClassPattern;         // "// ********** Begin Class <Name> ***..."
	FRegexPattern NewPropMetaDataHeader;     // "constexpr ... NewProp_<X>_MetaData[]"
	FRegexPattern MetaDataPairPattern;       // single `{ "Key", "Value" },` row
	FRegexPattern ClassPropertyFlagsPattern; // "Z_Construct_UClass_<C>_Statics::NewProp_<X> = { "<X>", ..., (EPropertyFlags)0x<HEX>,"
};
