// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 3a — v0.17.0).
//
// FCppReflectQueryAdapter — implementation. Six read-only handlers over the
// Phase 3a reflect_* + cpp_asset_edges tables. All run on the game thread.
// Cursor codec mirrored from the Phase 1 / Phase 2 adapters — consolidation
// into MonolithCore is a Phase 5+ item and out of scope.

#include "CppReflect/FCppReflectQueryAdapter.h"
#include "MonolithReflectionIntelModule.h"
#include "MonolithRIMetaTable.h"
#include "Shared/RICursorCodec.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Misc/Base64.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "SQLiteDatabase.h"
#include "Templates/TypeHash.h"

namespace
{
	// Cursor codec + filter-hash hoisted to Private/Shared/RICursorCodec.{h,cpp}
	// to avoid unity-build collisions across the six query adapters. See that
	// header for rationale. Wire format / behaviour unchanged.

	// ---------------------------------------------------------------------
	// Distinct token universe of the reflect_uclasses.flags column.
	//
	// `flags` stores colon-joined UHT metadata keys (e.g.
	// "IsBlueprintBase:BlueprintType"). This walks every row, splits on ':',
	// and tallies a per-token class count. Shared by HandleListClassSpecifiers
	// (the full vocabulary action) and HandleFindClassSpecifier's empty-result
	// `known_tokens` hint. Caller already holds a valid game-thread DB handle.
	//
	// Counts are per-row occurrences: a token tallies at most once per class row
	// (colon-lists do not repeat a key within one row), so the count is the
	// number of UCLASSes carrying that token.
	// ---------------------------------------------------------------------

