// SPDX-License-Identifier: MIT
// Plan: Plugins/Monolith/Docs/plans/2026-05-28-reflection-intelligence.md (Phase 2 — v0.17.0).
//
// Internal-only schema accessors for the Phase 2 risk + conditional-gate tables.
// Lives under Private/ — no other module needs these raw SQL strings; they exist
// so the indexer .cpp files and any future migration script share one source of
// truth. Mirrors the Phase 1 DecisionSchema.h pattern exactly.

#pragma once

#include "CoreMinimal.h"

namespace MonolithRiskSchema
{
	// Four new tables introduced in Phase 2:
	//   git_cochange_pairs       — symmetric file co-change weights per repo
	//   git_file_churn           — per-file commit-touch counts per repo
	//   risk_hotspot_scores      — churn × complexity composite scores
	//   reflect_conditional_gates — `#if WITH_*` / `bHas*` probe sweep results
	const TCHAR* GetCreateCoChangePairsTableSQL();
	const TCHAR* GetCreateFileChurnTableSQL();
	const TCHAR* GetCreateHotspotScoresTableSQL();
	const TCHAR* GetCreateConditionalGatesTableSQL();

	// Helper indices (nice-to-have, non-fatal if they fail).
	const TCHAR* GetCreateCoChangePairsIndexFileASQL();
	const TCHAR* GetCreateCoChangePairsIndexFileBSQL();
	const TCHAR* GetCreateFileChurnIndexPathSQL();
	const TCHAR* GetCreateHotspotScoresIndexScoreSQL();
	const TCHAR* GetCreateConditionalGatesIndexMacroSQL();
}
