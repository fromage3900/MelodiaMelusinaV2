// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 4a — v0.17.0).
//
// FPipelineAdapter — implementation. Two pure-composition handlers that fan
// out to multiple namespaces' actions through FMonolithToolRegistry::ExecuteAction
// and assemble a single envelope.
//
// Composers DO NOT write to any table. They tolerate any individual sub-call
// failing — failed sections appear in the envelope as `{ "error": "..." }` so
// the caller sees which check tripped without losing the rest.

#include "Pipeline/FPipelineAdapter.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "MonolithJsonUtils.h"
#include "MonolithParamSchema.h"

namespace
{
	/** Wrap an action call. On success the result object is returned verbatim;
	 *  on failure a small `{ "error": "<msg>", "code": <int> }` envelope is
	 *  returned so the parent composer can surface section-level failures
	 *  without aborting the whole composer.
	 */
	TSharedPtr<FJsonObject> CallSection(const FString& Namespace, const FString& Action,
		const TSharedPtr<FJsonObject>& Params)
	{
		FMonolithActionResult R = FMonolithToolRegistry::Get().ExecuteAction(
			Namespace, Action, Params);
		if (R.bSuccess && R.Result.IsValid())
		{
			return R.Result;
		}
		TSharedPtr<FJsonObject> ErrObj = MakeShared<FJsonObject>();
		ErrObj->SetStringField(TEXT("error"), R.ErrorMessage);
		ErrObj->SetNumberField(TEXT("code"), R.ErrorCode);
		return ErrObj;
	}

	/** Build a fresh, single-key Params object — convenience for one-arg
	 *  fan-out calls.
	 */
	TSharedPtr<FJsonObject> ParamsWithString(const FString& Key, const FString& Value)
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		P->SetStringField(Key, Value);
		return P;
	}
}

// ============================================================================
// Registration
// ============================================================================

void FPipelineAdapter::RegisterActions(FMonolithToolRegistry& Registry)
{
	// ---- pipeline_query("pr_review") ----
	Registry.RegisterAction(TEXT("pipeline"), TEXT("pr_review"),
		TEXT("Composer: PR-review report. For each file in `changed_files`, "
		     "compose the following checks into a single envelope:\n"
		     "  - risk_query(\"get_cochange_pairs\") — flags hidden coupling\n"
		     "  - risk_query(\"get_file_churn\") — per-file churn signal\n"
		     "  - decision_query(\"list_decisions\") with path_filter — surfaces "
		     "any architectural decisions whose source markdown matches the changed file\n"
		     "  - source_query(\"audit_module_dep_reality\") — flags missing Build.cs deps "
		     "(project-wide, run once)\n"
		     "  - blueprint_query(\"audit_cdo_drift\") — flags BP CDO drift "
		     "(project-wide, run once)\n"
		     "Returns one section per check. Read-only."),
		FMonolithActionHandler::CreateStatic(&FPipelineAdapter::HandlePRReview),
		FParamSchemaBuilder()
			.Required(TEXT("changed_files"), TEXT("array"),
				TEXT("Array of project-relative file paths (forward-slashed) — the PR's scope"))
			.Build());

	// ---- pipeline_query("release_readiness") ----
	Registry.RegisterAction(TEXT("pipeline"), TEXT("release_readiness"),
		TEXT("Composer: release pre-flight envelope. Composes:\n"
		     "  • monolith_status — current action count + module status\n"
		     "  • decision_query(\"list_stale\") — surfaces stale governance decisions\n"
		     "  • risk_query(\"get_release_window_hotspots\") — recent-window risk surfaces\n"
		     "  • risk_query(\"list_conditional_gates\") — sentinel-discipline view of "
		     "current conditional gating state\n"
		     "  • source_query(\"audit_module_dep_reality\") — missing Build.cs deps\n"
		     "Read-only + idempotent."),
		FMonolithActionHandler::CreateStatic(&FPipelineAdapter::HandleReleaseReadiness),
		FParamSchemaBuilder()
			.Optional(TEXT("target_release"), TEXT("string"),
				TEXT("Optional release tag label (e.g. 'v0.17.0'). Echoed back in the envelope."))
			.Build());

	FMonolithDispatcherAnnotations Anno;
	Anno.bReadOnlyHint    = true;
	Anno.bDestructiveHint = false;
	Anno.bIdempotentHint  = true;
	Anno.Title = TEXT("Composer pipelines (PR review, release readiness)");
	Registry.SetDispatcherAnnotations(TEXT("pipeline"), Anno);
}

// ============================================================================
// Handler — pipeline_query("pr_review")
// ============================================================================

