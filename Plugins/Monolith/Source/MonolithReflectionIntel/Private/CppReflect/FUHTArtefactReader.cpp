// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// FUHTArtefactReader — implementation. Idempotent regex sweep over `*.gen.cpp`
// artefacts; writes the six Phase 3a tables.
//
// Reading a UHT `.gen.cpp` is a structural-text exercise:
//
//  1. The TOP of the file declares cross-module references — including the
//     class's own `<MODULE>_API UClass* Z_Construct_UClass_<C>_NoRegister();`
//     line. This is the cheapest way to harvest (ClassName, ModuleName)
//     because the MODULE token is the API macro prefix in UPPER_SNAKE_CASE
//     and the class name is the C++ symbol verbatim.
//  2. The file is segmented by `// ********** Begin (Class|Interface) <Name>`
//     comment banners; each segment ends at a matching `End` banner.
//  3. Inside a Class segment, the `Z_Construct_UClass_<C>_Statics` struct
//     declares each property's metadata + type. The single line that pins
//     ALL signal at once is:
//        const UECodeGen_Private::F<T>PropertyParams ...::NewProp_<N> = { "<N>", ... }
//     — yielding (PropertyName, PropertyTypeTag).
//  4. The `static constexpr UE::CodeGen::FClassNativeFunction Funcs[]` block
//     enumerates BP-VM-exposed functions verbatim.
//  5. The `Z_Construct_UClass_<C>_Statics::InterfaceParams[] = { ... }` array
//     contains one row per implemented UINTERFACE.
//  6. Class metadata (BlueprintType / Abstract / etc.) lives in the first
//     `Class_MetaDataParams[]` array. We extract `ModuleRelativePath` to
//     reconstruct `source_path` and any specifier-like keys to populate
//     `flags`.
//  7. Property metadata (`Category`, `EditAnywhere`-shaped specifiers, etc.)
//     lives in the per-property `NewProp_<N>_MetaData[]` blocks just above
//     the Class_MetaDataParams.
//
// NONE of this needs a real C++ parser. The regex sweep is bounded by line-
// at-a-time scanning where possible; the property-meta blocks are scanned
// line-by-line within an outer state machine that tracks Class boundaries.

#include "CppReflect/FUHTArtefactReader.h"
#include "CppReflect/CppReflectSchema.h"
#include "MonolithReflectionIntelModule.h"
#include "MonolithRIMetaTable.h"

#include "HAL/FileManager.h"
#include "HAL/PlatformFileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "SQLiteDatabase.h"

namespace
{
	// A project-relative path resolver formerly lived here (anon-namespace copy of
	// the Phase 2 helper) but was never referenced in this TU. It collided under
	// unity with the identical copies in the other indexers; removed. If a future
	// edit needs it, include "Shared/RIPathUtils.h" and call RIToProjectRelative.

	/**
	 * Convert UPPER_SNAKE_CASE module-API tag (e.g. "LEVIATHAN", "INVENTORYSYSTEMX")
	 * into the Pascal/Camel module name. UE convention is that <MODULE>_API tag is
	 * the module name uppercased — and the original module name uses Pascal case.
	 *
	 * Phase 3a heuristic: scan the artefact's directory path for the module-name
	 * segment instead (`.../Inc/<Module>/UHT/<File>.gen.cpp`) — that gives the
	 * Pascal/Camel form deterministically. We only fall back to this de-uppering
	 * when the directory walk fails.
	 */
	FString GuessModuleNameFromApiTag(const FString& UpperApiTag)
	{
		if (UpperApiTag.IsEmpty()) { return FString(); }
		// `LEVIATHAN_API` → `Leviathan`. Trivial: lower-case all, then upper-case
		// first letter. UE does NOT preserve internal capitalisation in the API
		// tag (it just `_API` suffixes ToUpper(ModuleName)), so we cannot recover
		// camel-case boundaries.
		FString Lower = UpperApiTag.ToLower();
		if (Lower.Len() > 0) { Lower[0] = FChar::ToUpper(Lower[0]); }
		return Lower;
	}

	/** Walk up an absolute artefact path and return the `<Module>` segment that
	 *  appears between `/Inc/` and `/UHT/`. Returns FString() on failure. */
	FString UHTModuleNameFromArtefactDir(const FString& AbsArtefactPath)
	{
		FString Norm = AbsArtefactPath;
		Norm.ReplaceInline(TEXT("\\"), TEXT("/"));
		const int32 IncIdx = Norm.Find(TEXT("/Inc/"));
		const int32 UhtIdx = Norm.Find(TEXT("/UHT/"));
		if (IncIdx == INDEX_NONE || UhtIdx == INDEX_NONE || UhtIdx <= IncIdx + 5)
		{
			return FString();
		}
		// Module slice = between "/Inc/" and "/UHT/".
		const int32 StartIdx = IncIdx + 5; // skip "/Inc/"
		return Norm.Mid(StartIdx, UhtIdx - StartIdx);
	}
}

