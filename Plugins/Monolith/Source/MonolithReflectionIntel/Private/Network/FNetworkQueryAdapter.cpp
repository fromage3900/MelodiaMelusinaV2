// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FNetworkQueryAdapter — implementation. Four read-only handlers composed over
// Phase 3a (reflect_ufunctions) + Phase 4a (reflect_replicated_properties)
// tables. All run on the game thread.
//
// Cursor codec mirrored from the Phase 1/2/3a adapters — consolidation into
// MonolithCore is a Phase 5+ item and explicitly out of Phase 4a scope.

#include "Network/FNetworkQueryAdapter.h"
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

	/**
	 * Classify an RPC kind from the stored `specifiers` column (the normalized
	 * EFunctionFlags string written by FUHTArtefactReader, e.g. "Server,Reliable"
	 * / "Client" / "NetMulticast,Unreliable"):
	 *   contains "Server"       → "Server"
	 *   contains "Client"       → "Client"
	 *   contains "NetMulticast" → "Multicast"
	 *
	 * Returns FString() when no endpoint token is present. The "Multicast"
	 * canonical form is surfaced to callers for symmetry with the historical
	 * rpc_kind vocabulary (Server | Client | Multicast).
	 */
	FString ClassifyRpcKindFromSpecifiers(const FString& Specifiers)
	{
		if (Specifiers.Contains(TEXT("Server")))       { return TEXT("Server"); }
		if (Specifiers.Contains(TEXT("Client")))       { return TEXT("Client"); }
		if (Specifiers.Contains(TEXT("NetMulticast"))) { return TEXT("Multicast"); }
		return FString();
	}
}

// ============================================================================
// Registration
// ============================================================================

void FNetworkQueryAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- list_replicated_classes ----
	Registry.RegisterAction(TEXT("network"), TEXT("list_replicated_classes"),
		TEXT("List UCLASSes that contain at least one replicated UPROPERTY. "
		     "Aggregated from reflect_replicated_properties, which captures both "
		     "UPROPERTY(ReplicatedUsing=OnRep_Foo) (from UHT metadata blocks) and "
		     "bare UPROPERTY(Replicated) / DOREPLIFETIME replication (from the "
		     "CPF_Net property flag). Each row carries owning_class, cpp_module, and "
		     "a `replicated_property_count` of distinct replicated properties on "
		     "that class. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FNetworkQueryAdapter::HandleListReplicatedClasses),
		FParamSchemaBuilder()
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- list_rpc_functions ----
	Registry.RegisterAction(TEXT("network"), TEXT("list_rpc_functions"),
		TEXT("List UFUNCTION RPCs detected from their net specifiers. Matches on "
		     "reflect_ufunctions.specifiers (the normalized EFunctionFlags string — "
		     "e.g. `Server,Reliable` / `Client` / `NetMulticast,Unreliable`), so it "
		     "captures RPCs named plainly (UFUNCTION(Server, Reliable) Reload()) that "
		     "name-prefix matching would miss. Each row carries the parsed `specifiers` "
		     "and a canonical `rpc_kind` (Server|Client|Multicast). Filter by "
		     "`class_name` (exact) and/or `rpc_kind`. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FNetworkQueryAdapter::HandleListRPCFunctions),
		FParamSchemaBuilder()
			.Optional(TEXT("class_name"), TEXT("string"),
				TEXT("Filter by owning_class (exact match)"))
			.Optional(TEXT("rpc_kind"), TEXT("string"),
				TEXT("Restrict to one of: Server | Client | Multicast"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- list_onrep_handlers ----
	Registry.RegisterAction(TEXT("network"), TEXT("list_onrep_handlers"),
		TEXT("List UFUNCTIONs matching the `OnRep_*` name pattern (replication "
		     "notification handlers). Pure name-pattern SQL on "
		     "reflect_ufunctions. Filter by `class_name` (exact). Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FNetworkQueryAdapter::HandleListOnRepHandlers),
		FParamSchemaBuilder()
			.Optional(TEXT("class_name"), TEXT("string"),
				TEXT("Filter by owning_class (exact match)"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- audit_unbalanced_onreps ----
	Registry.RegisterAction(TEXT("network"), TEXT("audit_unbalanced_onreps"),
		TEXT("Audit: surface UPROPERTY(ReplicatedUsing=OnRep_Foo) declarations "
		     "whose `OnRep_Foo` UFUNCTION is MISSING on the same class. SQL "
		     "anti-join between reflect_replicated_properties (rep_kind = "
		     "'ReplicatedUsing') and reflect_ufunctions (function_name = "
		     "rep_notify_func). Common net-code refactor bug. Read-only. "
		     "Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FNetworkQueryAdapter::HandleAuditUnbalancedOnReps),
		FParamSchemaBuilder()
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// Dispatcher annotation — all four handlers are pure SELECT against the
	// Phase 3a + Phase 4a tables.
	FMonolithDispatcherAnnotations Anno;
	Anno.bReadOnlyHint    = true;
	Anno.bDestructiveHint = false;
	Anno.bIdempotentHint  = true;
	Anno.Title = TEXT("Replication + RPC reflection query");
	Registry.SetDispatcherAnnotations(TEXT("network"), Anno);
}

// ============================================================================
// DB accessor — lazy bootstrap of the network indexer on first call.
// ============================================================================

FSQLiteDatabase* FNetworkQueryAdapter::GetRawDB()
{
	ensure(IsInGameThread());

	FMonolithReflectionIntelModule* Module =
		FModuleManager::GetModulePtr<FMonolithReflectionIntelModule>(
			TEXT("MonolithReflectionIntel"));
	if (!Module) { return nullptr; }

	FSQLiteDatabase* DB = Module->GetOrOpenCachedQueryDb();
	if (!DB) { return nullptr; }

	if (!Module->HasAttemptedNetworkBootstrap())
	{
		Module->MarkNetworkBootstrapAttempted();
		FSQLitePreparedStatement TableCheck;
		const bool bPrepared = TableCheck.Create(*DB,
			TEXT("SELECT name FROM sqlite_master WHERE type='table' "
			     "AND name='reflect_replicated_properties';"));
		const bool bTableExists = bPrepared
			&& TableCheck.Step() == ESQLitePreparedStatementStepResult::Row;
		TableCheck.Destroy();

		// Handover doc item #1 — stale detection. Force-rebuild when the table
		// is absent OR the stamped code-version no longer matches the current
		// compiled constant.
		bool bVersionMismatch = false;
		if (bTableExists)
		{
			int32 StoredVersion = 0;
			const bool bHasStamp = MonolithRIMeta::ReadStoredVersion(
				*DB, TEXT("network"), StoredVersion);
			const int32 CurrentVersion = MonolithRIMeta::GetIndexerCodeVersion(TEXT("network"));
			if (!bHasStamp || StoredVersion != CurrentVersion)
			{
				UE_LOG(LogMonolithReflectionIntel, Log,
					TEXT("network: stale-detection triggered (stored=%d, current=%d) — forcing rebuild"),
					bHasStamp ? StoredVersion : -1, CurrentVersion);
				bVersionMismatch = true;
			}
		}

		if (!bTableExists || bVersionMismatch)
		{
			Module->ResetCachedQueryDb();
			FString IndexerStatus;
			FMonolithReflectionIntelModule::RunNetworkIndexerOnce(IndexerStatus);
			DB = Module->GetOrOpenCachedQueryDb();
			if (!DB) { return nullptr; }
		}
	}
	return DB;
}

// ============================================================================
// Handlers
// ============================================================================

FMonolithActionResult FNetworkQueryAdapter::HandleListReplicatedClasses(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap, "
			     "or build the project at least once so UHT artefacts exist."));
	}

	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({});

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

	const TCHAR* Sql = TEXT(
		"SELECT owning_class, cpp_module, COUNT(*) AS prop_count "
		"FROM reflect_replicated_properties "
		"GROUP BY owning_class, cpp_module "
		"ORDER BY cpp_module, owning_class "
		"LIMIT ? OFFSET ?;");

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (reflect_replicated_properties absent?)."));
	}
	Stmt.SetBindingValueByIndex(1, Limit);
	Stmt.SetBindingValueByIndex(2, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString OClass, MName;
		int32 Count = 0;
		Stmt.GetColumnValueByIndex(0, OClass);
		Stmt.GetColumnValueByIndex(1, MName);
		Stmt.GetColumnValueByIndex(2, Count);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("owning_class"), OClass);
		R->SetStringField(TEXT("cpp_module"), MName);
		R->SetNumberField(TEXT("replicated_property_count"), Count);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("classes"), Rows);

	if (!bHasCursor)
	{
		FSQLitePreparedStatement CountStmt;
		if (CountStmt.Create(*DB, TEXT(
			"SELECT COUNT(*) FROM (SELECT 1 FROM reflect_replicated_properties "
			"GROUP BY owning_class, cpp_module);")))
		{
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

FMonolithActionResult FNetworkQueryAdapter::HandleListRPCFunctions(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString ClassName = Params->HasField(TEXT("class_name"))
		? Params->GetStringField(TEXT("class_name")) : FString();
	const FString RpcKindFilter = Params->HasField(TEXT("rpc_kind"))
		? Params->GetStringField(TEXT("rpc_kind")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ ClassName, RpcKindFilter });

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

	// Specifier-based detection (network workstream). The authoritative net
	// signal is reflect_ufunctions.specifiers — the normalized EFunctionFlags
	// string FUHTArtefactReader writes for every UFUNCTION RPC (e.g.
	// "Server,Reliable"). A non-RPC function has an empty/NULL specifiers value
	// and never matches. We OR the three endpoint tokens; the optional
	// `rpc_kind` filter restricts further in C++. All inputs are BOUND — no
	// concatenation of caller-supplied strings into SQL.
	FString WhereSql = TEXT(
		"WHERE (specifiers LIKE '%Server%' "
		"   OR specifiers LIKE '%Client%' "
		"   OR specifiers LIKE '%NetMulticast%')");
	if (!ClassName.IsEmpty()) { WhereSql += TEXT(" AND owning_class = ?"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT owning_class, function_name, cpp_module, blueprint_callable, specifiers "
		     "FROM reflect_ufunctions %s "
		     "ORDER BY cpp_module, owning_class, function_name "
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
		FString OClass, FName, MName, Specifiers;
		int32 BpCallable = 0;
		Stmt.GetColumnValueByIndex(0, OClass);
		Stmt.GetColumnValueByIndex(1, FName);
		Stmt.GetColumnValueByIndex(2, MName);
		Stmt.GetColumnValueByIndex(3, BpCallable);
		Stmt.GetColumnValueByIndex(4, Specifiers);

		const FString Kind = ClassifyRpcKindFromSpecifiers(Specifiers);
		// Filter by rpc_kind in C++ (cheaper than an OR-chain inside the SQL).
		if (!RpcKindFilter.IsEmpty() && !Kind.Equals(RpcKindFilter, ESearchCase::IgnoreCase))
		{
			continue;
		}

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("owning_class"), OClass);
		R->SetStringField(TEXT("function_name"), FName);
		R->SetStringField(TEXT("cpp_module"), MName);
		R->SetStringField(TEXT("rpc_kind"), Kind);
		R->SetStringField(TEXT("specifiers"), Specifiers);
		R->SetBoolField(TEXT("blueprint_callable"), BpCallable != 0);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("rpcs"), Rows);

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

FMonolithActionResult FNetworkQueryAdapter::HandleListOnRepHandlers(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString ClassName = Params->HasField(TEXT("class_name"))
		? Params->GetStringField(TEXT("class_name")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ ClassName });

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

	FString WhereSql = TEXT("WHERE function_name LIKE 'OnRep_%'");
	if (!ClassName.IsEmpty()) { WhereSql += TEXT(" AND owning_class = ?"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT owning_class, function_name, cpp_module "
		     "FROM reflect_ufunctions %s "
		     "ORDER BY cpp_module, owning_class, function_name "
		     "LIMIT ? OFFSET ?;"),
		*WhereSql);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	int32 BindIdx = 1;
	if (!ClassName.IsEmpty()) { Stmt.SetBindingValueByIndex(BindIdx++, ClassName); }
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString OClass, FName, MName;
		Stmt.GetColumnValueByIndex(0, OClass);
		Stmt.GetColumnValueByIndex(1, FName);
		Stmt.GetColumnValueByIndex(2, MName);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("owning_class"), OClass);
		R->SetStringField(TEXT("function_name"), FName);
		R->SetStringField(TEXT("cpp_module"), MName);
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("handlers"), Rows);

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

FMonolithActionResult FNetworkQueryAdapter::HandleAuditUnbalancedOnReps(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({});

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

	// Anti-join: a ReplicatedUsing-tagged property whose rep_notify_func has
	// no matching UFUNCTION on the same class. The match is by owning_class
	// AND function_name = rep_notify_func. NULL on the right side of the
	// LEFT JOIN identifies violations.
	const TCHAR* Sql = TEXT(
		"SELECT rp.owning_class, rp.property_name, rp.cpp_module, rp.rep_notify_func "
		"FROM reflect_replicated_properties rp "
		"LEFT JOIN reflect_ufunctions uf "
		"  ON uf.owning_class = rp.owning_class "
		" AND uf.function_name = rp.rep_notify_func "
		" AND uf.cpp_module = rp.cpp_module "
		"WHERE rp.rep_kind = 'ReplicatedUsing' "
		"  AND rp.rep_notify_func IS NOT NULL "
		"  AND rp.rep_notify_func <> '' "
		"  AND uf.function_name IS NULL "
		"ORDER BY rp.cpp_module, rp.owning_class, rp.property_name "
		"LIMIT ? OFFSET ?;");

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	Stmt.SetBindingValueByIndex(1, Limit);
	Stmt.SetBindingValueByIndex(2, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString OClass, PName, MName, RepNotify;
		Stmt.GetColumnValueByIndex(0, OClass);
		Stmt.GetColumnValueByIndex(1, PName);
		Stmt.GetColumnValueByIndex(2, MName);
		Stmt.GetColumnValueByIndex(3, RepNotify);

		TSharedPtr<FJsonObject> R = MakeShared<FJsonObject>();
		R->SetStringField(TEXT("owning_class"), OClass);
		R->SetStringField(TEXT("property_name"), PName);
		R->SetStringField(TEXT("cpp_module"), MName);
		R->SetStringField(TEXT("missing_function"), RepNotify);
		R->SetStringField(TEXT("violation"),
			TEXT("UPROPERTY(ReplicatedUsing) references an OnRep_ UFUNCTION that does not exist on this class."));
		Rows.Add(MakeShared<FJsonValueObject>(R));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("violations"), Rows);

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