FMonolithActionResult FPipelineAdapter::HandlePRReview(const TSharedPtr<FJsonObject>& Params)
{
	if (!Params.IsValid() || !Params->HasField(TEXT("changed_files")))
	{
		return FMonolithActionResult::Error(
			TEXT("`changed_files` is required (array of project-relative file paths)."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	const TArray<TSharedPtr<FJsonValue>>* ChangedFiles = nullptr;
	if (!Params->TryGetArrayField(TEXT("changed_files"), ChangedFiles)
	    || !ChangedFiles
	    || ChangedFiles->Num() == 0)
	{
		return FMonolithActionResult::Error(
			TEXT("`changed_files` must be a non-empty array."),
			FMonolithJsonUtils::ErrInvalidParams);
	}

	TSharedPtr<FJsonObject> Envelope = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> EchoArr;
	for (const TSharedPtr<FJsonValue>& V : *ChangedFiles)
	{
		if (V.IsValid()) { EchoArr.Add(V); }
	}
	Envelope->SetArrayField(TEXT("changed_files"), EchoArr);

	// Per-file sections.
	TArray<TSharedPtr<FJsonValue>> PerFile;
	for (const TSharedPtr<FJsonValue>& V : *ChangedFiles)
	{
		if (!V.IsValid()) { continue; }
		FString FilePath;
		if (!V->TryGetString(FilePath) || FilePath.IsEmpty()) { continue; }

		TSharedPtr<FJsonObject> FileSection = MakeShared<FJsonObject>();
		FileSection->SetStringField(TEXT("file"), FilePath);

		// risk_query("get_cochange_pairs") expects { "file_path": "..." }.
		{
			TSharedPtr<FJsonObject> P = ParamsWithString(TEXT("file_path"), FilePath);
			FileSection->SetObjectField(TEXT("cochange_pairs"),
				CallSection(TEXT("risk"), TEXT("get_cochange_pairs"), P));
		}
		// risk_query("get_file_churn") — per-file churn signal.
		{
			TSharedPtr<FJsonObject> P = ParamsWithString(TEXT("file_path"), FilePath);
			FileSection->SetObjectField(TEXT("file_churn"),
				CallSection(TEXT("risk"), TEXT("get_file_churn"), P));
		}
		// decision_query("list_decisions") with path_filter substring matches
		// against decision source_path; using the changed file as the filter
		// surfaces any decision documents that touch this path.
		{
			TSharedPtr<FJsonObject> P = ParamsWithString(TEXT("path_filter"), FilePath);
			FileSection->SetObjectField(TEXT("decisions_matching_path"),
				CallSection(TEXT("decision"), TEXT("list_decisions"), P));
		}

		PerFile.Add(MakeShared<FJsonValueObject>(FileSection));
	}
	Envelope->SetArrayField(TEXT("per_file"), PerFile);

	// Project-wide sections — composed once, not per file.
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		Envelope->SetObjectField(TEXT("module_dep_reality"),
			CallSection(TEXT("source"), TEXT("audit_module_dep_reality"), P));
	}
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		Envelope->SetObjectField(TEXT("cdo_drift"),
			CallSection(TEXT("blueprint"), TEXT("audit_cdo_drift"), P));
	}

	return FMonolithActionResult::Success(Envelope);
}

// ============================================================================
// Handler — pipeline_query("release_readiness")
// ============================================================================

FMonolithActionResult FPipelineAdapter::HandleReleaseReadiness(const TSharedPtr<FJsonObject>& Params)
{
	const FString TargetRelease = Params.IsValid() && Params->HasField(TEXT("target_release"))
		? Params->GetStringField(TEXT("target_release")) : FString();

	TSharedPtr<FJsonObject> Envelope = MakeShared<FJsonObject>();
	if (!TargetRelease.IsEmpty())
	{
		Envelope->SetStringField(TEXT("target_release"), TargetRelease);
	}

	// monolith_status — server health, version, module status.
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		Envelope->SetObjectField(TEXT("monolith_status"),
			CallSection(TEXT("monolith"), TEXT("status"), P));
	}

	// decision_query("list_stale") — surfaces decisions whose source markdown
	// has not been modified in the last 90 days. Required `max_age_days`
	// param defaulted to 90; callers can re-invoke directly if they want a
	// different window.
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		P->SetNumberField(TEXT("max_age_days"), 90);
		Envelope->SetObjectField(TEXT("stale_decisions"),
			CallSection(TEXT("decision"), TEXT("list_stale"), P));
	}

	// risk_query("get_release_window_hotspots") — risk surfaces in the recent
	// commit window.
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		Envelope->SetObjectField(TEXT("release_window_hotspots"),
			CallSection(TEXT("risk"), TEXT("get_release_window_hotspots"), P));
	}

	// risk_query("list_conditional_gates") — sentinel-discipline view.
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		Envelope->SetObjectField(TEXT("conditional_gates"),
			CallSection(TEXT("risk"), TEXT("list_conditional_gates"), P));
	}

	// source_query("audit_module_dep_reality") — Build.cs / source dep
	// reality check.
	{
		TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
		Envelope->SetObjectField(TEXT("module_dep_reality"),
			CallSection(TEXT("source"), TEXT("audit_module_dep_reality"), P));
	}

	return FMonolithActionResult::Success(Envelope);
}