FUHTArtefactReader::FUHTArtefactReader()
	// Phase 2 code-quality item 4 — patterns built once per indexer instance.
	: IwyuIncludePattern(
		TEXT("//\\s*IWYU\\s+pragma:\\s*private,\\s*include\\s*\"([^\"]+)\""))
	, BeginClassPattern(
		TEXT("//\\s*\\*+\\s*Begin\\s+Class\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+\\*"))
	, BeginInterfacePattern(
		TEXT("//\\s*\\*+\\s*Begin\\s+Interface\\s+([A-Za-z_][A-Za-z0-9_]*)\\s+\\*"))
	, DependentSingletonPattern(
		TEXT("\\(UObject\\*\\s*\\(\\*\\)\\(\\)\\)Z_Construct_UClass_([A-Za-z_][A-Za-z0-9_]*)\\b"))
	, ClassMetaDataParamsHeader(
		TEXT("FMetaDataPairParam\\s+Class_MetaDataParams\\s*\\[\\s*\\]"))
	, MetaDataPairPattern(
		TEXT("\\{\\s*\"([^\"]+)\"\\s*,\\s*\"([^\"]*)\"\\s*\\}"))
	, PropertyDeclPattern(
		// Anchored at line-start; the canonical UHT layout is one declaration per line.
		// Capture (PropTypeTag, PropertyName) from
		//   const UECodeGen_Private::F<T>PropertyParams ...::NewProp_<X> = { "<X>", ...
		TEXT("UECodeGen_Private::F([A-Za-z]+)PropertyParams\\s+[^;]*::NewProp_([A-Za-z_][A-Za-z0-9_]*)\\s*=\\s*\\{\\s*\"([^\"]+)\""))
	, FuncInfoPattern(
		// LEGACY form (FuncInfo[] array):
		// `{ &Z_Construct_UFunction_<Class>_<Func>, "<Func>" }`
		TEXT("\\{\\s*&Z_Construct_UFunction_([A-Za-z_][A-Za-z0-9_]*)_([A-Za-z_][A-Za-z0-9_]*)\\s*,\\s*\"([A-Za-z_][A-Za-z0-9_]*)\"\\s*\\}"))
	, FuncDesignatorPattern(
		// MODERN form (Funcs[] / FClassNativeFunction designator-initializer):
		// `{ .NameUTF8 = UTF8TEXT("<Func>"), .Pointer = &<Class>::exec<Func> }`
		// Captures: 1=FuncName-from-string, 2=Class, 3=FuncName-from-exec-symbol.
		// Verified against UE 5.7 .gen.cpp output (CoreNative.h FNameNativePtrPair
		// + UE::CodeGen::FClassNativeFunction).
		TEXT("\\{\\s*\\.NameUTF8\\s*=\\s*UTF8TEXT\\(\\s*\"([A-Za-z_][A-Za-z0-9_]*)\"\\s*\\)\\s*,\\s*\\.Pointer\\s*=\\s*&([A-Za-z_][A-Za-z0-9_]*)::exec([A-Za-z_][A-Za-z0-9_]*)\\s*\\}"))
	, InterfaceParamPattern(
		// `{ Z_Construct_UClass_<I>_NoRegister, (int32)VTABLE_OFFSET(<C>, I<I_no_U>), false }`
		TEXT("\\{\\s*Z_Construct_UClass_([A-Za-z_][A-Za-z0-9_]*)_NoRegister\\s*,\\s*\\(int32\\)VTABLE_OFFSET\\(\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*,"))
	, FuncParamsHeaderPattern(
		// The definition line of a function's registration params, e.g.:
		//   const UECodeGen_Private::FFunctionParams
		//     Z_Construct_UFunction_<Class>_<Func>_Statics::FuncParams = {
		//       { (UObject*(*)())Z_Construct_UClass_<Class>, nullptr, "<Func>", ...
		// Capture: 1=Class, 2=Func-from-symbol, 3=Func-from-string-literal.
		// The `(EFunctionFlags)0x...` bitfield sits on a CONTINUATION line of the
		// SAME initializer (verified against UE 5.7 WeaponBase_ISX.gen.cpp), so a
		// bounded forward scan follows this match to recover the flags. Delegate
		// signatures use Z_Construct_UDelegateFunction_*, which this pattern does
		// NOT match — net specifiers only apply to UFUNCTION RPCs.
		TEXT("Z_Construct_UFunction_([A-Za-z_][A-Za-z0-9_]*)_([A-Za-z_][A-Za-z0-9_]*)_Statics::FuncParams\\s*=\\s*\\{\\s*\\{[^\"]*\"([A-Za-z_][A-Za-z0-9_]*)\""))
	, FunctionFlagsPattern(
		// The registration-flag bitfield token: `(EFunctionFlags)0x<HEX>`.
		TEXT("\\(EFunctionFlags\\)0x([0-9A-Fa-f]+)"))
{
}

// EFunctionFlags bit values — mirror of
// Engine/Source/Runtime/CoreUObject/Public/UObject/Script.h (EFunctionFlags).
// Verified via offline source index against UE 5.7. Net-relevant bits only.
namespace
{
	constexpr uint32 kFUNC_Net          = 0x00000040; // FUNC_Net — function is network-replicated
	constexpr uint32 kFUNC_NetReliable  = 0x00000080; // FUNC_NetReliable
	constexpr uint32 kFUNC_NetMulticast = 0x00004000; // FUNC_NetMulticast — Server -> All Clients
	constexpr uint32 kFUNC_NetServer    = 0x00200000; // FUNC_NetServer — executes on servers
	constexpr uint32 kFUNC_NetClient    = 0x01000000; // FUNC_NetClient — executes on clients
	constexpr uint32 kFUNC_NetValidate  = 0x80000000; // FUNC_NetValidate — supplies a _Validate impl
}

