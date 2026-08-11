// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// FAssetGraphJoiner — cross-joins reflect_uclasses (populated by
// FUHTArtefactReader) against IAssetRegistry to produce cpp_asset_edges rows.
//
// API verification (Iron Law 1) — UE 5.7:
//   - `FAssetRegistryModule` — Engine/Source/Runtime/AssetRegistry/Public/
//     AssetRegistry/AssetRegistryModule.h:51. Module name: "AssetRegistry"
//     (Engine/Source/Runtime/AssetRegistry/AssetRegistry.Build.cs).
//   - `IAssetRegistry::Get()` — IAssetRegistry.h:266 (returns nullable
//     pointer; UE::AssetRegistry::Private::IAssetRegistrySingleton::Get()).
//   - `IAssetRegistry::GetAllAssets(TArray<FAssetData>&, bool)`
//     — IAssetRegistry.h:465. Slow on huge registries; documented "use a
//     filter if possible" but Phase 3a wants the full enumeration once.
//   - `IAssetRegistry::GetDependencies(FName PackageName, TArray<FName>&,
//     UE::AssetRegistry::EDependencyCategory, FDependencyQuery)`
//     — IAssetRegistry.h:530. PackageName overload is the cheapest form.
//   - `FAssetData::AssetClassPath` (FTopLevelAssetPath) — AssetData.h:201.
//     The deprecated `FAssetData::AssetClass` (FName) is UE_DEPRECATED(5.1);
//     Phase 3a uses `AssetClassPath` exclusively.
//   - `FTopLevelAssetPath::ToString()` — TopLevelAssetPath.h:104.
//
// Strategy:
//   1. Enumerate all assets via IAssetRegistry::GetAllAssets.
//   2. For each asset, derive the bare C++ class name from
//      AssetClassPath.ToString() — strip "/Script/<Module>." prefix to get
//      the bare class name (e.g. "/Script/Engine.StaticMesh" → "UStaticMesh"
//      isn't quite right — the Script-class path uses the C++ struct name
//      directly, so /Script/Engine.StaticMesh maps to "StaticMesh"; we
//      attempt a match against reflect_uclasses both as-is AND with U/A
//      prefix stripping for tolerance).
//   3. Emit `instance_of` row when the class matches a reflect_uclasses
//      entry (deferred-resolution heuristic — Phase 3b will refine using
//      tree-sitter's inheritance walk).
//   4. For each ASSET → PackageDependencies, walk the dependency package
//      names and emit `references_class` rows when those packages happen
//      to be `/Script/<Module>` packages (i.e. C++ class references).
//      Asset → Blueprint-of-class is intentionally not handled in Phase 3a;
//      that needs the Blueprint generated-class inheritance walk.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Array.h"

class FSQLiteDatabase;

class MONOLITHREFLECTIONINTEL_API FAssetGraphJoiner
{
public:
	/**
	 * Run the asset-graph join. Idempotent — wipes + rewrites
	 * `cpp_asset_edges` in one transaction.
	 *
	 * @param DB         Open writable handle. Caller has enforced
	 *                   `PRAGMA journal_mode=DELETE`. Must also have already
	 *                   run FUHTArtefactReader so reflect_uclasses is fresh.
	 * @param OutStatus  One-line summary printed to log + returned to MCP.
	 * @return true on schema success and successful AssetRegistry access.
	 *         False if AssetRegistry was unreachable (editor not done loading).
	 */
	bool Run(FSQLiteDatabase& DB, FString& OutStatus);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);

	/** Pull every class_name currently in reflect_uclasses into a set. */
	bool LoadKnownClassNames(FSQLiteDatabase& DB, TSet<FString>& OutClassNames);
};
