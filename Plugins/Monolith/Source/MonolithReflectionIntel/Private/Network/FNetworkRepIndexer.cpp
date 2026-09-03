// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FNetworkRepIndexer — implementation. Regex sweep over `*.gen.cpp` artefacts;
// writes reflect_replicated_properties.
//
// Structural anatomy of the UHT artefact (mirrors Phase 3a's understanding):
//
//   // ********** Begin Class <Name> *...*
//   ...
//   static constexpr UE::CodeGen::FMetaDataPairParam NewProp_<X>_MetaData[] = {
//       { "Category", "Foo" },
//       { "ReplicatedUsing", "OnRep_<Func>" },
//       ...
//   };
//   ...
//   // ********** End Class <Name>
//
// Phase 4a's signal: any NewProp_<X>_MetaData block containing a
// "ReplicatedUsing" key fires a ReplicatedUsing row. We do NOT yet detect bare
// `UPROPERTY(Replicated)` (without =OnRep) because UHT does not emit a
// "Replicated" MetaData pair — it sets PropertyIsRepNotify on the type-tag
// flags instead. Phase 4b will deepen the scan to cover bare Replicated rows
// via the PropPointers[] specifier-flag scan. For Phase 4a the audit surface
// focused on `audit_onrep_coverage` and `audit_unbalanced_onreps` benefits more
// from accurate ReplicatedUsing capture than partial Replicated capture.

#include "Network/FNetworkRepIndexer.h"
#include "Network/NetworkSchema.h"
#include "MonolithReflectionIntelModule.h"
#include "MonolithRIMetaTable.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "SQLiteDatabase.h"

namespace
{
	/** Walk up an absolute artefact path and return the `<Module>` segment that
	 *  appears between `/Inc/` and `/UHT/`. Returns FString() on failure.
	 *  Duplicated from FUHTArtefactReader.cpp on purpose — consolidation is
	 *  Phase 5+ work. */
	FString RepModuleNameFromArtefactDir(const FString& AbsArtefactPath)
	{
		FString Norm = AbsArtefactPath;
		Norm.ReplaceInline(TEXT("\\"), TEXT("/"));
		const int32 IncIdx = Norm.Find(TEXT("/Inc/"));
		const int32 UhtIdx = Norm.Find(TEXT("/UHT/"));
		if (IncIdx == INDEX_NONE || UhtIdx == INDEX_NONE || UhtIdx <= IncIdx + 5)
		{
			return FString();
		}
		const int32 StartIdx = IncIdx + 5; // skip "/Inc/"
		return Norm.Mid(StartIdx, UhtIdx - StartIdx);
	}
}

FNetworkRepIndexer::FNetworkRepIndexer()
	// Phase 2 code-quality non-negotiable #4 — patterns built once per indexer instance.
	: IwyuIncludePattern(
		TEXT("//\\s*IWYU\\s+pragma:\\s*private,\\s*include\\s*\"([^\"]+)\""))
	, BeginClassPattern(
		TEXT("//\\s*\\*+\\s*Begin\\s+Class\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+\\*"))
	, NewPropMetaDataHeader(
		// Match the start of a per-property MetaData block. Capture the
		// property name. UHT-emitted form:
		//   static constexpr UE::CodeGen::FMetaDataPairParam NewProp_<Name>_MetaData[]
		// Or the alternative `FMetaDataPairParam ...::NewProp_<Name>_MetaData[]` form.
		TEXT("NewProp_([A-Za-z_][A-Za-z0-9_]*)_MetaData\\s*\\["))
	, MetaDataPairPattern(
		// A `{ "Key", "Value" }` row inside a MetaDataPairParam[] body.
		TEXT("\\{\\s*\"([^\"]+)\"\\s*,\\s*\"([^\"]*)\"\\s*\\}"))
	, ClassPropertyFlagsPattern(
		// A class-MEMBER property declaration carrying its EPropertyFlags bitfield:
		//   const UECodeGen_Private::F<T>PropertyParams
		//     Z_Construct_UClass_<C>_Statics::NewProp_<X> = { "<X>", nullptr,
		//       (EPropertyFlags)0x<HEX>, ...
		// Anchored on `Z_Construct_UClass_` so FUNCTION-param properties
		// (Z_Construct_UFunction_*) and STRUCT members (Z_Construct_UScriptStruct_*)
		// are excluded — only UCLASS members can be UPROPERTY(Replicated).
		// Captures: 1=Class, 2=PropName-from-symbol, 3=PropName-from-literal,
		// 4=64-bit hex EPropertyFlags. Verified against UE 5.7 WeaponBase_ISX.gen.cpp.
		TEXT("Z_Construct_UClass_([A-Za-z_][A-Za-z0-9_]*)_Statics::NewProp_([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*\\{\\s*\"([^\"]+)\"\\s*,\\s*[^,]*,\\s*\\(EPropertyFlags\\)0x([0-9A-Fa-f]+)"))
{
}

