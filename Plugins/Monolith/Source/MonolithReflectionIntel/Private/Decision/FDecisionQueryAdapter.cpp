// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).
//
// FDecisionQueryAdapter — implementation. Registers and serves 5 actions:
//   - decision_query("list_decisions",          {path_filter?, min_confidence?, status?, limit?, cursor?})
//   - decision_query("get_decision",            {decision_id})
//   - decision_query("list_stale",              {max_age_days, path_filter?, limit?, cursor?})
//   - decision_query("find_supersession_chain", {decision_id, depth?})
//   - decision_query("find_referent_decisions", {decision_id})
//
// All handlers are READ-ONLY against `decision_records` / `decision_supersedes`
// in EngineSource.db. Game-thread execution. Writes never happen here.
//
// DEVIATION (vs plan §0 mention of FMonolithSourceDatabase shared handle):
// The plan implies a `GetRawDatabase()` accessor on FMonolithSourceDatabase, but
// the live header does not expose one. Adapter falls back to opening a READ
// handle on the same DB file when the subsystem returns no accessor. See the
// GetRawDB() helper below for the exact policy.

#include "Decision/FDecisionQueryAdapter.h"
#include "MonolithReflectionIntelModule.h"
#include "MonolithRIMetaTable.h"
#include "Shared/RICursorCodec.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "HAL/PlatformFileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/Base64.h"
#include "Misc/DateTime.h"
#include "Misc/Paths.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "SQLiteDatabase.h"
#include "Templates/TypeHash.h"

namespace
{
	// Cursor codec (struct + Encode/Decode + InvalidCursorError) hoisted to
	// Private/Shared/RICursorCodec.{h,cpp} to avoid unity-build collisions across
	// the six query adapters. See that header for rationale. Wire format /
	// behaviour unchanged.
	//
	// NOTE: this adapter's ComputeFilterHash takes (FString, double, FString) —
	// a DIFFERENT signature from the four adapters that took an
	// initializer_list<FString> (now RIComputeFilterHash in RICursorCodec).
	// It is intentionally kept file-local (not hoisted)
	// because unifying the two signatures would change behaviour. After the codec
	// hoist this is the only ComputeFilterHash in the module, so it no longer
	// collides under unity.

	uint32 ComputeFilterHash(const FString& PathFilter, double MinConfidence, const FString& Status)
	{
		uint32 H = GetTypeHash(PathFilter);
		H = HashCombine(H, GetTypeHash(MinConfidence));
		H = HashCombine(H, GetTypeHash(Status));
		return H;
	}

	// Marshal a SQLite row into a JSON object matching the standard envelope.
	TSharedPtr<FJsonObject> RowToJson(FSQLitePreparedStatement& Stmt)
	{
		TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
		FString DecId, Title, Status, SourcePath, Rationale;
		int32 Line = 0;
		double Confidence = 0.0;
		int64 Mtime = 0;
		Stmt.GetColumnValueByIndex(0, DecId);
		Stmt.GetColumnValueByIndex(1, Title);
		Stmt.GetColumnValueByIndex(2, Status);
		Stmt.GetColumnValueByIndex(3, SourcePath);
		Stmt.GetColumnValueByIndex(4, Line);
		Stmt.GetColumnValueByIndex(5, Confidence);
		Stmt.GetColumnValueByIndex(6, Rationale);
		Stmt.GetColumnValueByIndex(7, Mtime);

		Row->SetStringField(TEXT("decision_id"), DecId);
		Row->SetStringField(TEXT("title"), Title);
		Row->SetStringField(TEXT("status"), Status);
		Row->SetStringField(TEXT("source_path"), SourcePath);
		Row->SetNumberField(TEXT("source_line"), Line);
		Row->SetNumberField(TEXT("confidence"), Confidence);
		Row->SetStringField(TEXT("rationale"), Rationale);
		Row->SetNumberField(TEXT("source_mtime"), static_cast<double>(Mtime));
		return Row;
	}

	const TCHAR* kSelectColumns = TEXT(
		"decision_id, title, status, source_path, source_line, confidence, rationale, source_mtime");

	// Resolve the EngineSource.db path the same way UMonolithSourceSubsystem does.
	FString ResolveEngineSourceDbPath()
	{
		TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("Monolith"));
		if (Plugin.IsValid())
		{
			return Plugin->GetBaseDir() / TEXT("Saved") / TEXT("EngineSource.db");
		}
		return FPaths::ProjectPluginsDir() / TEXT("Monolith") / TEXT("Saved") / TEXT("EngineSource.db");
	}
}

