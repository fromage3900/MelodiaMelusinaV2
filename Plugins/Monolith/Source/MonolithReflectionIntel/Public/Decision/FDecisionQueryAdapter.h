// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 1).
//
// FDecisionQueryAdapter — registers the `decision_query` namespace (5 actions)
// against the central FMonolithToolRegistry. Pure read-only handlers; no
// indexing happens here (that's FDecisionRecordIndexer's job).
//
// v0.17.0 ergonomics adoption:
//   - `path_filter` params tagged EMonolithParamKind::DiskPath (auto `\`→`/`).
//   - Dispatcher annotated readOnlyHint=true via SetDispatcherAnnotations.
//   - `list_decisions` adopts cursor pagination via MonolithCursorCodec.
//   - Response shaping (_fields/_omit/_compact_json) participates automatically
//     via the registry's dispatch path — no per-action shaping code.
//   - Fuzzy-match suggestions on unknown actions emerge for free.

#pragma once

#include "CoreMinimal.h"
#include "MonolithToolRegistry.h"

class MONOLITHREFLECTIONINTEL_API FDecisionQueryAdapter
{
public:
	/** Register all 5 decision_query actions + dispatcher annotations. */
	static void RegisterActions(FMonolithToolRegistry& Registry);

private:
	// --- Action handlers ---
	static FMonolithActionResult HandleListDecisions(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleGetDecision(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleListStale(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindSupersessionChain(const TSharedPtr<FJsonObject>& Params);
	static FMonolithActionResult HandleFindReferentDecisions(const TSharedPtr<FJsonObject>& Params);

	// --- Shared DB accessor ---
	static class FSQLiteDatabase* GetRawDB();
};
