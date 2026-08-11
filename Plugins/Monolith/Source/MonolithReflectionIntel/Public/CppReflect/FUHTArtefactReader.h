// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// FUHTArtefactReader — sweeps the UnrealHeaderTool-generated companion files
// under `Intermediate/Build/<Platform>/<Target>/Inc/<Module>/UHT/` and extracts
// reflection edges into the Phase 3a tables.
//
// Why UHT artefacts instead of source?
//   Phase 3a deliberately stays away from a full C++ AST walk — that needs the
//   tree-sitter vendoring deferred to Phase 3b. UHT artefacts are the next-best
//   surface: deterministic, machine-generated, regex-friendly, and they ALREADY
//   know about every UCLASS / UPROPERTY / UFUNCTION / UINTERFACE the project
//   compiled. The orchestrator's UBT runs produce them as a side-effect.
//
// Format conventions exploited (verified against
//   Intermediate/Build/Win64/UnrealEditor/Inc/Leviathan/UHT/LeviathanCharacterBase.gen.cpp
//   ISXWeaponFireBridgeInterface.gen.cpp):
//
//   `// IWYU pragma: private, include "<path>"`     — source header for `<File>.generated.h`
//   `// ********** Begin Class <Name> *...*`        — UCLASS section open
//   `// ********** Begin Interface <Name> *...*`    — UINTERFACE section open
//   `<MODULE>_API UClass* Z_Construct_UClass_<C>_NoRegister();`  — cross-module ref
//   `Z_Construct_UClass_<P>` in DependentSingletons[]            — parent class
//   `static constexpr UE::CodeGen::FMetaDataPairParam Class_MetaDataParams[]` — class meta
//   `static constexpr UE::CodeGen::FMetaDataPairParam NewProp_<N>_MetaData[]` — property meta
//   `const UECodeGen_Private::F<T>PropertyParams ...::NewProp_<N> = { "<N>", ...`
//                                                   — property type + name canonical form
//   `static constexpr UE::CodeGen::FClassNativeFunction Funcs[] = {`
//                                                   — BP-VM-exposed function table
//   `const UECodeGen_Private::FImplementedInterfaceParams ...::InterfaceParams[] = {`
//                                                   — interface implementation edges
//   `{ Z_Construct_UClass_<I>_NoRegister, (int32)VTABLE_OFFSET(<C>, I<I_no_U>), ... }`
//
// All patterns regex-extractable from the `.gen.cpp` text. Idempotent — wipes
// + rewrites all six tables each Run().

#pragma once

#include "CoreMinimal.h"
#include "Containers/Array.h"
#include "Containers/Map.h"
#include "Containers/Set.h"
#include "Internationalization/Regex.h"

class FSQLiteDatabase;

/** One extracted UCLASS row, buffered between scan and write. */
struct FCppReflectUClassRow
{
	FString ClassName;
	FString ModuleName;
	FString ParentClass;
	FString SourcePath;     // project-relative forward-slashed
	int32   SourceLine = 0; // Phase 3a always 0 (UHT does not record source line)
	FString Flags;          // colon-delimited specifier list
	bool    bIsInterface = false; // routed into reflect_uinterfaces instead of (or in addition to) reflect_uclasses
};

struct FCppReflectUPropertyRow
{
	FString OwningClass;
	FString PropertyName;
	FString PropertyType;        // "Struct", "Bool", "Enum", "Object", "SoftObject", "Float", "Double", ...
	FString CppModule;
	FString BlueprintVisibility; // "BlueprintReadOnly", "EditAnywhere", ... or empty
	FString Specifiers;          // colon-delimited
	int32   SourceLine = 0;
};

struct FCppReflectUFunctionRow
{
	FString OwningClass;
	FString FunctionName;
	FString ReturnType;          // best-effort — empty when not derivable
	bool    bBlueprintCallable = false;
	FString CppModule;
	FString Specifiers;          // colon-delimited
	int32   SourceLine = 0;
};

struct FCppReflectUInterfaceImplRow
{
	FString ImplementingClass;
	FString InterfaceName;
	FString CppModule;
};

/** Aggregate of a single artefact's parse result. */
struct FCppReflectArtefactBatch
{
	TArray<FCppReflectUClassRow>          UClasses;
	TArray<FCppReflectUPropertyRow>       UProperties;
	TArray<FCppReflectUFunctionRow>       UFunctions;
	TArray<FCppReflectUInterfaceImplRow>  InterfaceImpls;
};

class MONOLITHREFLECTIONINTEL_API FUHTArtefactReader
{
public:
	FUHTArtefactReader();