// EPropertyFlags bit values — mirror of
// Engine/Source/Runtime/CoreUObject/Public/UObject/ObjectMacros.h (EPropertyFlags).
// Verified via offline source index against UE 5.7. Replication-relevant bits.
namespace
{
	constexpr uint64 kCPF_Net       = 0x0000000000000020ull; // CPF_Net — relevant to network replication
	constexpr uint64 kCPF_RepNotify = 0x0000000100000000ull; // CPF_RepNotify — notify on replicate (ReplicatedUsing)
}

bool FNetworkRepIndexer::Run(FSQLiteDatabase& DB,
	const TArray<FString>& ArtefactRoots,
	bool bIncludeEnginePlugins,
	bool bAllowMarketplacePaths,
	FString& OutStatus,
	TArray<FString>* OutScannedRoots,
	TArray<TPair<FString, FString>>* OutSkippedRoots)
{
	ensure(IsInGameThread());

	// EnsureMetaTable up front — handover doc item #1 (stale-detection).
	MonolithRIMeta::EnsureMetaTable(DB);

	if (!EnsureSchema(DB))
	{
		OutStatus = TEXT("FNetworkRepIndexer: schema bootstrap failed");
		UE_LOG(LogMonolithReflectionIntel, Error, TEXT("%s"), *OutStatus);
		return false;
	}

	WipeTables(DB);

	// Resolve roots. Empty = auto-resolve.
	TArray<FString> ResolvedRoots;
	const FString ProjectRoot =
		FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());

	if (ArtefactRoots.Num() == 0)
	{
		ResolvedRoots.Add(FPaths::ConvertRelativePathToFull(
			FPaths::ProjectIntermediateDir() / TEXT("Build")));
	}
	else
	{
		for (const FString& RawRoot : ArtefactRoots)
		{
			FString Root = RawRoot;
			if (FPaths::IsRelative(Root))
			{
				Root = FPaths::ConvertRelativePathToFull(ProjectRoot / Root);
			}
			ResolvedRoots.Add(FPaths::ConvertRelativePathToFull(Root));
		}
	}

	// Handover doc item #2 — track scanned vs skipped roots and surface them up
	// through the optional output params. Missing-root log bumped Verbose →
	// Warning so silent skips become visible (the marketplace-scan rebase bug
	// took 2 cycles purely because this was Verbose).
	TArray<TPair<FString, FString>> ModuleAndArtefactPairs;
	for (const FString& Root : ResolvedRoots)
	{
		IPlatformFile& Pf = FPlatformFileManager::Get().GetPlatformFile();
		if (!Pf.DirectoryExists(*Root))
		{
			UE_LOG(LogMonolithReflectionIntel, Warning,
				TEXT("FNetworkRepIndexer: skipping missing root '%s'"), *Root);
			if (OutSkippedRoots)
			{
				OutSkippedRoots->Emplace(Root, TEXT("directory does not exist"));
			}
			continue;
		}
		if (OutScannedRoots)
		{
			OutScannedRoots->Add(Root);
		}
		CollectArtefacts(Root, bIncludeEnginePlugins, bAllowMarketplacePaths, ModuleAndArtefactPairs);
	}

	if (ModuleAndArtefactPairs.Num() == 0)
	{
		OutStatus = TEXT(
			"FNetworkRepIndexer: no UHT artefacts found — has the project built "
			"with UBT yet? (Live Coding patches do not produce gen.cpp).");
		UE_LOG(LogMonolithReflectionIntel, Warning, TEXT("%s"), *OutStatus);
		// Stamp the code-version on zero-artefact success (handover item #1).
		MonolithRIMeta::WriteStoredVersion(DB, TEXT("network"),
			MonolithRIMeta::GetIndexerCodeVersion(TEXT("network")));
		return true;
	}

	int32 TotalReps = 0;
	int32 FilesScanned = 0;

	for (const TPair<FString, FString>& Pair : ModuleAndArtefactPairs)
	{
		FNetworkArtefactBatch Batch;
		ScanArtefact(/*AbsArtefactPath=*/Pair.Value,
		             /*ModuleName=*/Pair.Key,
		             /*OutBatch=*/Batch);

		if (!WriteBatch(DB, Batch))
		{
			UE_LOG(LogMonolithReflectionIntel, Warning,
				TEXT("FNetworkRepIndexer: write failed for %s"), *Pair.Value);
		}

		TotalReps += Batch.ReplicatedProperties.Num();
		++FilesScanned;
	}

	OutStatus = FString::Printf(
		TEXT("FNetworkRepIndexer: %d artefacts scanned → ReplicatedProperties=%d"),
		FilesScanned, TotalReps);
	UE_LOG(LogMonolithReflectionIntel, Log, TEXT("%s"), *OutStatus);

	// Handover doc item #1 — stamp the network code-version on success.
	MonolithRIMeta::WriteStoredVersion(DB, TEXT("network"),
		MonolithRIMeta::GetIndexerCodeVersion(TEXT("network")));
	return true;
}

