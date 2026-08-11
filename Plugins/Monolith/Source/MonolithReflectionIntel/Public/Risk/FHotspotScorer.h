// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// FHotspotScorer — composite churn × complexity scorer. Reads `git_file_churn`
// (Phase 2 GitCoChangeIndexer output) and the existing `files` table (Monolith
// source indexer — `line_count` is the complexity proxy in Phase 2) and writes
// the join into `risk_hotspot_scores`. Plain C++ worker. Idempotent: wipes +
// rewrites the table on each Run().
//
// Threading: invoked from the game thread following GitCoChangeIndexer (same
// lazy-bootstrap path). All SQLite ops on the supplied DB handle.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Map.h"

class FSQLiteDatabase;

class MONOLITHREFLECTIONINTEL_API FHotspotScorer
{
public:
	/**
	 * Compute hotspot scores joining churn × complexity for every file with
	 * both signals. Writes `risk_hotspot_scores`. Returns true on full success.
	 *
	 * @param DB         Open writable handle. Caller has enforced
	 *                   `PRAGMA journal_mode=DELETE`.
	 * @param OutStatus  One-line summary.
	 */
	bool Run(FSQLiteDatabase& DB, FString& OutStatus);

private:
	bool EnsureSchema(FSQLiteDatabase& DB);

	struct FFileSignals
	{
		int32 ChurnCount = 0;
		int32 ComplexityProxy = 0; // line_count from MonolithSource.files
	};

	bool LoadChurn(FSQLiteDatabase& DB, TMap<FString, FFileSignals>& InOut);
	bool LoadComplexity(FSQLiteDatabase& DB, TMap<FString, FFileSignals>& InOut);
	bool WriteScores(FSQLiteDatabase& DB, const TMap<FString, FFileSignals>& Signals);
};