FString FUHTArtefactReader::NetSpecifiersFromFunctionFlags(uint32 FunctionFlags)
{
	// FUNC_Net gates the entire classification — a non-replicated function is
	// not an RPC and gets an empty specifier string.
	if ((FunctionFlags & kFUNC_Net) == 0)
	{
		return FString();
	}

	TArray<FString> Parts;

	// Endpoint specifier first (Server / Client / NetMulticast). A net function
	// always carries exactly one of these; if (defensively) none are set we still
	// surface the reliability so the row is not silently empty.
	if (FunctionFlags & kFUNC_NetServer)         { Parts.Add(TEXT("Server")); }
	else if (FunctionFlags & kFUNC_NetClient)    { Parts.Add(TEXT("Client")); }
	else if (FunctionFlags & kFUNC_NetMulticast) { Parts.Add(TEXT("NetMulticast")); }

	// Reliability: FUNC_NetReliable present → Reliable, absent → Unreliable.
	Parts.Add((FunctionFlags & kFUNC_NetReliable) ? TEXT("Reliable") : TEXT("Unreliable"));

	// WithValidation is an orthogonal modifier on Server RPCs.
	if (FunctionFlags & kFUNC_NetValidate) { Parts.Add(TEXT("WithValidation")); }

	return FString::Join(Parts, TEXT(","));
}

bool FUHTArtefactReader::Run(FSQLiteDatabase& DB,
	const TArray<FString>& ArtefactRoots,
	bool bIncludeEnginePlugins,
	bool bAllowMarketplacePaths,
	FString& OutStatus,
	TArray<FString>* OutScannedRoots,
	TArray<TPair<FString, FString>>* OutSkippedRoots)
{
	ensure(IsInGameThread());

	// EnsureMetaTable up front — keeps the stale-detection table alongside the
	// reflect_* tables under the same lock window. Non-fatal on failure (the
	// rest of the run can still produce useful data); logged inside.
	MonolithRIMeta::EnsureMetaTable(DB);

	if (!EnsureSchema(DB))
	{
		OutStatus = TEXT("FUHTArtefactReader: schema bootstrap failed");
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
		// Default: scan the entire `Intermediate/Build/` tree. The collector
		// then filters down to `/Inc/<Module>/UHT/` triples.
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

	// Collect all `(ModuleName, AbsArtefactPath)` pairs from every root.
	// Handover doc item #2: track scanned vs skipped roots and surface them up
	// (callers wire them into rebuild_reflection_index response). Bump the
	// missing-root log from Verbose to Warning so silent skips stop costing
	// debug cycles (the marketplace-scan rebase bug took 2 cycles purely
	// because this log was Verbose).
	TArray<TPair<FString, FString>> ModuleAndArtefactPairs;
	for (const FString& Root : ResolvedRoots)
	{
		IPlatformFile& Pf = FPlatformFileManager::Get().GetPlatformFile();
		if (!Pf.DirectoryExists(*Root))
		{
			UE_LOG(LogMonolithReflectionIntel, Warning,
				TEXT("FUHTArtefactReader: skipping missing root '%s'"), *Root);
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

	// Graceful degradation: zero artefacts on disk → log warning + 0 rows.
	if (ModuleAndArtefactPairs.Num() == 0)
	{
		OutStatus = TEXT(
			"FUHTArtefactReader: no UHT artefacts found — has the project built "
			"with UBT yet? (Live Coding patches do not produce gen.cpp).");
		UE_LOG(LogMonolithReflectionIntel, Warning, TEXT("%s"), *OutStatus);
		// Stamp the code-version even on zero-artefact success — schema is in
		// place and the row shape matches; rebuild on next code-bump still works.
		MonolithRIMeta::WriteStoredVersion(DB, TEXT("cppreflect"),
			MonolithRIMeta::GetIndexerCodeVersion(TEXT("cppreflect")));
		return true; // schema bootstrap counts as success
	}

	int32 TotalUClasses = 0, TotalUProps = 0, TotalUFuncs = 0, TotalUImpls = 0;
	int32 FilesScanned = 0;

	for (const TPair<FString, FString>& Pair : ModuleAndArtefactPairs)
	{
		FCppReflectArtefactBatch Batch;
		ScanArtefact(/*AbsArtefactPath=*/Pair.Value,
		             /*ModuleName=*/Pair.Key,
		             /*OutBatch=*/Batch);

		// project-relative path normalisation pass — UHT artefacts carry
		// `ModuleRelativePath` ("Public/Foo/Bar.h"); we want the project-
		// relative form ("Source/Leviathan/Public/Foo/Bar.h" or similar).
		// We cannot derive the module-Source prefix from the artefact alone —
		// leave the value as ModuleRelativePath for Phase 3a and let the
		// query handlers normalise on the way out. Down-stream auditors can
		// still match because the in-tree path uniquely identifies the file.

		if (!WriteBatch(DB, Batch))
		{
			UE_LOG(LogMonolithReflectionIntel, Warning,
				TEXT("FUHTArtefactReader: write failed for %s"), *Pair.Value);
			// Continue — other batches can still land. Indexer is best-effort.
		}

		TotalUClasses += Batch.UClasses.Num();
		TotalUProps   += Batch.UProperties.Num();
		TotalUFuncs   += Batch.UFunctions.Num();
		TotalUImpls   += Batch.InterfaceImpls.Num();
		++FilesScanned;
	}

	OutStatus = FString::Printf(
		TEXT("FUHTArtefactReader: %d artefacts scanned → UClasses=%d UProps=%d UFuncs=%d UInterfaceImpls=%d"),
		FilesScanned, TotalUClasses, TotalUProps, TotalUFuncs, TotalUImpls);
	UE_LOG(LogMonolithReflectionIntel, Log, TEXT("%s"), *OutStatus);

	// Handover doc item #1 — stamp the cppreflect code-version on success so the
	// adapter's lazy-bootstrap version-mismatch check can detect a stale schema
	// next call (and force a rebuild).
	MonolithRIMeta::WriteStoredVersion(DB, TEXT("cppreflect"),
		MonolithRIMeta::GetIndexerCodeVersion(TEXT("cppreflect")));
	return true;
}

bool FUHTArtefactReader::EnsureSchema(FSQLiteDatabase& DB)
{
	auto Exec = [&DB](const TCHAR* Sql) -> bool
	{
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, Sql))
		{
			UE_LOG(LogMonolithReflectionIntel, Error,
				TEXT("FUHTArtefactReader DDL prepare failed: %s"), Sql);
			return false;
		}
		return Stmt.Execute();
	};

	using namespace MonolithCppReflectSchema;
	if (!Exec(GetCreateUClassesTableSQL()))         { return false; }
	if (!Exec(GetCreateUPropertiesTableSQL()))      { return false; }
	if (!Exec(GetCreateUFunctionsTableSQL()))       { return false; }
	if (!Exec(GetCreateUInterfacesTableSQL()))      { return false; }
	if (!Exec(GetCreateUInterfaceImplsTableSQL())) { return false; }
	if (!Exec(GetCreateCppAssetEdgesTableSQL()))    { return false; }

	// Indices are non-fatal — log on failure but continue.
	Exec(GetCreateUPropertiesIndexOwningClassSQL());
	Exec(GetCreateUFunctionsIndexOwningClassSQL());
	Exec(GetCreateUFunctionsIndexBlueprintCallableSQL());
	Exec(GetCreateCppAssetEdgesIndexClassSQL());
	Exec(GetCreateCppAssetEdgesIndexKindSQL());
	return true;
}

void FUHTArtefactReader::WipeTables(FSQLiteDatabase& DB)
{
	auto Wipe = [&DB](const TCHAR* Sql)
	{
		FSQLitePreparedStatement Stmt;
		Stmt.Create(DB, Sql);
		Stmt.Execute();
	};
	// Note: cpp_asset_edges is wiped by FAssetGraphJoiner — keep this method
	// focused on tables WE own. The joiner runs in the same transaction so
	// asset edges either fully replace or fully don't.
	Wipe(TEXT("DELETE FROM reflect_uclasses;"));
	Wipe(TEXT("DELETE FROM reflect_uproperties;"));
	Wipe(TEXT("DELETE FROM reflect_ufunctions;"));
	Wipe(TEXT("DELETE FROM reflect_uinterfaces;"));
	Wipe(TEXT("DELETE FROM reflect_uinterface_impls;"));
}

void FUHTArtefactReader::CollectArtefacts(
	const FString& RootAbs, bool bIncludeEnginePlugins,
	bool bAllowMarketplacePaths,
	TArray<TPair<FString, FString>>& OutModuleAndArtefactPairs)
{
	// Visitor finds every `<Anywhere>/Inc/<Module>/UHT/<Anything>.gen.cpp`.
	// We do not actually need the directory shape — we just inspect each
	// file path and accept those that contain "/UHT/" and end in ".gen.cpp".
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
			// Engine-plugin filter: skip files whose path contains "/Engine/"
			// unless the operator opted in. Narrow exception: when
			// bAllowMarketplace is set we permit "/Plugins/Marketplace/" paths
			// (engine-installed marketplace plugins live under /Engine/ but are
			// NOT Epic built-ins). All OTHER /Engine/ paths stay blocked.
			if (!bIncludeEngine && Norm.Find(TEXT("/Engine/")) != INDEX_NONE
				&& !(bAllowMarketplace && Norm.Contains(TEXT("/Plugins/Marketplace/"))))
			{
				return true;
			}
			const FString Module = UHTModuleNameFromArtefactDir(Norm);
			if (Module.IsEmpty()) { return true; }
			Out.Emplace(Module, Norm);
			return true;
		}
	};
	FCppGenVisitor Visitor(OutModuleAndArtefactPairs, bIncludeEnginePlugins, bAllowMarketplacePaths);
	IFileManager::Get().IterateDirectoryRecursively(*RootAbs, Visitor);
}