	/**
	 * Handover doc item #10 — best-effort source-line auto-join.
	 *
	 * UHT artefacts discard the original header line number, so every reflect_*
	 * row carries source_line=0. Rather than round-trip every caller through
	 * source_query("search_source"), look the line up in the same EngineSource.db
	 * symbol index that already powers source_query.
	 *
	 * Lookup shape:
	 *   SELECT line_start FROM symbols
	 *   WHERE name = ? AND kind IN ('class','struct')
	 *   LIMIT 1
	 *
	 * Why kind-restricted: `symbols.name` is the raw C++ identifier (preserves
	 * A/U/I prefix — verified in MonolithCppParser.cpp:170 where Kind is set to
	 * 'class' or 'struct'). For UCLASS rows this matches the class_name field
	 * 1:1.
	 *
	 * source_path resolution (handover doc item E): the UHT-derived
	 * reflect_uclasses.source_path stores the ModuleRelativePath
	 * ("Public/Foo/Bar.h") while symbols.file_id -> files.path stores the
	 * ABSOLUTE path from IFileManager::FindFilesRecursive over the
	 * ConvertRelativePathToFull module root (verified MonolithSourceIndexer.cpp
	 * IndexModule/IndexCppFile + MonolithSourceSubsystem.cpp:282-292). A direct
	 * equality JOIN of the two path forms would never match, so we instead reuse
	 * the SAME name-only symbol match that already powers the line lookup and
	 * additionally read the joined absolute path. The path is returned verbatim
	 * (absolute, e.g. "D:/Unreal Projects/.../Foo.h") — not relativised, because
	 * engine-source files live outside the project dir and would relativise to
	 * fragile "../../../" forms; an absolute path stays unambiguously navigable.
	 *
	 * Name-only lookup is a best-effort compromise: same-named classes in
	 * different modules collapse to the first symbol hit, so both the line AND the
	 * path may point at the wrong same-named class. Acceptable per the
	 * "empty/0 means unknown" contract — caller always tolerates a miss.
	 *
	 * Both out-params are left untouched (caller pre-zeros / pre-empties) on miss.
	 * Caller must already hold the shared DB lock (the borrowed source-symbol DB
	 * is the SAME handle this query uses).
	 */
	void LookupClassSource(FSQLiteDatabase& DB, const FString& ClassName, int32& OutLine, FString& OutPath)
	{
		if (ClassName.IsEmpty()) { return; }
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, TEXT(
			"SELECT s.line_start, f.path FROM symbols s "
			"JOIN files f ON f.id = s.file_id "
			"WHERE s.name = ? AND s.kind IN ('class','struct') "
			"LIMIT 1;")))
		{
			return;
		}
		Stmt.SetBindingValueByIndex(1, ClassName);
		if (Stmt.Step() != ESQLitePreparedStatementStepResult::Row) { return; }
		Stmt.GetColumnValueByIndex(0, OutLine);
		Stmt.GetColumnValueByIndex(1, OutPath);
	}

	/** Variant for UFUNCTION rows: scope the function-name lookup to the owning
	 *  class via the parent-symbol foreign key. Empty class falls back to a
	 *  bare name lookup (won't disambiguate between same-named functions in
	 *  different classes; engine code with that pattern keeps line=0). */
	int32 LookupFunctionSourceLine(FSQLiteDatabase& DB, const FString& OwningClass, const FString& FunctionName)
	{
		if (FunctionName.IsEmpty()) { return 0; }
		if (OwningClass.IsEmpty())
		{
			FSQLitePreparedStatement Stmt;
			if (!Stmt.Create(DB, TEXT(
				"SELECT line_start FROM symbols "
				"WHERE name = ? AND kind IN ('function','method') "
				"LIMIT 1;")))
			{
				return 0;
			}
			Stmt.SetBindingValueByIndex(1, FunctionName);
			if (Stmt.Step() != ESQLitePreparedStatementStepResult::Row) { return 0; }
			int32 Line = 0;
			Stmt.GetColumnValueByIndex(0, Line);
			return Line;
		}
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, TEXT(
			"SELECT s.line_start FROM symbols s "
			"JOIN symbols p ON p.id = s.parent_symbol_id "
			"WHERE s.name = ? AND s.kind IN ('function','method') "
			"  AND p.name = ? AND p.kind IN ('class','struct') "
			"LIMIT 1;")))
		{
			return 0;
		}
		Stmt.SetBindingValueByIndex(1, FunctionName);
		Stmt.SetBindingValueByIndex(2, OwningClass);
		if (Stmt.Step() != ESQLitePreparedStatementStepResult::Row) { return 0; }
		int32 Line = 0;
		Stmt.GetColumnValueByIndex(0, Line);
		return Line;
	}

	bool CollectClassSpecifierTokens(FSQLiteDatabase& DB, TMap<FString, int32>& OutCounts)
	{
		FSQLitePreparedStatement Stmt;
		if (!Stmt.Create(DB, TEXT(
			"SELECT flags FROM reflect_uclasses WHERE flags IS NOT NULL AND flags <> '';")))
		{
			return false;
		}
		while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
		{
			FString Flags;
			Stmt.GetColumnValueByIndex(0, Flags);
			if (Flags.IsEmpty()) { continue; }

			TArray<FString> Tokens;
			Flags.ParseIntoArray(Tokens, TEXT(":"), /*InCullEmpty=*/true);
			for (const FString& Token : Tokens)
			{
				const FString Trimmed = Token.TrimStartAndEnd();
				if (Trimmed.IsEmpty()) { continue; }
				int32& Count = OutCounts.FindOrAdd(Trimmed);
				++Count;
			}
		}
		return true;
	}

	// Build a `[{ token, count }]` JSON array from a token->count map, sorted by
	// descending count then ascending token for a stable, useful ordering.
	TArray<TSharedPtr<FJsonValue>> TokenCountsToJsonArray(const TMap<FString, int32>& Counts)
	{
		TArray<TPair<FString, int32>> Sorted;
		Sorted.Reserve(Counts.Num());
		for (const TPair<FString, int32>& Pair : Counts) { Sorted.Add(Pair); }
		Sorted.Sort([](const TPair<FString, int32>& A, const TPair<FString, int32>& B)
		{
			if (A.Value != B.Value) { return A.Value > B.Value; }
			return A.Key < B.Key;
		});

		TArray<TSharedPtr<FJsonValue>> Out;
		Out.Reserve(Sorted.Num());
		for (const TPair<FString, int32>& Pair : Sorted)
		{
			TSharedPtr<FJsonObject> O = MakeShared<FJsonObject>();
			O->SetStringField(TEXT("token"), Pair.Key);
			O->SetNumberField(TEXT("count"), Pair.Value);
			Out.Add(MakeShared<FJsonValueObject>(O));
		}
		return Out;
	}
}

// ============================================================================
// Registration
// ============================================================================

void FCppReflectQueryAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- get_uclass ----
	Registry.RegisterAction(TEXT("cppreflect"), TEXT("get_uclass"),
		TEXT("Return one UCLASS row plus all UPROPERTYs, all UFUNCTIONs, and the "
		     "parent-class chain. `class_name` is the C++ symbol with prefix "
		     "(e.g. \"ALeviathanCharacterBase\"). Returns null when the class "
		     "is not in the reflection index — call UBT before re-querying."),
		FMonolithActionHandler::CreateStatic(&FCppReflectQueryAdapter::HandleGetUClass),
		FParamSchemaBuilder()
			.Required(TEXT("class_name"), TEXT("string"),
				TEXT("C++ class symbol (e.g. ALeviathanCharacterBase)"))
			.Optional(TEXT("module_name"), TEXT("string"),
				TEXT("Optional module filter when the class exists in multiple modules"))
			.Build());

	// ---- list_uproperties ----
	Registry.RegisterAction(TEXT("cppreflect"), TEXT("list_uproperties"),
		TEXT("List UPROPERTY rows. Filter by `class_name` (recommended — "
		     "engine-scope queries can hit thousands of rows). "
		     "`blueprint_visible_only=true` filters to properties with a "
		     "blueprint_visibility specifier set. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FCppReflectQueryAdapter::HandleListUProperties),
		FParamSchemaBuilder()
			.Optional(TEXT("class_name"), TEXT("string"),
				TEXT("Filter by owning_class (exact match)"))
			.Optional(TEXT("blueprint_visible_only"), TEXT("boolean"),
				TEXT("Restrict to properties with a non-empty blueprint_visibility"), TEXT("false"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- list_ufunctions ----
	Registry.RegisterAction(TEXT("cppreflect"), TEXT("list_ufunctions"),
		TEXT("List UFUNCTION rows. Filter by `class_name` or restrict to "
		     "BlueprintCallable-eligible functions via `blueprint_callable_only`. "
		     "Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FCppReflectQueryAdapter::HandleListUFunctions),
		FParamSchemaBuilder()
			.Optional(TEXT("class_name"), TEXT("string"),
				TEXT("Filter by owning_class (exact match)"))
			.Optional(TEXT("blueprint_callable_only"), TEXT("boolean"),
				TEXT("Restrict to functions exposed to the BP VM"), TEXT("false"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- find_interface_impls ----
	Registry.RegisterAction(TEXT("cppreflect"), TEXT("find_interface_impls"),
		TEXT("List UCLASSes implementing `interface_name`. `interface_name` is "
		     "the U-prefixed companion class symbol (e.g. \"UISXWeaponFireBridgeInterface\"). "
		     "Returns the implementing_class + module + source_path tuple."),
		FMonolithActionHandler::CreateStatic(&FCppReflectQueryAdapter::HandleFindInterfaceImpls),
		FParamSchemaBuilder()
			.Required(TEXT("interface_name"), TEXT("string"),
				TEXT("U-prefixed interface class symbol"))
			.Build());

	// ---- find_class_specifier ----
	Registry.RegisterAction(TEXT("cppreflect"), TEXT("find_class_specifier"),
		TEXT("Find UCLASS rows whose `flags` column contains the given token. "
		     "NOTE: `flags` stores UHT METADATA KEYS, not raw C++ specifiers — "
		     "real stored tokens include \"IsBlueprintBase\", \"BlueprintType\", "
		     "\"Abstract\". A small alias map translates well-known C++ specifiers "
		     "(\"Blueprintable\" -> \"IsBlueprintBase\"). Specifiers UHT drops "
		     "entirely (\"MinimalAPI\", \"NotBlueprintable\") are NOT stored and "
		     "return an explicit not-captured note. Match is case-insensitive. "
		     "Call list_class_specifiers to discover the exact token universe. "
		     "Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FCppReflectQueryAdapter::HandleFindClassSpecifier),
		FParamSchemaBuilder()
			.Required(TEXT("specifier_name"), TEXT("string"),
				TEXT("UCLASS specifier or metadata-key token to search the flags column for"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- list_class_specifiers ----
	Registry.RegisterAction(TEXT("cppreflect"), TEXT("list_class_specifiers"),
		TEXT("Return the DISTINCT universe of tokens stored in the `flags` column "
		     "of reflect_uclasses, each with a per-token class count. The `flags` "
		     "column stores UHT metadata keys (e.g. \"IsBlueprintBase\", "
		     "\"BlueprintType\", \"Abstract\"), NOT raw C++ UCLASS specifiers. Use "
		     "this to discover what find_class_specifier can actually match."),
		FMonolithActionHandler::CreateStatic(&FCppReflectQueryAdapter::HandleListClassSpecifiers),
		FParamSchemaBuilder().Build());

	// Dispatcher annotation — all six handlers are pure SELECT against the
	// Phase 3a reflect_* tables.
	FMonolithDispatcherAnnotations Anno;
	Anno.bReadOnlyHint    = true;
	Anno.bDestructiveHint = false;
	Anno.bIdempotentHint  = true;
	Anno.Title = TEXT("C++ reflection-edge query");
	Registry.SetDispatcherAnnotations(TEXT("cppreflect"), Anno);
}

// ============================================================================
// DB accessor — lazy bootstrap of the cppreflect tables on first call.
// ============================================================================

FSQLiteDatabase* FCppReflectQueryAdapter::GetRawDB()
{
	// Phase 1+2 lesson #5: any DB accessor — read or write — runs on the game
	// thread. Writers (FUHTArtefactReader::Run, FAssetGraphJoiner::Run) already
	// enforce this; mirror the assertion on the read side.
	ensure(IsInGameThread());

	FMonolithReflectionIntelModule* Module =
		FModuleManager::GetModulePtr<FMonolithReflectionIntelModule>(
			TEXT("MonolithReflectionIntel"));
	if (!Module) { return nullptr; }

	FSQLiteDatabase* DB = Module->GetOrOpenCachedQueryDb();
	if (!DB) { return nullptr; }

	if (!Module->HasAttemptedCppReflectBootstrap())
	{
		Module->MarkCppReflectBootstrapAttempted();
		FSQLitePreparedStatement TableCheck;
		const bool bPrepared = TableCheck.Create(*DB,
			TEXT("SELECT name FROM sqlite_master WHERE type='table' AND name='reflect_uclasses';"));
		const bool bTableExists = bPrepared
			&& TableCheck.Step() == ESQLitePreparedStatementStepResult::Row;
		TableCheck.Destroy();

		// Handover doc item #1 — stale detection. Force-rebuild when the table
		// is absent OR the stamped indexer-code-version no longer matches the
		// current compiled constant. This catches the silent-stale-rows trap
		// caused by parser/schema changes that don't invalidate the table itself.
		bool bVersionMismatch = false;
		if (bTableExists)
		{
			int32 StoredVersion = 0;
			const bool bHasStamp = MonolithRIMeta::ReadStoredVersion(
				*DB, TEXT("cppreflect"), StoredVersion);
			const int32 CurrentVersion = MonolithRIMeta::GetIndexerCodeVersion(TEXT("cppreflect"));
			if (!bHasStamp || StoredVersion != CurrentVersion)
			{
				UE_LOG(LogMonolithReflectionIntel, Log,
					TEXT("cppreflect: stale-detection triggered (stored=%d, current=%d) — forcing rebuild"),
					bHasStamp ? StoredVersion : -1, CurrentVersion);
				bVersionMismatch = true;
			}
		}

		if (!bTableExists || bVersionMismatch)
		{
			Module->ResetCachedQueryDb();
			FString IndexerStatus;
			FMonolithReflectionIntelModule::RunCppReflectIndexersOnce(IndexerStatus);
			DB = Module->GetOrOpenCachedQueryDb();
			if (!DB) { return nullptr; }
		}
	}
	return DB;
}

// ============================================================================
// Handlers
// ============================================================================

FMonolithActionResult FCppReflectQueryAdapter::HandleGetUClass(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap, "
			     "or build the project at least once so UHT artefacts exist."));
	}

	const FString ClassName = Params->GetStringField(TEXT("class_name"));
	if (ClassName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`class_name` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}
	const FString ModuleFilter = Params->HasField(TEXT("module_name"))
		? Params->GetStringField(TEXT("module_name")) : FString();

	// --- UClass row(s) ---
	FString ClassSql = TEXT(
		"SELECT class_name, module_name, parent_class, source_path, source_line, flags "
		"FROM reflect_uclasses WHERE class_name = ?");
	if (!ModuleFilter.IsEmpty()) { ClassSql += TEXT(" AND module_name = ?"); }
	ClassSql += TEXT(" LIMIT 1;");

	FSQLitePreparedStatement ClassStmt;
	if (!ClassStmt.Create(*DB, *ClassSql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (reflect_uclasses absent?)."));
	}
	int32 BindIdx = 1;
	ClassStmt.SetBindingValueByIndex(BindIdx++, ClassName);
	if (!ModuleFilter.IsEmpty()) { ClassStmt.SetBindingValueByIndex(BindIdx++, ModuleFilter); }

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	if (ClassStmt.Step() != ESQLitePreparedStatementStepResult::Row)
	{
		Out->SetField(TEXT("uclass"), MakeShared<FJsonValueNull>());
		return FMonolithActionResult::Success(Out);
	}

	FString CName, MName, Parent, SrcPath, Flags;
	int32 SrcLine = 0;
	ClassStmt.GetColumnValueByIndex(0, CName);
	ClassStmt.GetColumnValueByIndex(1, MName);
	ClassStmt.GetColumnValueByIndex(2, Parent);
	ClassStmt.GetColumnValueByIndex(3, SrcPath);
	ClassStmt.GetColumnValueByIndex(4, SrcLine);
	ClassStmt.GetColumnValueByIndex(5, Flags);

	// Handover doc items #10 + E — best-effort auto-join the original source
	// line AND file path when the stored values are missing (UHT discards header
	// line numbers and the reflect_uclasses.source_path is the ModuleRelativePath
	// form, often empty; the source-symbol index carries both). A single joined
	// lookup fills whichever of the two is unknown. The name-only match may pick
	// the wrong file/line when two classes share a name (see LookupClassSource).
	if (SrcLine == 0 || SrcPath.IsEmpty())
	{
		int32 JoinedLine = 0;
		FString JoinedPath;
		LookupClassSource(*DB, CName, JoinedLine, JoinedPath);
		if (SrcLine == 0)       { SrcLine = JoinedLine; }
		if (SrcPath.IsEmpty())  { SrcPath = JoinedPath; }
	}

	TSharedPtr<FJsonObject> UClassObj = MakeShared<FJsonObject>();
	UClassObj->SetStringField(TEXT("class_name"), CName);
	UClassObj->SetStringField(TEXT("module_name"), MName);
	UClassObj->SetStringField(TEXT("parent_class"), Parent);
	UClassObj->SetStringField(TEXT("source_path"), SrcPath);
	UClassObj->SetNumberField(TEXT("source_line"), SrcLine);
	UClassObj->SetStringField(TEXT("flags"), Flags);

	// --- Parent-class chain via repeated lookup. Cap at 16 to avoid loops. ---
	{
		TArray<TSharedPtr<FJsonValue>> Chain;
		FString Cur = Parent;
		int32 Walks = 0;
		while (!Cur.IsEmpty() && Walks++ < 16)
		{
			FSQLitePreparedStatement ParentStmt;
			if (!ParentStmt.Create(*DB, TEXT(
				"SELECT parent_class FROM reflect_uclasses WHERE class_name = ? LIMIT 1;")))
			{
				break;
			}
			ParentStmt.SetBindingValueByIndex(1, Cur);
			if (ParentStmt.Step() != ESQLitePreparedStatementStepResult::Row)
			{
				// Unknown — engine class outside the index (UObject, AActor, etc).
				Chain.Add(MakeShared<FJsonValueString>(Cur));
				break;
			}
			Chain.Add(MakeShared<FJsonValueString>(Cur));
			FString Next;
			ParentStmt.GetColumnValueByIndex(0, Next);
			Cur = Next;
			if (Cur == Chain.Last()->AsString()) { break; } // defensive cycle guard
		}
		UClassObj->SetArrayField(TEXT("parent_chain"), Chain);
	}

	// --- All UPROPERTYs on this class ---
	{
		FSQLitePreparedStatement PropStmt;
		FString PropSql = TEXT(
			"SELECT property_name, property_type, cpp_module, blueprint_visibility, specifiers "
			"FROM reflect_uproperties WHERE owning_class = ?");
		if (!ModuleFilter.IsEmpty()) { PropSql += TEXT(" AND cpp_module = ?"); }
		PropSql += TEXT(" ORDER BY property_name;");
		if (PropStmt.Create(*DB, *PropSql))
		{
			int32 PBind = 1;
			PropStmt.SetBindingValueByIndex(PBind++, CName);
			if (!ModuleFilter.IsEmpty()) { PropStmt.SetBindingValueByIndex(PBind++, ModuleFilter); }

			TArray<TSharedPtr<FJsonValue>> Props;
			while (PropStmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				FString PName, PType, PModule, BpVis, Specs;
				PropStmt.GetColumnValueByIndex(0, PName);
				PropStmt.GetColumnValueByIndex(1, PType);
				PropStmt.GetColumnValueByIndex(2, PModule);
				PropStmt.GetColumnValueByIndex(3, BpVis);
				PropStmt.GetColumnValueByIndex(4, Specs);

				TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
				P->SetStringField(TEXT("property_name"), PName);
				P->SetStringField(TEXT("property_type"), PType);
				P->SetStringField(TEXT("cpp_module"), PModule);
				P->SetStringField(TEXT("blueprint_visibility"), BpVis);
				P->SetStringField(TEXT("specifiers"), Specs);
				Props.Add(MakeShared<FJsonValueObject>(P));
			}
			UClassObj->SetArrayField(TEXT("uproperties"), Props);
		}
	}

	// --- All UFUNCTIONs on this class ---
	{
		FSQLitePreparedStatement FuncStmt;
		FString FuncSql = TEXT(
			"SELECT function_name, return_type, blueprint_callable, cpp_module, specifiers "
			"FROM reflect_ufunctions WHERE owning_class = ?");
		if (!ModuleFilter.IsEmpty()) { FuncSql += TEXT(" AND cpp_module = ?"); }
		FuncSql += TEXT(" ORDER BY function_name;");
		if (FuncStmt.Create(*DB, *FuncSql))
		{
			int32 FBind = 1;
			FuncStmt.SetBindingValueByIndex(FBind++, CName);
			if (!ModuleFilter.IsEmpty()) { FuncStmt.SetBindingValueByIndex(FBind++, ModuleFilter); }

			TArray<TSharedPtr<FJsonValue>> Funcs;
			while (FuncStmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				FString FName, RetType, FModule, Specs;
				int32 BpCallable = 0;
				FuncStmt.GetColumnValueByIndex(0, FName);
				FuncStmt.GetColumnValueByIndex(1, RetType);
				FuncStmt.GetColumnValueByIndex(2, BpCallable);
				FuncStmt.GetColumnValueByIndex(3, FModule);
				FuncStmt.GetColumnValueByIndex(4, Specs);

				TSharedPtr<FJsonObject> F = MakeShared<FJsonObject>();
				F->SetStringField(TEXT("function_name"), FName);
				F->SetStringField(TEXT("return_type"), RetType);
				F->SetBoolField(TEXT("blueprint_callable"), BpCallable != 0);
				F->SetStringField(TEXT("cpp_module"), FModule);
				F->SetStringField(TEXT("specifiers"), Specs);
				Funcs.Add(MakeShared<FJsonValueObject>(F));
			}
			UClassObj->SetArrayField(TEXT("ufunctions"), Funcs);
		}
	}

	Out->SetObjectField(TEXT("uclass"), UClassObj);
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FCppReflectQueryAdapter::HandleListUProperties(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString ClassName = Params->HasField(TEXT("class_name"))
		? Params->GetStringField(TEXT("class_name")) : FString();
	const bool bBpOnly = Params->HasField(TEXT("blueprint_visible_only"))
		? Params->GetBoolField(TEXT("blueprint_visible_only")) : false;
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ ClassName, bBpOnly ? TEXT("1") : TEXT("0") });

	int32 Page = 0;
	int32 CachedTotal = -1;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
		CachedTotal = State.CachedTotalEstimate;
	}

	FString WhereSql = TEXT("WHERE 1=1");
	if (!ClassName.IsEmpty()) { WhereSql += TEXT(" AND owning_class = ?"); }
	if (bBpOnly)                { WhereSql += TEXT(" AND blueprint_visibility IS NOT NULL AND blueprint_visibility <> ''"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT owning_class, property_name, property_type, cpp_module, blueprint_visibility, specifiers "
			 "FROM reflect_uproperties %s "
			 "ORDER BY owning_class, property_name "
			 "LIMIT ? OFFSET ?;"),
		*WhereSql);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (reflect_uproperties absent?)."));
	}
	int32 BindIdx = 1;
	if (!ClassName.IsEmpty()) { Stmt.SetBindingValueByIndex(BindIdx++, ClassName); }
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString OClass, PName, PType, PModule, BpVis, Specs;
		Stmt.GetColumnValueByIndex(0, OClass);
		Stmt.GetColumnValueByIndex(1, PName);
		Stmt.GetColumnValueByIndex(2, PType);
		Stmt.GetColumnValueByIndex(3, PModule);
		Stmt.GetColumnValueByIndex(4, BpVis);
		Stmt.GetColumnValueByIndex(5, Specs);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("owning_class"), OClass);
		R->SetStringField(TEXT("property_name"), PName);
		R->SetStringField(TEXT("property_type"), PType);
		R->SetStringField(TEXT("cpp_module"), PModule);
		R->SetStringField(TEXT("blueprint_visibility"), BpVis);
		R->SetStringField(TEXT("specifiers"), Specs);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("uproperties"), Rows);

	if (!bHasCursor)
	{
		FString CountSql = TEXT("SELECT COUNT(*) FROM reflect_uproperties ") + WhereSql + TEXT(";");
		FSQLitePreparedStatement CountStmt;
		if (CountStmt.Create(*DB, *CountSql))
		{
			int32 CBind = 1;
			if (!ClassName.IsEmpty()) { CountStmt.SetBindingValueByIndex(CBind++, ClassName); }
			if (CountStmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				int32 Total = 0;
				CountStmt.GetColumnValueByIndex(0, Total);
				CachedTotal = Total;
				Out->SetNumberField(TEXT("total_estimate"), CachedTotal);
			}
		}
	}

	if (Rows.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = CachedTotal;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FCppReflectQueryAdapter::HandleListUFunctions(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString ClassName = Params->HasField(TEXT("class_name"))
		? Params->GetStringField(TEXT("class_name")) : FString();
	const bool bBpOnly = Params->HasField(TEXT("blueprint_callable_only"))
		? Params->GetBoolField(TEXT("blueprint_callable_only")) : false;
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ ClassName, bBpOnly ? TEXT("1") : TEXT("0") });

	int32 Page = 0;
	int32 CachedTotal = -1;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
		CachedTotal = State.CachedTotalEstimate;
	}

	FString WhereSql = TEXT("WHERE 1=1");
	if (!ClassName.IsEmpty()) { WhereSql += TEXT(" AND owning_class = ?"); }
	if (bBpOnly)                { WhereSql += TEXT(" AND blueprint_callable = 1"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT owning_class, function_name, return_type, blueprint_callable, cpp_module, specifiers, source_line "
			 "FROM reflect_ufunctions %s "
			 "ORDER BY owning_class, function_name "
			 "LIMIT ? OFFSET ?;"),
		*WhereSql);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (reflect_ufunctions absent?)."));
	}
	int32 BindIdx = 1;
	if (!ClassName.IsEmpty()) { Stmt.SetBindingValueByIndex(BindIdx++, ClassName); }
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString OClass, FName, RetType, FModule, Specs;
		int32 BpCallable = 0;
		int32 SrcLine = 0;
		Stmt.GetColumnValueByIndex(0, OClass);
		Stmt.GetColumnValueByIndex(1, FName);
		Stmt.GetColumnValueByIndex(2, RetType);
		Stmt.GetColumnValueByIndex(3, BpCallable);
		Stmt.GetColumnValueByIndex(4, FModule);
		Stmt.GetColumnValueByIndex(5, Specs);
		Stmt.GetColumnValueByIndex(6, SrcLine);

		// Handover doc item #10 — best-effort auto-join the original source
		// line from the symbol index when the stored value is 0.
		if (SrcLine == 0)
		{
			SrcLine = LookupFunctionSourceLine(*DB, OClass, FName);
		}

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("owning_class"), OClass);
		R->SetStringField(TEXT("function_name"), FName);
		R->SetStringField(TEXT("return_type"), RetType);
		R->SetBoolField(TEXT("blueprint_callable"), BpCallable != 0);
		R->SetStringField(TEXT("cpp_module"), FModule);
		R->SetStringField(TEXT("specifiers"), Specs);
		R->SetNumberField(TEXT("source_line"), SrcLine);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("ufunctions"), Rows);

	if (!bHasCursor)
	{
		FString CountSql = TEXT("SELECT COUNT(*) FROM reflect_ufunctions ") + WhereSql + TEXT(";");
		FSQLitePreparedStatement CountStmt;
		if (CountStmt.Create(*DB, *CountSql))
		{
			int32 CBind = 1;
			if (!ClassName.IsEmpty()) { CountStmt.SetBindingValueByIndex(CBind++, ClassName); }
			if (CountStmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				int32 Total = 0;
				CountStmt.GetColumnValueByIndex(0, Total);
				CachedTotal = Total;
				Out->SetNumberField(TEXT("total_estimate"), CachedTotal);
			}
		}
	}

	if (Rows.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = CachedTotal;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FCppReflectQueryAdapter::HandleFindInterfaceImpls(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString InterfaceName = Params->GetStringField(TEXT("interface_name"));
	if (InterfaceName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`interface_name` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	// Join the implementer rows with their reflect_uclasses entry so we can
	// surface module + source_path for each implementer.
	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT impl.implementing_class, impl.cpp_module, cls.source_path "
		"FROM reflect_uinterface_impls impl "
		"LEFT JOIN reflect_uclasses cls "
		"  ON cls.class_name = impl.implementing_class "
		" AND cls.module_name = impl.cpp_module "
		"WHERE impl.interface_name = ? "
		"ORDER BY impl.cpp_module, impl.implementing_class;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	Stmt.SetBindingValueByIndex(1, InterfaceName);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString CName, MName, SPath;
		Stmt.GetColumnValueByIndex(0, CName);
		Stmt.GetColumnValueByIndex(1, MName);
		Stmt.GetColumnValueByIndex(2, SPath);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("implementing_class"), CName);
		R->SetStringField(TEXT("cpp_module"), MName);
		R->SetStringField(TEXT("source_path"), SPath);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetStringField(TEXT("interface_name"), InterfaceName);
	Out->SetArrayField(TEXT("implementers"), Rows);
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FCppReflectQueryAdapter::HandleFindClassSpecifier(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString SpecifierName = Params->GetStringField(TEXT("specifier_name"));
	if (SpecifierName.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`specifier_name` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	// --- C++-specifier -> stored metadata-key translation ----------------
	// The `flags` column stores UHT metadata keys, not raw C++ UCLASS
	// specifiers (see CppReflectSchema.cpp / FUHTArtefactReader writer). Two
	// classes of well-known specifier need handling before we build the query:
	//
	//   1. ALIASED: UHT rewrites the specifier into a different stored key.
	//      The only mainstream one is Blueprintable -> IsBlueprintBase.
	//      ("BlueprintType" and "Abstract" pass through 1:1 and need no entry.)
	//   2. DROPPED:  UHT never stores the token at all (MinimalAPI is purely an
	//      export-macro hint; NotBlueprintable is encoded as ABSENCE of
	//      IsBlueprintBase). Searching the flags column for these can only ever
	//      return empty — so we answer honestly instead of a misleading [].
	//
	// Kept deliberately small and local: this is a find_class_specifier-only
	// affordance, not a general alias system (Phase D).
	const FString SpecLower = SpecifierName.ToLower();

	// Specifiers UHT drops entirely — never present in the metadata-key vocab.
	if (SpecLower == TEXT("minimalapi") || SpecLower == TEXT("notblueprintable"))
	{
		TMap<FString, int32> TokenCounts;
		CollectClassSpecifierTokens(*DB, TokenCounts);

		TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
		Out->SetStringField(TEXT("specifier_name"), SpecifierName);
		Out->SetArrayField(TEXT("uclasses"), TArray<TSharedPtr<FJsonValue>>());
		Out->SetBoolField(TEXT("token_stored"), false);
		Out->SetStringField(TEXT("note"), FString::Printf(TEXT(
			"\"%s\" is a C++ UCLASS specifier that UHT does not store in the "
			"metadata-key vocabulary (the `flags` column), so it can never match. "
			"Call list_class_specifiers to see the tokens that are queryable."),
			*SpecifierName));
		Out->SetArrayField(TEXT("known_tokens"), TokenCountsToJsonArray(TokenCounts));
		return FMonolithActionResult::Success(Out);
	}

	// Aliased specifiers: translate to the stored metadata key before querying.
	FString EffectiveToken = SpecifierName;
	if (SpecLower == TEXT("blueprintable"))
	{
		EffectiveToken = TEXT("IsBlueprintBase");
	}

	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ SpecifierName });

	int32 Page = 0;
	const bool bHasCursor = !CursorIn.IsEmpty();
	if (bHasCursor)
	{
		FRICursorState State;
		if (!DecodeRICursor(CursorIn, State))
		{
			return RIInvalidCursorError(TEXT("Cursor decode failed; restart pagination without `cursor`."));
		}
		if (State.QueryHash != FilterHash)
		{
			return RIInvalidCursorError(TEXT("Cursor filter mismatch; restart pagination without `cursor`."));
		}
		Page = State.Page;
	}

	// Match against the colon-delimited `flags` column using the translated
	// EffectiveToken (see alias map above). SQLite LIKE pattern:
	//   `flags = ?`                exact-only (whole metadata-key list = match)
	//   `flags LIKE ?:%`           starts with this token
	//   `flags LIKE %:?:%`         contains this token in the middle
	//   `flags LIKE %:?`           ends with this token
	// We OR all four shapes to catch any position. Simpler than a regex.
	// The exact arm carries COLLATE NOCASE so single-token flags match
	// case-insensitively (LIKE is already ASCII-case-insensitive in SQLite).
	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT class_name, module_name, parent_class, source_path, flags "
		"FROM reflect_uclasses "
		"WHERE flags = ?1 COLLATE NOCASE OR flags LIKE ?2 OR flags LIKE ?3 OR flags LIKE ?4 "
		"ORDER BY module_name, class_name "
		"LIMIT ? OFFSET ?;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	const FString ExactMatch = EffectiveToken;
	const FString PrefixMatch = EffectiveToken + TEXT(":%");
	const FString MidMatch    = TEXT("%:") + EffectiveToken + TEXT(":%");
	const FString SuffixMatch = TEXT("%:") + EffectiveToken;
	Stmt.SetBindingValueByIndex(1, ExactMatch);
	Stmt.SetBindingValueByIndex(2, PrefixMatch);
	Stmt.SetBindingValueByIndex(3, MidMatch);
	Stmt.SetBindingValueByIndex(4, SuffixMatch);
	Stmt.SetBindingValueByIndex(5, Limit);
	Stmt.SetBindingValueByIndex(6, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString CName, MName, Parent, SPath, Flags;
		Stmt.GetColumnValueByIndex(0, CName);
		Stmt.GetColumnValueByIndex(1, MName);
		Stmt.GetColumnValueByIndex(2, Parent);
		Stmt.GetColumnValueByIndex(3, SPath);
		Stmt.GetColumnValueByIndex(4, Flags);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("class_name"), CName);
		R->SetStringField(TEXT("module_name"), MName);
		R->SetStringField(TEXT("parent_class"), Parent);
		R->SetStringField(TEXT("source_path"), SPath);
		R->SetStringField(TEXT("flags"), Flags);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetStringField(TEXT("specifier_name"), SpecifierName);
	// Surface the alias translation so the caller understands what was actually
	// queried (e.g. caller typed "Blueprintable", translated to "IsBlueprintBase").
	// Set unconditionally of row count so the empty-result hint path below also
	// carries it — an empty result must still tell the caller the queried token.
	if (EffectiveToken != SpecifierName)
	{
		Out->SetStringField(TEXT("effective_token"), EffectiveToken);
	}
	Out->SetArrayField(TEXT("uclasses"), Rows);

	// Informative empty response: when the first page matched zero rows, attach
	// the full distinct token universe so the caller can self-correct without a
	// second round-trip to list_class_specifiers. (effective_token, if an alias
	// was applied, is already attached above.)
	if (Rows.Num() == 0 && !bHasCursor)
	{
		TMap<FString, int32> TokenCounts;
		CollectClassSpecifierTokens(*DB, TokenCounts);
		Out->SetArrayField(TEXT("known_tokens"), TokenCountsToJsonArray(TokenCounts));
	}

	if (Rows.Num() == Limit)
	{
		FRICursorState OutCursor;
		OutCursor.QueryHash = FilterHash;
		OutCursor.Page = Page + 1;
		OutCursor.CachedTotalEstimate = -1;
		Out->SetStringField(TEXT("next_cursor"), EncodeRICursor(OutCursor));
	}
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FCppReflectQueryAdapter::HandleListClassSpecifiers(const TSharedPtr<FJsonObject>& /*Params*/)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	// The token universe is small (a few dozen distinct metadata keys across the
	// whole index), so no pagination is needed — return the full distinct set
	// with per-token class counts. `flags` stores UHT metadata keys, not raw
	// C++ specifiers (see HandleFindClassSpecifier's alias map).
	TMap<FString, int32> TokenCounts;
	if (!CollectClassSpecifierTokens(*DB, TokenCounts))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (reflect_uclasses absent?)."));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("specifiers"), TokenCountsToJsonArray(TokenCounts));
	Out->SetNumberField(TEXT("distinct_count"), TokenCounts.Num());
	return FMonolithActionResult::Success(Out);
}
