// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// FAssetGraphJoiner — implementation. Cross-joins reflect_uclasses against
// IAssetRegistry to produce cpp_asset_edges rows.

#include "CppReflect/FAssetGraphJoiner.h"
#include "CppReflect/CppReflectSchema.h"
#include "MonolithReflectionIntelModule.h"

#include "AssetRegistry/AssetData.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "Modules/ModuleManager.h"
#include "SQLiteDatabase.h"
#include "UObject/TopLevelAssetPath.h"

namespace
{
	/**
	 * `/Script/<Module>.<ClassName>` is the canonical FTopLevelAssetPath form
	 * for native UClass references. Strip the prefix and return the bare
	 * `<ClassName>` token. For asset paths like `/Game/Foo/Bar.Bar_C`, returns
	 * an empty FString — caller treats that as "not a native-class match".
	 */
	FString ExtractNativeClassName(const FTopLevelAssetPath& Path)
	{
		const FString PathStr = Path.ToString();
		if (PathStr.IsEmpty() || !PathStr.StartsWith(TEXT("/Script/")))
		{
			return FString();
		}
		const int32 DotIdx = PathStr.Find(TEXT("."), ESearchCase::CaseSensitive,
			ESearchDir::FromStart, 8 /*after "/Script/"*/);
		if (DotIdx == INDEX_NONE) { return FString(); }
		return PathStr.Mid(DotIdx + 1);
	}

	/**
	 * Common Phase 3a normalisation — try matching `ClassName` against the
	 * known-set both verbatim and with the U/A/F/I single-char prefix added.
	 * AssetClassPath ships the bare struct name (e.g. "StaticMesh"), but the
	 * UHT-derived reflect_uclasses ships the prefixed C++ symbol
	 * (e.g. "UStaticMesh"). Try both.
	 */
	bool ResolveKnownClass(const TSet<FString>& KnownClasses, const FString& BareName,
		FString& OutCanonical)
	{
		if (BareName.IsEmpty()) { return false; }
		if (KnownClasses.Contains(BareName))
		{
			OutCanonical = BareName;
			return true;
		}
		for (const TCHAR* Prefix : { TEXT("A"), TEXT("U"), TEXT("F"), TEXT("I") })
		{
			const FString Candidate = FString(Prefix) + BareName;
			if (KnownClasses.Contains(Candidate))
			{
				OutCanonical = Candidate;
				return true;
			}
		}
		return false;
	}
}