void FUHTArtefactReader::ScanArtefact(
	const FString& AbsArtefactPath,
	const FString& ModuleName,
	FCppReflectArtefactBatch& OutBatch)
{
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *AbsArtefactPath)) { return; }

	// Hoist the file into one string + a line array for state-machine scans.
	TArray<FString> Lines;
	Text.ParseIntoArrayLines(Lines, /*InCullEmpty=*/false);

	// -----------------------------------------------------------------
	// Pass 1 — line-state walk. Track current Class/Interface banner and
	// capture properties, functions, interface-implementation rows inside.
	//
	// We intentionally skip a "Cross Module References" pre-pass: the
	// `Begin Class <Name>` banner is the authoritative declaration of
	// which classes this artefact owns. The cross-module ref lines are
	// just declarations of singleton accessors for ALL referenced UCLASSes
	// (including foreign ones in dependent modules) and would over-
	// emit if used as the ownership filter.
	// -----------------------------------------------------------------
	FString CurrentClass;
	bool    bInInterface = false;
	bool    bClassWasInterface = false; // sticky per class — remembers whether the open banner said "Interface"
	FString SourceHeaderRel; // from IWYU pragma line, file-level

	// Dedupe set — UE 5.7 emits BOTH the legacy FuncInfo[] AND the modern
	// designator-style Funcs[] arrays in the same file (verified against
	// LeviathanAnimMathLib.gen.cpp: 10 modern + 10 legacy = same 10
	// functions). Either form alone is sufficient to enumerate the class's
	// BP-VM-exposed functions, but to be robust against UE versions that drop
	// the legacy form, both matchers run and dedupe on (OwningClass|FuncName).
	TSet<FString> SeenFunctionKeys;

	// IWYU pragma scan (anywhere in file) — extract source header path.
	{
		FRegexMatcher M(IwyuIncludePattern, Text);
		if (M.FindNext())
		{
			SourceHeaderRel = M.GetCaptureGroup(1);
		}
	}

	// -----------------------------------------------------------------
	// Pre-pass — net-specifier harvest. Each UFUNCTION's registration
	// `...FuncParams = { { ... "<Func>", ...` carries an `(EFunctionFlags)0x...`
	// bitfield on a CONTINUATION line of the same initializer. We map
	// (OwningClass|FuncName) → normalized net-specifier string so Pass 1 can
	// stamp it onto the matching reflect_ufunctions row regardless of whether
	// the function was enumerated from the legacy FuncInfo[] or modern Funcs[]
	// array. The bitfield is the AUTHORITATIVE net signal — UFUNCTION(Server,
	// Reliable) compiles to FUNC_Net|FUNC_NetReliable|FUNC_NetServer, never to a
	// name prefix. Non-net functions produce an empty string and are skipped.
	// -----------------------------------------------------------------
	TMap<FString, FString> FunctionNetSpecifiers; // key "Class|Func" → "Server,Reliable"
	{
		// The flags token may be a few lines past the header (params struct +
		// size lines sit between). A small bounded window is ample — verified
		// layout is header line + up to ~4 continuation lines before the flags.
		constexpr int32 kFlagsScanWindow = 8;
		for (int32 LineIdx = 0; LineIdx < Lines.Num(); ++LineIdx)
		{
			FRegexMatcher HeaderM(FuncParamsHeaderPattern, Lines[LineIdx]);
			if (!HeaderM.FindNext()) { continue; }

			const FString DeclaringClass = HeaderM.GetCaptureGroup(1);
			const FString FuncSym        = HeaderM.GetCaptureGroup(2);
			const FString FuncStr        = HeaderM.GetCaptureGroup(3);
			// The string literal and the symbol token must agree; a mismatch is
			// exceptional and skipped defensively (mirrors the Funcs[] policy).
			if (!FuncStr.Equals(FuncSym, ESearchCase::CaseSensitive)) { continue; }

			// Scan this line and a bounded window of following lines for the
			// `(EFunctionFlags)0x...` token belonging to this initializer.
			const int32 ScanEnd = FMath::Min(LineIdx + kFlagsScanWindow, Lines.Num());
			for (int32 FlagLine = LineIdx; FlagLine < ScanEnd; ++FlagLine)
			{
				FRegexMatcher FlagM(FunctionFlagsPattern, Lines[FlagLine]);
				if (!FlagM.FindNext()) { continue; }

				const FString HexStr = FlagM.GetCaptureGroup(1);
				const uint32 Flags = static_cast<uint32>(
					FCString::Strtoui64(*HexStr, nullptr, /*Base=*/16));
				const FString Specifiers = NetSpecifiersFromFunctionFlags(Flags);
				if (!Specifiers.IsEmpty())
				{
					FunctionNetSpecifiers.Add(
						DeclaringClass + TEXT("|") + FuncStr, Specifiers);
				}
				break; // first flags token after the header is the right one
			}
		}
	}

	for (int32 LineIdx = 0; LineIdx < Lines.Num(); ++LineIdx)
	{
		const FString& Line = Lines[LineIdx];

		// Begin Class banner — open a Class segment.
		{
			FRegexMatcher M(BeginClassPattern, Line);
			if (M.FindNext())
			{
				CurrentClass = M.GetCaptureGroup(1);
				bInInterface = false;
				bClassWasInterface = false;
				continue;
			}
		}
		// Begin Interface banner — open an Interface segment.
		{
			FRegexMatcher M(BeginInterfacePattern, Line);
			if (M.FindNext())
			{
				CurrentClass = M.GetCaptureGroup(1);
				bInInterface = true;
				bClassWasInterface = true;
				continue;
			}
		}

		if (CurrentClass.IsEmpty()) { continue; }

		// ------ Class-level metadata: `Z_Construct_UClass_<C>_Statics::ClassParams`
		// `DependentSingletons[]` carries the parent class as its FIRST
		// `(UObject* (*)())Z_Construct_UClass_<P>` entry. We capture the FIRST
		// such pattern after the class-Statics struct opens and BEFORE any
		// following Class banner. To keep the regex cheap, we just remember
		// the first match seen during this class's segment.
		// (We collect ALL matches and pick the first inside the segment via a
		// per-class flag.)

		// ------ Function table — LEGACY form
		// `{ &Z_Construct_UFunction_<Class>_<Func>, "<Func>" }` (FuncInfo[]).
		{
			FRegexMatcher M(FuncInfoPattern, Line);
			while (M.FindNext())
			{
				const FString DeclaringClass = M.GetCaptureGroup(1);
				const FString FuncSym        = M.GetCaptureGroup(2);
				const FString FuncStr        = M.GetCaptureGroup(3);
				if (DeclaringClass != CurrentClass) { continue; } // foreign
				if (!FuncStr.Equals(FuncSym, ESearchCase::CaseSensitive))
				{
					// UHT mismatches between the symbol name and the string
					// literal would be exceptional — skip defensively.
					continue;
				}
				const FString Key = CurrentClass + TEXT("|") + FuncStr;
				bool bAlreadySeen = false;
				SeenFunctionKeys.Add(Key, &bAlreadySeen);
				if (bAlreadySeen) { continue; }
				FCppReflectUFunctionRow Row;
				Row.OwningClass = CurrentClass;
				Row.FunctionName = FuncStr;
				Row.ReturnType.Empty(); // Phase 3a does not parse the parms struct
				Row.bBlueprintCallable = true; // presence in Funcs[] implies BP-VM exposure
				Row.CppModule = ModuleName;
				// Net-specifier stamp (network workstream): empty for non-RPC.
				if (const FString* Spec = FunctionNetSpecifiers.Find(Key))
				{
					Row.Specifiers = *Spec;
				}
				OutBatch.UFunctions.Add(MoveTemp(Row));
			}
		}

		// ------ Function table — MODERN form
		// `{ .NameUTF8 = UTF8TEXT("<Func>"), .Pointer = &<Class>::exec<Func> }`
		// (UE::CodeGen::FClassNativeFunction designator-initializer Funcs[]).
		// Some future UE version may drop the legacy form — running both
		// matchers + deduping via SeenFunctionKeys is robust either way.
		{
			FRegexMatcher M(FuncDesignatorPattern, Line);
			while (M.FindNext())
			{
				const FString FuncStr        = M.GetCaptureGroup(1); // from UTF8TEXT
				const FString DeclaringClass = M.GetCaptureGroup(2); // before "::exec"
				const FString FuncSym        = M.GetCaptureGroup(3); // after "::exec"
				if (DeclaringClass != CurrentClass) { continue; } // foreign
				if (!FuncStr.Equals(FuncSym, ESearchCase::CaseSensitive))
				{
					// Mismatch between string literal and exec<F> symbol — skip
					// defensively to mirror the legacy-form policy.
					continue;
				}
				const FString Key = CurrentClass + TEXT("|") + FuncStr;
				bool bAlreadySeen = false;
				SeenFunctionKeys.Add(Key, &bAlreadySeen);
				if (bAlreadySeen) { continue; }
				FCppReflectUFunctionRow Row;
				Row.OwningClass = CurrentClass;
				Row.FunctionName = FuncStr;
				Row.ReturnType.Empty();
				Row.bBlueprintCallable = true;
				Row.CppModule = ModuleName;
				// Net-specifier stamp (network workstream): empty for non-RPC.
				if (const FString* Spec = FunctionNetSpecifiers.Find(Key))
				{
					Row.Specifiers = *Spec;
				}
				OutBatch.UFunctions.Add(MoveTemp(Row));
			}
		}

		// ------ Property declarations — F<T>PropertyParams ...::NewProp_<X> = { "<X>", ...
		{
			FRegexMatcher M(PropertyDeclPattern, Line);
			while (M.FindNext())
			{
				const FString TypeTag = M.GetCaptureGroup(1);
				const FString PropSym = M.GetCaptureGroup(2);
				const FString PropStr = M.GetCaptureGroup(3);
				if (!PropStr.Equals(PropSym, ESearchCase::CaseSensitive))
				{
					// `NewProp_Foo_Underlying` is a synthetic for enum-underlying
					// properties whose string literal is "UnderlyingType". Skip
					// when symbol-vs-string disagree to avoid double-counting.
					continue;
				}
				FCppReflectUPropertyRow Row;
				Row.OwningClass = CurrentClass;
				Row.PropertyName = PropStr;
				Row.PropertyType = TypeTag;     // e.g. "Struct", "Bool", "Float", "Object"
				Row.CppModule = ModuleName;
				// `blueprint_visibility` + `specifiers` parse is a Phase 3b refinement.
				// In Phase 3a, ScanArtefact leaves them empty — the action
				// surface tolerates NULL on these columns.
				OutBatch.UProperties.Add(MoveTemp(Row));
			}
		}

		// ------ Interface impls — FImplementedInterfaceParams row.
		{
			FRegexMatcher M(InterfaceParamPattern, Line);
			while (M.FindNext())
			{
				const FString IName = M.GetCaptureGroup(1); // "UISXWeaponFireBridgeInterface"
				const FString CName = M.GetCaptureGroup(2); // ULeviathanISXWeaponFireBridgeComponent
				// `IName` is the U-prefixed interface name; pure-C++ side is
				// "I<IName-without-U>". Store the U-prefixed form to match
				// reflect_uinterfaces.interface_name PK.
				if (CName != CurrentClass) { continue; } // foreign
				FCppReflectUInterfaceImplRow Row;
				Row.ImplementingClass = CurrentClass;
				Row.InterfaceName = IName;
				Row.CppModule = ModuleName;
				OutBatch.InterfaceImpls.Add(MoveTemp(Row));
			}
		}
	}

	// -----------------------------------------------------------------
	// Fallback emission — a net RPC that carries no exec-thunk (and so never
	// appears in Funcs[]/FuncInfo[]) would otherwise have no reflect_ufunctions
	// row at all, losing its specifiers. In practice every UFUNCTION RPC gets an
	// exec thunk (verified: WeaponBase_ISX::Reload appears in Funcs[]), so this
	// pass is a no-op for current artefacts — but it guarantees the specifier
	// signal is never silently dropped for an unusual codegen shape. Keys not
	// already in SeenFunctionKeys get a row with bBlueprintCallable=false (no
	// BP-VM exposure observed). The "Class|Func" key encodes the owning class.
	for (const TPair<FString, FString>& Pair : FunctionNetSpecifiers)
	{
		if (SeenFunctionKeys.Contains(Pair.Key)) { continue; }
		int32 SepIdx = INDEX_NONE;
		if (!Pair.Key.FindChar(TEXT('|'), SepIdx) || SepIdx <= 0) { continue; }
		FCppReflectUFunctionRow Row;
		Row.OwningClass = Pair.Key.Left(SepIdx);
		Row.FunctionName = Pair.Key.Mid(SepIdx + 1);
		Row.ReturnType.Empty();
		Row.bBlueprintCallable = false; // not in Funcs[]/FuncInfo[] → no BP-VM exposure
		Row.CppModule = ModuleName;
		Row.Specifiers = Pair.Value;
		SeenFunctionKeys.Add(Pair.Key);
		OutBatch.UFunctions.Add(MoveTemp(Row));
	}

	// -----------------------------------------------------------------
	// Pass 2 — emit one UClass row per banner-confirmed class. We walk
	// the line set once more to find each Begin <Class|Interface> banner
	// and look ahead for the immediately-following DependentSingletons
	// content block to harvest the parent. Cheaper than a multi-state
	// walk because the segment-internal data has already been captured.
	// -----------------------------------------------------------------
	{
		struct FBanner
		{
			FString Name;
			bool bIsInterface = false;
			int32 StartLine = 0;
			int32 EndLine = INT32_MAX; // approximate; clamps to next banner
		};
		TArray<FBanner> Banners;
		for (int32 LineIdx = 0; LineIdx < Lines.Num(); ++LineIdx)
		{
			FRegexMatcher M1(BeginClassPattern, Lines[LineIdx]);
			if (M1.FindNext())
			{
				FBanner B; B.Name = M1.GetCaptureGroup(1); B.bIsInterface = false; B.StartLine = LineIdx;
				Banners.Add(MoveTemp(B));
				continue;
			}
			FRegexMatcher M2(BeginInterfacePattern, Lines[LineIdx]);
			if (M2.FindNext())
			{
				FBanner B; B.Name = M2.GetCaptureGroup(1); B.bIsInterface = true; B.StartLine = LineIdx;
				Banners.Add(MoveTemp(B));
				continue;
			}
		}
		// Compute end-line as the start of the next banner (or EOF).
		for (int32 i = 0; i + 1 < Banners.Num(); ++i)
		{
			Banners[i].EndLine = Banners[i + 1].StartLine;
		}
		if (Banners.Num() > 0)
		{
			Banners.Last().EndLine = Lines.Num();
		}

		// One pass to dedupe Class+Function banners (the same class can have
		// many `Begin Class <X> Function <Y>` banners for each UFUNCTION; we
		// only want the bare-`Begin Class <X>` segment which is the class
		// definition proper).  Heuristic: drop banners whose `EndLine -
		// StartLine` is small (< 8 lines) AND whose name has already appeared
		// in Banners — those are function sub-banners.
		// In practice this is a no-op because BeginClassPattern matches the
		// trailing `*****` count too loosely; the Function-suffixed banners
		// have extra text after the class name. We refine the regex above to
		// require `BeginClassPattern` to end with `\\*` rather than `\\*+`
		// after the class name — that excludes the Function-sub-banners
		// because they have ` Function <Y>` before the trailing stars.
		// REFINED: the regex includes `\\s+\\*` so banners with extra tokens
		// between the name and the stars are excluded.

		for (const FBanner& B : Banners)
		{
			FCppReflectUClassRow Row;
			Row.ClassName = B.Name;
			Row.ModuleName = ModuleName;
			Row.SourcePath = SourceHeaderRel; // ModuleRelativePath form
			Row.SourceLine = 0;               // UHT does not record source line
			Row.bIsInterface = B.bIsInterface;

			// Harvest parent class from the first DependentSingletons match
			// inside the segment.
			for (int32 LineIdx = B.StartLine; LineIdx < B.EndLine && LineIdx < Lines.Num(); ++LineIdx)
			{
				FRegexMatcher M(DependentSingletonPattern, Lines[LineIdx]);
				if (M.FindNext())
				{
					Row.ParentClass = M.GetCaptureGroup(1);
					break;
				}
			}

			// Harvest class-level metadata from the segment's
			// Class_MetaDataParams[] block. We look for the start of that
			// block and then collect MetaDataPair rows until the next `};`.
			// Specifiers we surface as `flags`:
			//   BlueprintType, Abstract, MinimalAPI, NotBlueprintable,
			//   Blueprintable, NotPlaceable, Placeable, HideCategories,
			//   IsBlueprintBase
			bool bInMetaBlock = false;
			TArray<FString> FlagBuf;
			for (int32 LineIdx = B.StartLine; LineIdx < B.EndLine && LineIdx < Lines.Num(); ++LineIdx)
			{
				const FString& Line = Lines[LineIdx];
				if (!bInMetaBlock)
				{
					FRegexMatcher M(ClassMetaDataParamsHeader, Line);
					if (M.FindNext()) { bInMetaBlock = true; }
					continue;
				}
				if (Line.Contains(TEXT("};"))) { break; }
				FRegexMatcher M(MetaDataPairPattern, Line);
				while (M.FindNext())
				{
					const FString Key = M.GetCaptureGroup(1);
					// Drop sticky non-specifier keys.
					if (Key.Equals(TEXT("ModuleRelativePath"), ESearchCase::IgnoreCase)) { continue; }
					if (Key.Equals(TEXT("IncludePath"), ESearchCase::IgnoreCase))        { continue; }
					if (Key.Equals(TEXT("Comment"), ESearchCase::IgnoreCase))            { continue; }
					if (Key.Equals(TEXT("ToolTip"), ESearchCase::IgnoreCase))            { continue; }
					if (Key.Equals(TEXT("Category"), ESearchCase::IgnoreCase))           { continue; }
					FlagBuf.Add(Key);
				}
			}
			Row.Flags = FString::Join(FlagBuf, TEXT(":"));

			OutBatch.UClasses.Add(MoveTemp(Row));
		}
	}
}