bool FNetworkRepIndexer::EnsureSchema(FSQLiteDatabase& DB)
{
	auto Exec = [&DB](const TCHAR* Sql) -> bool
	{
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, Sql))
		{
			UE_LOG(LogMonolithReflectionIntel, Error,
				TEXT("FNetworkRepIndexer DDL prepare failed: %s"), Sql);
			return false;
		}
		return Stmt.Execute();
	};

	using namespace MonolithNetworkSchema;
	if (!Exec(GetCreateReplicatedPropertiesTableSQL())) { return false; }
	// Indices are non-fatal.
	Exec(GetCreateReplicatedPropertiesIndexOwningClassSQL());
	Exec(GetCreateReplicatedPropertiesIndexRepNotifySQL());
	return true;
}

void FNetworkRepIndexer::WipeTables(FSQLiteDatabase& DB)
{
	FSQLitePreparedStatement Stmt;
	Stmt.Create(DB, TEXT("DELETE FROM reflect_replicated_properties;"));
	Stmt.Execute();
}

void FNetworkRepIndexer::CollectArtefacts(
	const FString& RootAbs, bool bIncludeEnginePlugins,
	bool bAllowMarketplacePaths,
	TArray<TPair<FString, FString>>& OutModuleAndArtefactPairs)
{
	class FCppGenVisitor : public IPlatformFile::FDirectoryVisitor
	{
	public:
		TArray<TPair<FString, FString>>& Out;
		bool bIncludeEngine;
		bool bAllowMarketplace;
		explicit FCppGenVisitor(TArray<TPair<FString, FString>>& InOut, bool bInIncludeEngine, bool bInAllowMarketplace)
			: Out(InOut), bIncludeEngine(bInIncludeEngine), bAllowMarketplace(bInAllowMarketplace) {}

		virtual bool Visit(const TCHAR* FilenameOrDirectory, bool bIsDirectory) override
		{
			if (bIsDirectory) { return true; }
			const FString Path(FilenameOrDirectory);
			FString Norm = Path;
			Norm.ReplaceInline(TEXT("\\"), TEXT("/"));
			if (!Norm.EndsWith(TEXT(".gen.cpp"), ESearchCase::IgnoreCase)) { return true; }
			if (Norm.Find(TEXT("/UHT/")) == INDEX_NONE) { return true; }
			// Engine-plugin filter: skip "/Engine/" paths unless opted in.
			// Narrow exception: when bAllowMarketplace is set we permit
			// "/Plugins/Marketplace/" paths (engine-installed marketplace
			// plugins live under /Engine/ but are NOT Epic built-ins). All
			// OTHER /Engine/ paths stay blocked.
			if (!bIncludeEngine && Norm.Find(TEXT("/Engine/")) != INDEX_NONE
				&& !(bAllowMarketplace && Norm.Contains(TEXT("/Plugins/Marketplace/"))))
			{
				return true;
			}
			const FString Module = RepModuleNameFromArtefactDir(Norm);
			if (Module.IsEmpty()) { return true; }
			Out.Emplace(Module, Norm);
			return true;
		}
	};
	FCppGenVisitor Visitor(OutModuleAndArtefactPairs, bIncludeEnginePlugins, bAllowMarketplacePaths);
	IFileManager::Get().IterateDirectoryRecursively(*RootAbs, Visitor);
}