bool FAssetGraphJoiner::Run(FSQLiteDatabase& DB, FString& OutStatus)
{
	ensure(IsInGameThread());

	if (!EnsureSchema(DB))
	{
		OutStatus = TEXT("FAssetGraphJoiner: schema bootstrap failed");
		UE_LOG(LogMonolithReflectionIntel, Error, TEXT("%s"), *OutStatus);
		return false;
	}

	// Wipe + rewrite — same idempotent contract as the other indexers.
	{
		FSQLitePreparedStatement Del;
		Del.Create(DB, TEXT("DELETE FROM cpp_asset_edges;"));
		Del.Execute();
	}

	// Force-load AssetRegistry module. `LoadModuleChecked` is the canonical
	// idiom per `AssetTools.cpp:2861` + `AnimationSettingsModule.cpp:71`.
	FAssetRegistryModule& ARModule =
		FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
	IAssetRegistry& AR = ARModule.Get();

	TSet<FString> KnownClasses;
	if (!LoadKnownClassNames(DB, KnownClasses))
	{
		OutStatus = TEXT(
			"FAssetGraphJoiner: reflect_uclasses missing or empty — run UHT "
			"artefact pass first.");
		UE_LOG(LogMonolithReflectionIntel, Warning, TEXT("%s"), *OutStatus);
		return false;
	}

	// Enumerate all assets. The plan acknowledges this can be slow on huge
	// registries; cost matches the design-spec Q6 ~30s budget for projects.
	TArray<FAssetData> AllAssets;
	if (!AR.GetAllAssets(AllAssets, /*bIncludeOnlyOnDiskAssets=*/false))
	{
		OutStatus = TEXT("FAssetGraphJoiner: IAssetRegistry::GetAllAssets failed");
		UE_LOG(LogMonolithReflectionIntel, Warning, TEXT("%s"), *OutStatus);
		return false;
	}

	int32 InstanceEdges = 0;

	FSQLitePreparedStatement Ins;
	if (!Ins.Create(DB, TEXT(
		"INSERT OR IGNORE INTO cpp_asset_edges (cpp_class, asset_path, edge_kind) "
		"VALUES (?, ?, ?);")))
	{
		OutStatus = TEXT("FAssetGraphJoiner: INSERT prepare failed");
		UE_LOG(LogMonolithReflectionIntel, Error, TEXT("%s"), *OutStatus);
		return false;
	}

	DB.Execute(TEXT("BEGIN TRANSACTION;"));

	// Phase 3a emits ONLY `instance_of` edges. The Phase 3a implementation
	// previously also emitted `(asset_class, dep_package_name, "references_class")`
	// rows, but the semantics were mis-attributed: that row reads "ClassX
	// references PackageY" while the actual fact is "AssetA (an instance of
	// ClassX) references PackageY". A `WHERE cpp_class = '<X>'` caller would
	// see asset-instance noise instead of class-level intent. Phase 3b will
	// revisit with per-package class extraction to produce semantically
	// honest references_class edges; the column + index stay in the schema
	// so the rewrite is purely additive.

	for (const FAssetData& Asset : AllAssets)
	{
		const FString PackageNameStr = Asset.PackageName.ToString();
		// Skip script packages (the registry sometimes enumerates synthetic
		// `/Script/<Module>` entries that are not real assets-on-disk).
		if (PackageNameStr.StartsWith(TEXT("/Script/"))) { continue; }

		// instance_of edge — the asset IS an instance of its native class.
		// This row is semantically correct: `cpp_class` is the asset's class,
		// `asset_path` is the asset's package on disk.
		const FString AssetClassBare = ExtractNativeClassName(Asset.AssetClassPath);
		FString Canonical;
		if (ResolveKnownClass(KnownClasses, AssetClassBare, Canonical))
		{
			Ins.Reset();
			Ins.ClearBindings();
			Ins.SetBindingValueByIndex(1, Canonical);
			Ins.SetBindingValueByIndex(2, PackageNameStr);
			Ins.SetBindingValueByIndex(3, FString(TEXT("instance_of")));
			if (Ins.Execute()) { ++InstanceEdges; }
		}
	}

	DB.Execute(TEXT("COMMIT;"));

	OutStatus = FString::Printf(
		TEXT("FAssetGraphJoiner: %d assets scanned → instance_of=%d (references_class deferred to Phase 3b)"),
		AllAssets.Num(), InstanceEdges);
	UE_LOG(LogMonolithReflectionIntel, Log, TEXT("%s"), *OutStatus);
	return true;
}

bool FAssetGraphJoiner::EnsureSchema(FSQLiteDatabase& DB)
{
	auto Exec = [&DB](const TCHAR* Sql) -> bool
	{
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, Sql)) { return false; }
		return Stmt.Execute();
	};
	using namespace MonolithCppReflectSchema;
	if (!Exec(GetCreateCppAssetEdgesTableSQL())) { return false; }
	Exec(GetCreateCppAssetEdgesIndexClassSQL());
	Exec(GetCreateCppAssetEdgesIndexKindSQL());
	return true;
}

bool FAssetGraphJoiner::LoadKnownClassNames(FSQLiteDatabase& DB, TSet<FString>& OutClassNames)
{
	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(DB, TEXT("SELECT DISTINCT class_name FROM reflect_uclasses;")))
	{
		return false;
	}
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString Name;
		Stmt.GetColumnValueByIndex(0, Name);
		if (!Name.IsEmpty()) { OutClassNames.Add(Name); }
	}
	return OutClassNames.Num() > 0;
}