bool FUHTArtefactReader::WriteBatch(FSQLiteDatabase& DB, const FCppReflectArtefactBatch& Batch)
{
	// Single transaction per artefact — cheap (the batch is small per file).
	DB.Execute(TEXT("BEGIN TRANSACTION;"));
	bool bAllOk = true;

	// --- UClasses + UInterfaces (split by bIsInterface) ---
	FSQLitePreparedStatement InsUClass;
	FSQLitePreparedStatement InsUIface;
	const bool bUClassOk = InsUClass.Create(DB, TEXT(
		"INSERT OR REPLACE INTO reflect_uclasses "
		"(class_name, module_name, parent_class, source_path, source_line, flags) "
		"VALUES (?, ?, ?, ?, ?, ?);"));
	const bool bUIfaceOk = InsUIface.Create(DB, TEXT(
		"INSERT OR REPLACE INTO reflect_uinterfaces "
		"(interface_name, module_name, source_path, source_line) "
		"VALUES (?, ?, ?, ?);"));

	if (bUClassOk && bUIfaceOk)
	{
		for (const FCppReflectUClassRow& Row : Batch.UClasses)
		{
			if (Row.bIsInterface)
			{
				InsUIface.Reset();
				InsUIface.ClearBindings();
				InsUIface.SetBindingValueByIndex(1, Row.ClassName);
				InsUIface.SetBindingValueByIndex(2, Row.ModuleName);
				InsUIface.SetBindingValueByIndex(3, Row.SourcePath);
				InsUIface.SetBindingValueByIndex(4, Row.SourceLine);
				if (!InsUIface.Execute()) { bAllOk = false; }
			}
			// ALWAYS emit a reflect_uclasses row too — even for interfaces
			// the U-prefixed companion class is a real UClass and other
			// queries (e.g. find_class_specifier on UINTERFACE) need it.
			InsUClass.Reset();
			InsUClass.ClearBindings();
			InsUClass.SetBindingValueByIndex(1, Row.ClassName);
			InsUClass.SetBindingValueByIndex(2, Row.ModuleName);
			InsUClass.SetBindingValueByIndex(3, Row.ParentClass);
			InsUClass.SetBindingValueByIndex(4, Row.SourcePath);
			InsUClass.SetBindingValueByIndex(5, Row.SourceLine);
			InsUClass.SetBindingValueByIndex(6, Row.Flags);
			if (!InsUClass.Execute()) { bAllOk = false; }
		}
	}
	else
	{
		bAllOk = false;
	}

	// --- UProperties ---
	{
		FSQLitePreparedStatement Ins;
		if (!Ins.Create(DB, TEXT(
			"INSERT OR REPLACE INTO reflect_uproperties "
			"(owning_class, property_name, property_type, cpp_module, blueprint_visibility, specifiers, source_line) "
			"VALUES (?, ?, ?, ?, ?, ?, ?);")))
		{
			bAllOk = false;
		}
		else
		{
			for (const FCppReflectUPropertyRow& Row : Batch.UProperties)
			{
				Ins.Reset();
				Ins.ClearBindings();
				Ins.SetBindingValueByIndex(1, Row.OwningClass);
				Ins.SetBindingValueByIndex(2, Row.PropertyName);
				Ins.SetBindingValueByIndex(3, Row.PropertyType);
				Ins.SetBindingValueByIndex(4, Row.CppModule);
				Ins.SetBindingValueByIndex(5, Row.BlueprintVisibility);
				Ins.SetBindingValueByIndex(6, Row.Specifiers);
				Ins.SetBindingValueByIndex(7, Row.SourceLine);
				if (!Ins.Execute()) { bAllOk = false; }
			}
		}
	}

	// --- UFunctions ---
	{
		FSQLitePreparedStatement Ins;
		if (!Ins.Create(DB, TEXT(
			"INSERT OR REPLACE INTO reflect_ufunctions "
			"(owning_class, function_name, return_type, blueprint_callable, cpp_module, specifiers, source_line) "
			"VALUES (?, ?, ?, ?, ?, ?, ?);")))
		{
			bAllOk = false;
		}
		else
		{
			for (const FCppReflectUFunctionRow& Row : Batch.UFunctions)
			{
				Ins.Reset();
				Ins.ClearBindings();
				Ins.SetBindingValueByIndex(1, Row.OwningClass);
				Ins.SetBindingValueByIndex(2, Row.FunctionName);
				Ins.SetBindingValueByIndex(3, Row.ReturnType);
				Ins.SetBindingValueByIndex(4, Row.bBlueprintCallable ? 1 : 0);
				Ins.SetBindingValueByIndex(5, Row.CppModule);
				Ins.SetBindingValueByIndex(6, Row.Specifiers);
				Ins.SetBindingValueByIndex(7, Row.SourceLine);
				if (!Ins.Execute()) { bAllOk = false; }
			}
		}
	}

	// --- UInterface impls ---
	{
		FSQLitePreparedStatement Ins;
		if (!Ins.Create(DB, TEXT(
			"INSERT OR REPLACE INTO reflect_uinterface_impls "
			"(implementing_class, interface_name, cpp_module) "
			"VALUES (?, ?, ?);")))
		{
			bAllOk = false;
		}
		else
		{
			for (const FCppReflectUInterfaceImplRow& Row : Batch.InterfaceImpls)
			{
				Ins.Reset();
				Ins.ClearBindings();
				Ins.SetBindingValueByIndex(1, Row.ImplementingClass);
				Ins.SetBindingValueByIndex(2, Row.InterfaceName);
				Ins.SetBindingValueByIndex(3, Row.CppModule);
				if (!Ins.Execute()) { bAllOk = false; }
			}
		}
	}

	DB.Execute(TEXT("COMMIT;"));
	return bAllOk;
}