// ============================================================================
// Registration
// ============================================================================

void FDecisionQueryAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- list_decisions ----
	Registry.RegisterAction(TEXT("decision"), TEXT("list_decisions"),
		TEXT("List architectural decisions extracted from project markdown. "
		     "Filterable by source-path prefix and minimum heuristic confidence. "
		     "Supports cursor pagination — pass `cursor` from a prior `next_cursor`."),
		FMonolithActionHandler::CreateStatic(&FDecisionQueryAdapter::HandleListDecisions),
		FParamSchemaBuilder()
			// v0.17.0 §0: DiskPath kind on path_filter — markdown root prefix.
			.OptionalDiskPath(TEXT("path_filter"),
				TEXT("Substring match against source_path (project-relative)"))
			.Optional(TEXT("min_confidence"), TEXT("number"),
				TEXT("Minimum heuristic confidence in [0,1]"), TEXT("0.6"))
			.Optional(TEXT("status"), TEXT("string"),
				TEXT("Filter by status (open/accepted/superseded/deprecated/draft)"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor from a prior `next_cursor`"))
			.Build());

	// ---- get_decision ----
	Registry.RegisterAction(TEXT("decision"), TEXT("get_decision"),
		TEXT("Fetch one decision record by its stable decision_id."),
		FMonolithActionHandler::CreateStatic(&FDecisionQueryAdapter::HandleGetDecision),
		FParamSchemaBuilder()
			.Required(TEXT("decision_id"), TEXT("string"),
				TEXT("Stable decision id (e.g. `Docs/specs/SPEC_X.md#some-anchor`)"))
			.Build());

	// ---- list_stale ----
	Registry.RegisterAction(TEXT("decision"), TEXT("list_stale"),
		TEXT("List decisions whose source markdown has not been modified within "
		     "`max_age_days` days. Useful for spec-drift detection."),
		FMonolithActionHandler::CreateStatic(&FDecisionQueryAdapter::HandleListStale),
		FParamSchemaBuilder()
			.Required(TEXT("max_age_days"), TEXT("integer"),
				TEXT("Staleness threshold in days (compared against source-file mtime)"))
			.OptionalDiskPath(TEXT("path_filter"),
				TEXT("Substring match against source_path (project-relative)"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor from a prior `next_cursor`"))
			.Build());

	// ---- find_supersession_chain ----
	Registry.RegisterAction(TEXT("decision"), TEXT("find_supersession_chain"),
		TEXT("Walk supersedes edges outward from a decision_id. Returns the "
		     "ordered chain of decisions this one supersedes, transitively."),
		FMonolithActionHandler::CreateStatic(&FDecisionQueryAdapter::HandleFindSupersessionChain),
		FParamSchemaBuilder()
			.Required(TEXT("decision_id"), TEXT("string"),
				TEXT("Stable decision id to start the walk from"))
			.Optional(TEXT("depth"), TEXT("integer"),
				TEXT("Maximum walk depth (default 10, hard cap 50)"), TEXT("10"))
			.Build());

	// ---- find_referent_decisions ----
	Registry.RegisterAction(TEXT("decision"), TEXT("find_referent_decisions"),
		TEXT("Inverse of find_supersession_chain — list decisions that explicitly "
		     "supersede the given decision_id (i.e. who replaced it)."),
		FMonolithActionHandler::CreateStatic(&FDecisionQueryAdapter::HandleFindReferentDecisions),
		FParamSchemaBuilder()
			.Required(TEXT("decision_id"), TEXT("string"),
				TEXT("Stable decision id to find supersession referrers for"))
			.Build());

	// v0.17.0 §0 — annotate the dispatcher as read-only + idempotent (re-running
	// any of these handlers against an unchanged DB yields the same envelope).
	FMonolithDispatcherAnnotations Anno;
	Anno.bReadOnlyHint = true;
	Anno.bDestructiveHint = false;
	Anno.bIdempotentHint = true;
	Anno.Title = TEXT("Decision-record query");
	Registry.SetDispatcherAnnotations(TEXT("decision"), Anno);
}

// ============================================================================
// DB accessor
// ============================================================================

FSQLiteDatabase* FDecisionQueryAdapter::GetRawDB()
{
	// Thread-safety contract (matches FNetworkQueryAdapter / FAuditAdapter /
	// FCppReflectQueryAdapter / FRiskQueryAdapter): RI borrows the subsystem's
	// open EngineSource.db handle. All access must be game-thread-only — the
	// subsystem's handle close runs on the game thread (its reindex trigger is
	// game-thread-dispatched), so game-thread-only reads serialise against that
	// close without any per-read lock.
	ensure(IsInGameThread());

	// SHARED-HANDLE POLICY (corrected 2026-05-29, plan §0): borrow
	// UMonolithSourceSubsystem's already-open handle via GetOrOpenCachedQueryDb;
	// the module no longer opens its own ReadOnly handle (the UE 5.7 single-open
	// `unreal-fs` VFS rejected the second open with SQLITE_IOERR).
	//
	// On-demand bootstrap: if `decision_records` is missing from the DB, ask
	// FMonolithReflectionIntelModule::RunDecisionIndexerOnce to run the indexer.
	// That transient ReadWrite open happens only while the subsystem's handle is
	// closed (during a reindex), so it does not collide with the single-open VFS.

	FMonolithReflectionIntelModule* Module =
		FModuleManager::GetModulePtr<FMonolithReflectionIntelModule>(
			TEXT("MonolithReflectionIntel"));
	if (!Module)
	{
		// Module has been unloaded — refuse to operate on stale state rather
		// than reaching into a process-static handle that may have outlived
		// the SQLiteCore module.
		return nullptr;
	}

	FSQLiteDatabase* DB = Module->GetOrOpenCachedQueryDb();
	if (!DB)
	{
		// EngineSource.db missing or failed to open ReadOnly — caller's
		// error string surfaces the "run source.trigger_reindex" hint.
		return nullptr;
	}

	// Lazy first-call bootstrap: if `decision_records` is missing from the DB
	// (it lives there only after the indexer has run at least once), kick the
	// indexer now. The latch lives on the module instance so a Live Coding
	// module reload re-arms it automatically.
	if (!Module->HasAttemptedBootstrap())
	{
		Module->MarkBootstrapAttempted();
		FSQLitePreparedStatement TableCheck;
		const bool bPrepared = TableCheck.Create(*DB,
			TEXT("SELECT name FROM sqlite_master WHERE type='table' AND name='decision_records';"));
		const bool bTableExists = bPrepared
			&& TableCheck.Step() == ESQLitePreparedStatementStepResult::Row;
		// Release the prepared statement before tearing down the underlying handle.
		TableCheck.Destroy();

		// Handover doc item #1 — stale detection. Force-rebuild when the table
		// is absent OR the stamped code-version no longer matches the current
		// compiled constant.
		bool bVersionMismatch = false;
		if (bTableExists)
		{
			int32 StoredVersion = 0;
			const bool bHasStamp = MonolithRIMeta::ReadStoredVersion(
				*DB, TEXT("decision"), StoredVersion);
			const int32 CurrentVersion = MonolithRIMeta::GetIndexerCodeVersion(TEXT("decision"));
			if (!bHasStamp || StoredVersion != CurrentVersion)
			{
				UE_LOG(LogMonolithReflectionIntel, Log,
					TEXT("decision: stale-detection triggered (stored=%d, current=%d) — forcing rebuild"),
					bHasStamp ? StoredVersion : -1, CurrentVersion);
				bVersionMismatch = true;
			}
		}

		if (!bTableExists || bVersionMismatch)
		{
			// Drop the RO handle so the indexer's RW open does not contend
			// with our reader, then reopen RO once the indexer has closed.
			Module->ResetCachedQueryDb();

			FString IndexerStatus;
			FMonolithReflectionIntelModule::RunDecisionIndexerOnce(IndexerStatus);

			DB = Module->GetOrOpenCachedQueryDb();
			if (!DB) { return nullptr; }
		}
	}

	return DB;
}

// ============================================================================
// Handlers
// ============================================================================

FMonolithActionResult FDecisionQueryAdapter::HandleListDecisions(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString PathFilter   = Params->HasField(TEXT("path_filter"))    ? Params->GetStringField(TEXT("path_filter"))    : FString();
	const double  MinConfidence = Params->HasField(TEXT("min_confidence")) ? Params->GetNumberField(TEXT("min_confidence")) : 0.6;
	const FString StatusFilter = Params->HasField(TEXT("status"))         ? Params->GetStringField(TEXT("status"))         : FString();
	const int32   ReqLimit     = Params->HasField(TEXT("limit"))          ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn     = Params->HasField(TEXT("cursor"))         ? Params->GetStringField(TEXT("cursor"))         : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = ComputeFilterHash(PathFilter, MinConfidence, StatusFilter);

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

	// Build dynamic WHERE. Bind parameters in stable order.
	FString WhereSql = TEXT("WHERE confidence >= ?");
	if (!PathFilter.IsEmpty()) { WhereSql += TEXT(" AND source_path LIKE ?"); }
	if (!StatusFilter.IsEmpty()) { WhereSql += TEXT(" AND status = ?"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT %s FROM decision_records %s ORDER BY source_path, source_line LIMIT ? OFFSET ?;"),
		kSelectColumns, *WhereSql);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (decision_records absent?)."));
	}

	int32 BindIdx = 1;
	Stmt.SetBindingValueByIndex(BindIdx++, MinConfidence);
	if (!PathFilter.IsEmpty())
	{
		const FString Like = FString(TEXT("%")) + PathFilter + TEXT("%");
		Stmt.SetBindingValueByIndex(BindIdx++, Like);
	}
	if (!StatusFilter.IsEmpty())
	{
		Stmt.SetBindingValueByIndex(BindIdx++, StatusFilter);
	}
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		Rows.Add(MakeShared<FJsonValueObject>(RowToJson(Stmt)));
	}

	TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
	ResultObj->SetArrayField(TEXT("decisions"), Rows);

	// Page-0 only: issue COUNT(*) for total_estimate.
	if (!bHasCursor)
	{
		const FString CountSql = FString::Printf(
			TEXT("SELECT COUNT(*) FROM decision_records %s;"), *WhereSql);
		FSQLitePreparedStatement CountStmt;
		if (CountStmt.Create(*DB, *CountSql))
		{
			int32 CIdx = 1;
			CountStmt.SetBindingValueByIndex(CIdx++, MinConfidence);
			if (!PathFilter.IsEmpty())
			{
				const FString Like = FString(TEXT("%")) + PathFilter + TEXT("%");
				CountStmt.SetBindingValueByIndex(CIdx++, Like);
			}
			if (!StatusFilter.IsEmpty())
			{
				CountStmt.SetBindingValueByIndex(CIdx++, StatusFilter);
			}
			if (CountStmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				int32 Total = 0;
				CountStmt.GetColumnValueByIndex(0, Total);
				CachedTotal = Total;
				ResultObj->SetNumberField(TEXT("total_estimate"), CachedTotal);
			}
		}
	}

	// Emit next_cursor only if this page was full AND the next slice would
	// not exceed the table count we know about.
	const bool bShortPage = Rows.Num() < Limit;
	if (!bShortPage)
	{
		FRICursorState Out;
		Out.QueryHash = FilterHash;
		Out.Page = Page + 1;
		Out.CachedTotalEstimate = CachedTotal;
		ResultObj->SetStringField(TEXT("next_cursor"), EncodeRICursor(Out));
	}

	return FMonolithActionResult::Success(ResultObj);
}

FMonolithActionResult FDecisionQueryAdapter::HandleGetDecision(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const FString DecisionId = Params->GetStringField(TEXT("decision_id"));
	if (DecisionId.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`decision_id` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	const FString Sql = FString::Printf(
		TEXT("SELECT %s FROM decision_records WHERE decision_id = ? LIMIT 1;"),
		kSelectColumns);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	Stmt.SetBindingValueByIndex(1, DecisionId);

	if (Stmt.Step() != ESQLitePreparedStatementStepResult::Row)
	{
		TSharedPtr<FJsonObject> Empty = MakeShared<FJsonObject>();
		Empty->SetField(TEXT("decision"), MakeShared<FJsonValueNull>());
		return FMonolithActionResult::Success(Empty);
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetObjectField(TEXT("decision"), RowToJson(Stmt));
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FDecisionQueryAdapter::HandleListStale(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const int32 MaxAgeDays = Params->HasField(TEXT("max_age_days"))
		? static_cast<int32>(Params->GetNumberField(TEXT("max_age_days"))) : 0;
	if (MaxAgeDays <= 0)
	{
		return FMonolithActionResult::Error(TEXT("`max_age_days` must be positive."),
			FMonolithJsonUtils::ErrInvalidParams);
	}
	const FString PathFilter = Params->HasField(TEXT("path_filter"))
		? Params->GetStringField(TEXT("path_filter")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);

	const int64 CutoffUnix = FDateTime::UtcNow().ToUnixTimestamp()
		- (static_cast<int64>(MaxAgeDays) * 24LL * 60LL * 60LL);

	const uint32 FilterHash = ComputeFilterHash(
		PathFilter, static_cast<double>(MaxAgeDays), TEXT("__stale__"));

	int32 Page = 0;
	if (!CursorIn.IsEmpty())
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

	FString WhereSql = TEXT("WHERE source_mtime > 0 AND source_mtime < ?");
	if (!PathFilter.IsEmpty()) { WhereSql += TEXT(" AND source_path LIKE ?"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT %s FROM decision_records %s ORDER BY source_mtime ASC LIMIT ? OFFSET ?;"),
		kSelectColumns, *WhereSql);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}

	int32 BindIdx = 1;
	Stmt.SetBindingValueByIndex(BindIdx++, CutoffUnix);
	if (!PathFilter.IsEmpty())
	{
		const FString Like = FString(TEXT("%")) + PathFilter + TEXT("%");
		Stmt.SetBindingValueByIndex(BindIdx++, Like);
	}
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		Rows.Add(MakeShared<FJsonValueObject>(RowToJson(Stmt)));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("stale_decisions"), Rows);
	Out->SetNumberField(TEXT("cutoff_unix"), static_cast<double>(CutoffUnix));

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

FMonolithActionResult FDecisionQueryAdapter::HandleFindSupersessionChain(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const FString StartId = Params->GetStringField(TEXT("decision_id"));
	if (StartId.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`decision_id` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}
	const int32 ReqDepth = Params->HasField(TEXT("depth"))
		? static_cast<int32>(Params->GetNumberField(TEXT("depth"))) : 10;
	const int32 MaxDepth = FMath::Clamp(ReqDepth, 1, 50);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT to_decision_id FROM decision_supersedes WHERE from_decision_id = ?;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}

	TArray<TSharedPtr<FJsonValue>> ChainArr;
	TArray<FString> Frontier;
	TSet<FString> Visited;
	Frontier.Add(StartId);
	Visited.Add(StartId);

	int32 Depth = 0;
	while (!Frontier.IsEmpty() && Depth < MaxDepth)
	{
		TArray<FString> NextFrontier;
		for (const FString& From : Frontier)
		{
			Stmt.Reset();
			Stmt.ClearBindings();
			Stmt.SetBindingValueByIndex(1, From);
			while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
			{
				FString To;
				Stmt.GetColumnValueByIndex(0, To);
				if (Visited.Contains(To)) { continue; }
				Visited.Add(To);

				TSharedPtr<FJsonObject> Edge = MakeShared<FJsonObject>();
				Edge->SetStringField(TEXT("from"), From);
				Edge->SetStringField(TEXT("to"),   To);
				Edge->SetNumberField(TEXT("depth"), Depth + 1);
				ChainArr.Add(MakeShared<FJsonValueObject>(Edge));
				NextFrontier.Add(To);
			}
		}
		Frontier = MoveTemp(NextFrontier);
		++Depth;
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetStringField(TEXT("start"), StartId);
	Out->SetArrayField(TEXT("chain"), ChainArr);
	Out->SetBoolField(TEXT("truncated"), !Frontier.IsEmpty());
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FDecisionQueryAdapter::HandleFindReferentDecisions(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const FString DecisionId = Params->GetStringField(TEXT("decision_id"));
	if (DecisionId.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`decision_id` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT r.decision_id, r.title, r.status, r.source_path, r.source_line, "
		"       r.confidence, r.rationale, r.source_mtime "
		"FROM decision_supersedes s "
		"JOIN decision_records r ON r.decision_id = s.from_decision_id "
		"WHERE s.to_decision_id = ? "
		"ORDER BY r.source_path, r.source_line;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	Stmt.SetBindingValueByIndex(1, DecisionId);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		Rows.Add(MakeShared<FJsonValueObject>(RowToJson(Stmt)));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetStringField(TEXT("decision_id"), DecisionId);
	Out->SetArrayField(TEXT("referent_decisions"), Rows);
	return FMonolithActionResult::Success(Out);
}