	/**
	 * Walk `ArtefactRoots` (Intermediate/Build/<Platform>/<Target>/Inc/) for
	 * `*.gen.cpp` files, parse each, and write the six reflect_* tables.
	 *
	 * @param DB              Open writable handle. Caller has enforced
	 *                        `PRAGMA journal_mode=DELETE`.
	 * @param ArtefactRoots   Absolute or project-relative directories. Empty
	 *                        array → auto-resolve via
	 *                        FPaths::ProjectIntermediateDir() / "Build".
	 * @param bIncludeEnginePlugins When true, also sweeps engine plugin Inc/
	 *                        directories (under the same Build root they
	 *                        share with the project — UE 5.7's standard
	 *                        layout merges them).  Off by default.
	 * @param bAllowMarketplacePaths When true, the `/Engine/` skip filter makes
	 *                        a narrow exception for `/Plugins/Marketplace/`
	 *                        paths (engine-installed marketplace plugins live
	 *                        physically under /Engine/ but are NOT Epic
	 *                        built-ins). All OTHER /Engine/ paths stay blocked
	 *                        unless bIncludeEnginePlugins is set. Off by default.
	 * @param OutStatus       One-line summary printed to log + returned to MCP.
	 * @return true on schema success and at least one artefact scanned
	 *         (graceful degradation: zero artefacts = log warning + return
	 *         true with zero rows, since the project may not yet have built).
	 */
	bool Run(FSQLiteDatabase& DB,
		const TArray<FString>& ArtefactRoots,
		bool bIncludeEnginePlugins,
		bool bAllowMarketplacePaths,
		FString& OutStatus,
		/** Optional — receives the resolved absolute roots that DirectoryExists()
		 *  said yes to (the ones actually walked). Default nullptr preserves the
		 *  existing API. */
		TArray<FString>* OutScannedRoots = nullptr,
		/** Optional — receives the {AbsolutePath, Reason} pairs for any roots
		 *  that were SKIPPED (e.g. "directory does not exist"). Mirrors the
		 *  scanned-roots vector and is what `rebuild_reflection_index` surfaces
		 *  so a misconfigured root never silently vanishes. */
		TArray<TPair<FString, FString>>* OutSkippedRoots = nullptr);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);
	void WipeTables(FSQLiteDatabase& DB);

	/** Single-file scan. Reads the `.gen.cpp` into FileText, runs the regex
	 *  passes, fills OutBatch. */
	void ScanArtefact(const FString& AbsArtefactPath,
		const FString& ModuleName,
		FCppReflectArtefactBatch& OutBatch);

	bool WriteBatch(FSQLiteDatabase& DB, const FCppReflectArtefactBatch& Batch);

	/** Helper — resolve `<Build>/<Platform>/<Target>/Inc/<Module>/UHT/`
	 *  parents into a flat list of (ModuleName, AbsArtefactPath) pairs.
	 *  bAllowMarketplacePaths opens a narrow /Plugins/Marketplace/ exception to
	 *  the /Engine/ skip filter — see Run() docs. */
	void CollectArtefacts(const FString& RootAbs, bool bIncludeEnginePlugins,
		bool bAllowMarketplacePaths,
		TArray<TPair<FString, FString>>& OutModuleAndArtefactPairs);

	// Phase 2 code-quality non-negotiable item 4 — FRegexPattern hoisted to
	// member scope. Re-used per file; FRegexMatcher per-text-input is what
	// binds to a specific buffer.
	FRegexPattern IwyuIncludePattern;        // grabs "// IWYU pragma: private, include "<path>""
	FRegexPattern BeginClassPattern;         // "// ********** Begin Class <Name> ***..."
	FRegexPattern BeginInterfacePattern;     // "// ********** Begin Interface <Name> ***..."
	FRegexPattern DependentSingletonPattern; // "(UObject* (*)())Z_Construct_UClass_<P>"
	FRegexPattern ClassMetaDataParamsHeader; // start-of-Class_MetaDataParams array
	FRegexPattern MetaDataPairPattern;       // single `{ "Key", "Value" },` row
	FRegexPattern PropertyDeclPattern;       // F<T>PropertyParams ...::NewProp_<N> = { "<N>", ...
	FRegexPattern FuncInfoPattern;           // LEGACY FuncInfo[] entry "{ &Z_..._<Class>_<Func>, "<Func>" }"
	FRegexPattern FuncDesignatorPattern;     // MODERN Funcs[] entry "{ .NameUTF8 = UTF8TEXT("<F>"), .Pointer = &<C>::exec<F> }"
	FRegexPattern InterfaceParamPattern;     // FImplementedInterfaceParams row → Z_Construct_UClass_<I>_NoRegister
	FRegexPattern FuncParamsHeaderPattern;   // "Z_Construct_UFunction_<Class>_<Func>_Statics::FuncParams = { { ... "<Func>","
	FRegexPattern FunctionFlagsPattern;      // "(EFunctionFlags)0x<HEX>" — the registration-flag bitfield

	/**
	 * Decode an EFunctionFlags bitfield (parsed from a `(EFunctionFlags)0x...`
	 * token in a FuncParams definition) into a normalized net-specifier string,
	 * e.g. "Server,Reliable" / "Client" / "NetMulticast,Unreliable". Returns
	 * an empty string when the function carries no net flags (FUNC_Net unset),
	 * which the caller treats as "not an RPC". Bit values mirror
	 * Engine/Source/Runtime/CoreUObject/Public/UObject/Script.h (EFunctionFlags).
	 */
	static FString NetSpecifiersFromFunctionFlags(uint32 FunctionFlags);
};