void FNetworkRepIndexer::ScanArtefact(
	const FString& AbsArtefactPath,
	const FString& ModuleName,
	FNetworkArtefactBatch& OutBatch)
{
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *AbsArtefactPath)) { return; }

	TArray<FString> Lines;
	Text.ParseIntoArrayLines(Lines, /*InCullEmpty=*/false);

	FString SourceHeaderRel; // from IWYU pragma line, file-level
	{
		FRegexMatcher M(IwyuIncludePattern, Text);
		if (M.FindNext())
		{
			SourceHeaderRel = M.GetCaptureGroup(1);
		}
	}

	// State machine. Track current Class banner + current per-property
	// MetaData block (open when we see `NewProp_<X>_MetaData[]`, close at
	// the first `};` line after the header).
	FString CurrentClass;
	FString CurrentMetaProperty;
	bool bInMetaBlock = false;
	FString PendingRepKind;
	FString PendingRepNotifyFunc;

	// ReplicatedUsing-emitted keys ("Class|Prop") — the bare-Replicated fallback
	// below skips these so a ReplicatedUsing property is never double-emitted.
	TSet<FString> EmittedReplicatedUsingKeys;

	// CPF_Net harvest. The replication type-tag lives on the class-member
	// property DECLARATION line (outside any MetaData block):
	//   const ...F<T>PropertyParams Z_Construct_UClass_<C>_Statics::NewProp_<X>
	//     = { "<X>", nullptr, (EPropertyFlags)0x...Net..., ... }
	// We harvest every (Class|Prop) carrying CPF_Net here, then emit a
	// rep_kind="Replicated" row for any that did NOT already fire ReplicatedUsing
	// (bare UPROPERTY(Replicated) and GAS DOREPLIFETIME-driven replication —
	// both set CPF_Net without a "ReplicatedUsing" MetaData pair).
	struct FNetPropHarvest
	{
		FString OwningClass;
		FString PropertyName;
		bool    bRepNotify = false; // CPF_RepNotify also set → it's a ReplicatedUsing prop
	};
	TArray<FNetPropHarvest> NetProps;
	TSet<FString> NetPropKeysSeen; // dedupe harvest on "Class|Prop"

	for (int32 LineIdx = 0; LineIdx < Lines.Num(); ++LineIdx)
	{
		const FString& Line = Lines[LineIdx];

		// ------ Begin Class banner — open a new Class segment.
		{
			FRegexMatcher M(BeginClassPattern, Line);
			if (M.FindNext())
			{
				CurrentClass = M.GetCaptureGroup(1);
				// Reset any in-progress meta-block state if a previous block
				// did not close cleanly (defensive).
				CurrentMetaProperty.Empty();
				bInMetaBlock = false;
				PendingRepKind.Empty();
				PendingRepNotifyFunc.Empty();
				continue;
			}
		}

		if (CurrentClass.IsEmpty()) { continue; }

		// ------ CPF_Net harvest (class-member property declarations). Scanned
		// on every in-class line, independent of MetaData-block state, because
		// the declaration line sits OUTSIDE the per-property MetaData arrays.
		{
			FRegexMatcher FlagM(ClassPropertyFlagsPattern, Line);
			while (FlagM.FindNext())
			{
				const FString DeclaringClass = FlagM.GetCaptureGroup(1);
				const FString PropSym        = FlagM.GetCaptureGroup(2);
				const FString PropStr        = FlagM.GetCaptureGroup(3);
				const FString HexStr         = FlagM.GetCaptureGroup(4);
				if (DeclaringClass != CurrentClass) { continue; } // foreign
				// Symbol vs string-literal must agree (mirrors the Phase 3a
				// NewProp_*_Underlying defensive skip).
				if (!PropStr.Equals(PropSym, ESearchCase::CaseSensitive)) { continue; }

				const uint64 PropFlags = static_cast<uint64>(
					FCString::Strtoui64(*HexStr, nullptr, /*Base=*/16));
				if ((PropFlags & kCPF_Net) == 0) { continue; } // not replicated

				const FString Key = DeclaringClass + TEXT("|") + PropStr;
				bool bAlreadySeen = false;
				NetPropKeysSeen.Add(Key, &bAlreadySeen);
				if (bAlreadySeen) { continue; }
				FNetPropHarvest H;
				H.OwningClass = DeclaringClass;
				H.PropertyName = PropStr;
				H.bRepNotify = (PropFlags & kCPF_RepNotify) != 0;
				NetProps.Add(MoveTemp(H));
			}
		}

		// ------ Open a per-property MetaData block.
		if (!bInMetaBlock)
		{
			FRegexMatcher M(NewPropMetaDataHeader, Line);
			if (M.FindNext())
			{
				CurrentMetaProperty = M.GetCaptureGroup(1);
				bInMetaBlock = true;
				PendingRepKind.Empty();
				PendingRepNotifyFunc.Empty();
				continue;
			}
			// Not in a meta block and not opening one — nothing to do.
			continue;
		}

		// ------ Inside a per-property MetaData block.
		// Close on a `};` line (end of array body).
		if (Line.Contains(TEXT("};")))
		{
			// Emit if we captured a replication signal.
			if (!PendingRepKind.IsEmpty())
			{
				FNetworkRepPropertyRow Row;
				Row.OwningClass = CurrentClass;
				Row.PropertyName = CurrentMetaProperty;
				Row.CppModule = ModuleName;
				Row.RepKind = PendingRepKind;
				Row.RepNotifyFunc = PendingRepNotifyFunc;
				Row.SourcePath = SourceHeaderRel;
				EmittedReplicatedUsingKeys.Add(CurrentClass + TEXT("|") + CurrentMetaProperty);
				OutBatch.ReplicatedProperties.Add(MoveTemp(Row));
			}
			CurrentMetaProperty.Empty();
			bInMetaBlock = false;
			PendingRepKind.Empty();
			PendingRepNotifyFunc.Empty();
			continue;
		}

		// Scan for MetaData pair rows. Multiple pairs per line is rare but
		// possible (the artefact generator usually one-per-line). FindNext()
		// is a while-loop over the same matcher.
		FRegexMatcher PairM(MetaDataPairPattern, Line);
		while (PairM.FindNext())
		{
			const FString Key = PairM.GetCaptureGroup(1);
			const FString Val = PairM.GetCaptureGroup(2);
			if (Key.Equals(TEXT("ReplicatedUsing"), ESearchCase::IgnoreCase))
			{
				PendingRepKind = TEXT("ReplicatedUsing");
				PendingRepNotifyFunc = Val;
			}
		}
	}

	// ------ Bare-Replicated fallback emission. For every CPF_Net property that
	// did NOT fire a ReplicatedUsing row, emit rep_kind="Replicated" with an
	// empty rep_notify_func. This captures UPROPERTY(Replicated) and
	// DOREPLIFETIME-macro replication — neither emits a "ReplicatedUsing"
	// MetaData pair, so the legacy MetaData-only scan missed them entirely.
	for (const FNetPropHarvest& H : NetProps)
	{
		const FString Key = H.OwningClass + TEXT("|") + H.PropertyName;
		if (EmittedReplicatedUsingKeys.Contains(Key)) { continue; }
		FNetworkRepPropertyRow Row;
		Row.OwningClass = H.OwningClass;
		Row.PropertyName = H.PropertyName;
		Row.CppModule = ModuleName;
		Row.RepKind = TEXT("Replicated");
		Row.RepNotifyFunc.Empty();
		Row.SourcePath = SourceHeaderRel;
		OutBatch.ReplicatedProperties.Add(MoveTemp(Row));
	}
}

