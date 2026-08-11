// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FRiskQueryAdapter — implementation. Five read-only handlers over the Phase 2
// risk tables. All run on the game thread. Cursor codec mirrored from the
// Phase 1 decision adapter; consolidating into MonolithCore is a Phase 5+
// item and out of scope.

#include "Risk/FRiskQueryAdapter.h"
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

	/** Forward-slash + lowercase the path so cursor hashes are stable across input forms. */
	FString CanonPath(const FString& In)
	{
		FString Out = In;
		Out.ReplaceInline(TEXT("\\"), TEXT("/"));
		return Out;
	}
}

// ============================================================================
// Registration
// ============================================================================

void FRiskQueryAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- get_hotspot_score ----
	Registry.RegisterAction(TEXT("risk"), TEXT("get_hotspot_score"),
		TEXT("Look up the composite churn × complexity hotspot score for a file. "
		     "`file_path` is project-relative (forward slashes recommended). "
		     "Returns null if the file is not in the score index."),
		FMonolithActionHandler::CreateStatic(&FRiskQueryAdapter::HandleGetHotspotScore),
		FParamSchemaBuilder()
			.RequiredDiskPath(TEXT("file_path"),
				TEXT("Project-relative source file path"))
			.Build());

	// ---- get_cochange_pairs ----
	Registry.RegisterAction(TEXT("risk"), TEXT("get_cochange_pairs"),
		TEXT("List files that historically co-change with `file_path`, ranked "
		     "by co-change count descending. Mines from `git_cochange_pairs` "
		     "(populated by FGitCoChangeIndexer). Supports cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FRiskQueryAdapter::HandleGetCoChangePairs),
		FParamSchemaBuilder()
			.RequiredDiskPath(TEXT("file_path"),
				TEXT("Project-relative source file path"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor from a prior `next_cursor`"))
			.Build());

	// ---- get_file_churn ----
	Registry.RegisterAction(TEXT("risk"), TEXT("get_file_churn"),
		TEXT("Report per-repo commit-touch count + last-touched Unix timestamp "
		     "for `file_path`."),
		FMonolithActionHandler::CreateStatic(&FRiskQueryAdapter::HandleGetFileChurn),
		FParamSchemaBuilder()
			.RequiredDiskPath(TEXT("file_path"),
				TEXT("Project-relative source file path"))
			.Optional(TEXT("repo_tag"), TEXT("string"),
				TEXT("Optional repo tag filter (e.g. \"Monolith\", \"Resonance\")"))
			.Build());

	// ---- get_release_window_hotspots ----
	Registry.RegisterAction(TEXT("risk"), TEXT("get_release_window_hotspots"),
		TEXT("Top hotspot files touched within the release window (since the "
		     "given Unix timestamp). Useful for prioritising review attention "
		     "before a tag. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FRiskQueryAdapter::HandleGetReleaseWindowHotspots),
		FParamSchemaBuilder()
			.Optional(TEXT("since_unix"), TEXT("integer"),
				TEXT("Unix timestamp lower bound (default = 30 days ago)"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// ---- list_conditional_gates ----
	// DEVIATION from plan §7 — 5th action surfacing reflect_conditional_gates;
	// see header comment for rationale.
	Registry.RegisterAction(TEXT("risk"), TEXT("list_conditional_gates"),
		TEXT("List `#if WITH_*` conditional sites and `bHas*` Build.cs probes. "
		     "Useful for auditing conditional-gating discipline. Cursor pagination."),
		FMonolithActionHandler::CreateStatic(&FRiskQueryAdapter::HandleListConditionalGates),
		FParamSchemaBuilder()
			.Optional(TEXT("macro_filter"), TEXT("string"),
				TEXT("Substring match on macro_name (e.g. \"WITH_GBA\")"))
			.OptionalDiskPath(TEXT("path_filter"),
				TEXT("Substring match on source_path"))
			.Optional(TEXT("limit"), TEXT("integer"),
				TEXT("Max rows per page (default 50, hard cap 200)"), TEXT("50"))
			.Optional(TEXT("cursor"), TEXT("string"),
				TEXT("Opaque pagination cursor"))
			.Build());

	// Dispatcher annotation — all five handlers are pure SELECT against the
	// risk tables. Same shape as Phase 1's decision dispatcher annotation.
	FMonolithDispatcherAnnotations Anno;
	Anno.bReadOnlyHint   = true;
	Anno.bDestructiveHint = false;
	Anno.bIdempotentHint = true;
	Anno.Title = TEXT("Risk + co-change query");
	Registry.SetDispatcherAnnotations(TEXT("risk"), Anno);
}

// ============================================================================
// DB accessor — lazy bootstrap of the risk tables on first call.
// ============================================================================

FSQLiteDatabase* FRiskQueryAdapter::GetRawDB()
{
	// Thread-safety contract (matches FNetworkQueryAdapter and the other RI
	// adapters): the borrowed EngineSource.db handle is game-thread-only. The
	// subsystem's handle close runs on the game thread (its reindex trigger is
	// game-thread-dispatched), so game-thread-only reads serialise against that
	// close without a per-read lock.
	ensure(IsInGameThread());

	FMonolithReflectionIntelModule* Module =
		FModuleManager::GetModulePtr<FMonolithReflectionIntelModule>(
			TEXT("MonolithReflectionIntel"));
	if (!Module) { return nullptr; }

	FSQLiteDatabase* DB = Module->GetOrOpenCachedQueryDb();
	if (!DB) { return nullptr; }

	if (!Module->HasAttemptedRiskBootstrap())
	{
		Module->MarkRiskBootstrapAttempted();
		FSQLitePreparedStatement TableCheck;
		const bool bPrepared = TableCheck.Create(*DB,
			TEXT("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_hotspot_scores';"));
		const bool bTableExists = bPrepared
			&& TableCheck.Step() == ESQLitePreparedStatementStepResult::Row;
		TableCheck.Destroy();

		// Handover doc item #1 — stale detection.
		bool bVersionMismatch = false;
		if (bTableExists)
		{
			int32 StoredVersion = 0;
			const bool bHasStamp = MonolithRIMeta::ReadStoredVersion(
				*DB, TEXT("risk"), StoredVersion);
			const int32 CurrentVersion = MonolithRIMeta::GetIndexerCodeVersion(TEXT("risk"));
			if (!bHasStamp || StoredVersion != CurrentVersion)
			{
				UE_LOG(LogMonolithReflectionIntel, Log,
					TEXT("risk: stale-detection triggered (stored=%d, current=%d) — forcing rebuild"),
					bHasStamp ? StoredVersion : -1, CurrentVersion);
				bVersionMismatch = true;
			}
		}

		if (!bTableExists || bVersionMismatch)
		{
			Module->ResetCachedQueryDb();
			FString IndexerStatus;
			FMonolithReflectionIntelModule::RunRiskIndexersOnce(IndexerStatus);
			DB = Module->GetOrOpenCachedQueryDb();
			if (!DB) { return nullptr; }
		}
	}
	return DB;
}

// ============================================================================
// Handlers
// ============================================================================

FMonolithActionResult FRiskQueryAdapter::HandleGetHotspotScore(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB)
	{
		return FMonolithActionResult::Error(
			TEXT("EngineSource.db not available. Run source.trigger_reindex to bootstrap."));
	}

	const FString FilePath = CanonPath(Params->GetStringField(TEXT("file_path")));
	if (FilePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`file_path` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT file_path, churn, complexity_proxy, normalised_churn, "
		"       normalised_complexity, score "
		"FROM risk_hotspot_scores WHERE file_path = ? LIMIT 1;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (risk_hotspot_scores absent?)."));
	}
	Stmt.SetBindingValueByIndex(1, FilePath);

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	if (Stmt.Step() != ESQLitePreparedStatementStepResult::Row)
	{
		Out->SetField(TEXT("hotspot"), MakeShared<FJsonValueNull>());
		return FMonolithActionResult::Success(Out);
	}

	FString Path;
	int32 Churn = 0, Cmplx = 0;
	double NChurn = 0.0, NCmplx = 0.0, Score = 0.0;
	Stmt.GetColumnValueByIndex(0, Path);
	Stmt.GetColumnValueByIndex(1, Churn);
	Stmt.GetColumnValueByIndex(2, Cmplx);
	Stmt.GetColumnValueByIndex(3, NChurn);
	Stmt.GetColumnValueByIndex(4, NCmplx);
	Stmt.GetColumnValueByIndex(5, Score);

	TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
	Row->SetStringField(TEXT("file_path"), Path);
	Row->SetNumberField(TEXT("churn"), Churn);
	Row->SetNumberField(TEXT("complexity_proxy"), Cmplx);
	Row->SetNumberField(TEXT("normalised_churn"), NChurn);
	Row->SetNumberField(TEXT("normalised_complexity"), NCmplx);
	Row->SetNumberField(TEXT("score"), Score);
	Out->SetObjectField(TEXT("hotspot"), Row);
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FRiskQueryAdapter::HandleGetCoChangePairs(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const FString FilePath = CanonPath(Params->GetStringField(TEXT("file_path")));
	if (FilePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`file_path` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ FilePath });

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

	// Pairs are stored undirected with file_a < file_b. To find all partners of
	// `FilePath`, we OR the two sides of the pair.
	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT repo_tag, "
		"  CASE WHEN file_a = ? THEN file_b ELSE file_a END AS partner, "
		"  count "
		"FROM git_cochange_pairs "
		"WHERE file_a = ? OR file_b = ? "
		"ORDER BY count DESC, partner ASC "
		"LIMIT ? OFFSET ?;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (git_cochange_pairs absent?)."));
	}
	int32 BindIdx = 1;
	Stmt.SetBindingValueByIndex(BindIdx++, FilePath); // CASE arm
	Stmt.SetBindingValueByIndex(BindIdx++, FilePath); // OR file_a
	Stmt.SetBindingValueByIndex(BindIdx++, FilePath); // OR file_b
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString Repo, Partner;
		int32 Count = 0;
		Stmt.GetColumnValueByIndex(0, Repo);
		Stmt.GetColumnValueByIndex(1, Partner);
		Stmt.GetColumnValueByIndex(2, Count);

		TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
		Row->SetStringField(TEXT("repo_tag"), Repo);
		Row->SetStringField(TEXT("partner"), Partner);
		Row->SetNumberField(TEXT("count"), Count);
		Rows.Add(MakeShared<FJsonValueObject>(Row));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetStringField(TEXT("file_path"), FilePath);
	Out->SetArrayField(TEXT("partners"), Rows);

	if (!bHasCursor)
	{
		FSQLitePreparedStatement CountStmt;
		if (CountStmt.Create(*DB, TEXT(
			"SELECT COUNT(*) FROM git_cochange_pairs WHERE file_a = ? OR file_b = ?;")))
		{
			CountStmt.SetBindingValueByIndex(1, FilePath);
			CountStmt.SetBindingValueByIndex(2, FilePath);
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

FMonolithActionResult FRiskQueryAdapter::HandleGetFileChurn(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const FString FilePath = CanonPath(Params->GetStringField(TEXT("file_path")));
	if (FilePath.IsEmpty())
	{
		return FMonolithActionResult::Error(TEXT("`file_path` is required."),
			FMonolithJsonUtils::ErrInvalidParams);
	}
	const FString RepoTag = Params->HasField(TEXT("repo_tag"))
		? Params->GetStringField(TEXT("repo_tag")) : FString();

	FString Sql = TEXT("SELECT repo_tag, commit_count, last_touched FROM git_file_churn WHERE file_path = ?");
	if (!RepoTag.IsEmpty()) { Sql += TEXT(" AND repo_tag = ?"); }
	Sql += TEXT(";");

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (git_file_churn absent?)."));
	}
	int32 BindIdx = 1;
	Stmt.SetBindingValueByIndex(BindIdx++, FilePath);
	if (!RepoTag.IsEmpty()) { Stmt.SetBindingValueByIndex(BindIdx++, RepoTag); }

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString Repo;
		int32 Count = 0;
		int64 Last = 0;
		Stmt.GetColumnValueByIndex(0, Repo);
		Stmt.GetColumnValueByIndex(1, Count);
		Stmt.GetColumnValueByIndex(2, Last);

		TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
		Row->SetStringField(TEXT("repo_tag"), Repo);
		Row->SetNumberField(TEXT("commit_count"), Count);
		Row->SetNumberField(TEXT("last_touched_unix"), static_cast<double>(Last));
		Rows.Add(MakeShared<FJsonValueObject>(Row));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetStringField(TEXT("file_path"), FilePath);
	Out->SetArrayField(TEXT("churn_by_repo"), Rows);
	return FMonolithActionResult::Success(Out);
}

FMonolithActionResult FRiskQueryAdapter::HandleGetReleaseWindowHotspots(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const int64 DefaultSince =
		FDateTime::UtcNow().ToUnixTimestamp() - (30LL * 24LL * 60LL * 60LL);
	const int64 Since = Params->HasField(TEXT("since_unix"))
		? static_cast<int64>(Params->GetNumberField(TEXT("since_unix"))) : DefaultSince;

	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ FString::FromInt(Since) });

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

	// Join hotspots × churn-last_touched. A file qualifies if ANY repo
	// touched it after `Since`. We aggregate via MAX(last_touched) per file.
	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, TEXT(
		"SELECT h.file_path, h.score, h.churn, h.complexity_proxy, "
		"       (SELECT MAX(c.last_touched) FROM git_file_churn c "
		"        WHERE c.file_path = h.file_path) AS last_touched "
		"FROM risk_hotspot_scores h "
		"WHERE (SELECT MAX(c2.last_touched) FROM git_file_churn c2 "
		"       WHERE c2.file_path = h.file_path) >= ? "
		"ORDER BY h.score DESC "
		"LIMIT ? OFFSET ?;")))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed."));
	}
	Stmt.SetBindingValueByIndex(1, Since);
	Stmt.SetBindingValueByIndex(2, Limit);
	Stmt.SetBindingValueByIndex(3, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		FString Path;
		double Score = 0.0;
		int32 Churn = 0, Cmplx = 0;
		int64 Last = 0;
		Stmt.GetColumnValueByIndex(0, Path);
		Stmt.GetColumnValueByIndex(1, Score);
		Stmt.GetColumnValueByIndex(2, Churn);
		Stmt.GetColumnValueByIndex(3, Cmplx);
		Stmt.GetColumnValueByIndex(4, Last);

		TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
		Row->SetStringField(TEXT("file_path"), Path);
		Row->SetNumberField(TEXT("score"), Score);
		Row->SetNumberField(TEXT("churn"), Churn);
		Row->SetNumberField(TEXT("complexity_proxy"), Cmplx);
		Row->SetNumberField(TEXT("last_touched_unix"), static_cast<double>(Last));
		Rows.Add(MakeShared<FJsonValueObject>(Row));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetNumberField(TEXT("since_unix"), static_cast<double>(Since));
	Out->SetArrayField(TEXT("hotspots"), Rows);

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

FMonolithActionResult FRiskQueryAdapter::HandleListConditionalGates(const TSharedPtr<FJsonObject>& Params)
{
	FSQLiteDatabase* DB = GetRawDB();
	if (!DB) { return FMonolithActionResult::Error(TEXT("EngineSource.db not available.")); }

	const FString MacroFilter = Params->HasField(TEXT("macro_filter"))
		? Params->GetStringField(TEXT("macro_filter")) : FString();
	const FString PathFilter = Params->HasField(TEXT("path_filter"))
		? Params->GetStringField(TEXT("path_filter")) : FString();
	const int32 ReqLimit = Params->HasField(TEXT("limit"))
		? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 50;
	const FString CursorIn = Params->HasField(TEXT("cursor"))
		? Params->GetStringField(TEXT("cursor")) : FString();

	constexpr int32 HARD_CAP = 200;
	const int32 Limit = FMath::Clamp(ReqLimit, 1, HARD_CAP);
	const uint32 FilterHash = RIComputeFilterHash({ MacroFilter, PathFilter });

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

	FString WhereSql = TEXT("WHERE 1=1");
	if (!MacroFilter.IsEmpty()) { WhereSql += TEXT(" AND macro_name LIKE ?"); }
	if (!PathFilter.IsEmpty())  { WhereSql += TEXT(" AND source_path LIKE ?"); }

	const FString Sql = FString::Printf(
		TEXT("SELECT id, source_path, source_line, macro_name, gate_kind, context_snippet "
			 "FROM reflect_conditional_gates %s "
			 "ORDER BY source_path, source_line "
			 "LIMIT ? OFFSET ?;"),
		*WhereSql);

	FSQLitePreparedStatement Stmt;
	if (!Stmt.Create(*DB, *Sql))
	{
		return FMonolithActionResult::Error(TEXT("SELECT prepare failed (reflect_conditional_gates absent?)."));
	}
	int32 BindIdx = 1;
	if (!MacroFilter.IsEmpty())
	{
		Stmt.SetBindingValueByIndex(BindIdx++, FString(TEXT("%")) + MacroFilter + TEXT("%"));
	}
	if (!PathFilter.IsEmpty())
	{
		Stmt.SetBindingValueByIndex(BindIdx++, FString(TEXT("%")) + PathFilter + TEXT("%"));
	}
	Stmt.SetBindingValueByIndex(BindIdx++, Limit);
	Stmt.SetBindingValueByIndex(BindIdx++, Page * Limit);

	TArray<TSharedPtr<FJsonValue>> Rows;
	while (Stmt.Step() == ESQLitePreparedStatementStepResult::Row)
	{
		int32 Id = 0, Line = 0;
		FString SourcePath, MacroName, GateKind, Snippet;
		Stmt.GetColumnValueByIndex(0, Id);
		Stmt.GetColumnValueByIndex(1, SourcePath);
		Stmt.GetColumnValueByIndex(2, Line);
		Stmt.GetColumnValueByIndex(3, MacroName);
		Stmt.GetColumnValueByIndex(4, GateKind);
		Stmt.GetColumnValueByIndex(5, Snippet);

		TSharedPtr<FJsonObject> Row = MakeShared<FJsonObject>();
		Row->SetNumberField(TEXT("id"), Id);
		Row->SetStringField(TEXT("source_path"), SourcePath);
		Row->SetNumberField(TEXT("source_line"), Line);
		Row->SetStringField(TEXT("macro_name"), MacroName);
		Row->SetStringField(TEXT("gate_kind"), GateKind);
		Row->SetStringField(TEXT("context_snippet"), Snippet);
		Rows.Add(MakeShared<FJsonValueObject>(Row));
	}

	TSharedPtr<FJsonObject> Out = MakeShared<FJsonObject>();
	Out->SetArrayField(TEXT("gates"), Rows);

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