bool FNetworkRepIndexer::WriteBatch(FSQLiteDatabase& DB, const FNetworkArtefactBatch& Batch)
{
	if (Batch.ReplicatedProperties.Num() == 0) { return true; }

	DB.Execute(TEXT("BEGIN TRANSACTION;"));
	bool bAllOk = true;

	FSQLitePreparedStatement Ins;
	if (!Ins.Create(DB, TEXT(
		"INSERT OR REPLACE INTO reflect_replicated_properties "
		"(owning_class, property_name, cpp_module, rep_kind, rep_notify_func, source_path, source_line) "
		"VALUES (?, ?, ?, ?, ?, ?, ?);")))
	{
		bAllOk = false;
	}
	else
	{
		for (const FNetworkRepPropertyRow& Row : Batch.ReplicatedProperties)
		{
			Ins.Reset();
			Ins.ClearBindings();
			Ins.SetBindingValueByIndex(1, Row.OwningClass);
			Ins.SetBindingValueByIndex(2, Row.PropertyName);
			Ins.SetBindingValueByIndex(3, Row.CppModule);
			Ins.SetBindingValueByIndex(4, Row.RepKind);
			Ins.SetBindingValueByIndex(5, Row.RepNotifyFunc);
			Ins.SetBindingValueByIndex(6, Row.SourcePath);
			Ins.SetBindingValueByIndex(7, 0); // source_line — not derivable from UHT artefact
			if (!Ins.Execute()) { bAllOk = false; }
		}
	}

	DB.Execute(TEXT("COMMIT;"));
	return bAllOk;
}
