// SPDX-License-Identifier: MIT
// Survivor C (Action + namespace did_you_mean fuzzy match) — plan §3.C.
// Plan: Plugins/Monolith/Docs/plans/2026-05-27-mcp-llm-ergonomics.md
//
// PRIVATE header (lives under Private/, not Public/). The fuzzy-match scorer
// is an internal helper of the registry; exposing it via a Private/ header is
// enough for MonolithToolRegistry.cpp (same module) and the dev-automation
// test file (also same module) to call it without leaking into MonolithCore's
// public surface.

#pragma once

#include "CoreMinimal.h"
#include "Containers/Array.h"
#include "Containers/UnrealString.h"

namespace MonolithFuzzyMatchDetail
{
	/**
	 * One scored fuzzy-match candidate.
	 *  Key   — the candidate string (action name or namespace name).
	 *  Score — normalised similarity in [0, 1]; 1.0 == exact, lower == more distant.
	 *          Computed as 1.0f - (LevenshteinDistance(Needle, Key) / WorstCase)
	 *          where WorstCase = max(Needle.Len(), Key.Len()). Matches the
	 *          IKRigAutoCharacterizer.cpp:1761 precedent verified at plan time.
	 */
	struct FFuzzyCandidate
	{
		FString Key;
		float Score = 0.0f;
	};

	/**
	 * Score every Key in KeysSnapshot against Needle and return the TopN by
	 * descending Score. Stable order between equal-score candidates is by
	 * insertion order in KeysSnapshot.
	 *
	 * CRITICAL: caller MUST have already dropped any registry lock before
	 * invoking this. The scoring loop is O(N · |Needle| · |Key|) and can
	 * sweep over 1500+ registry keys — holding the lock would block every
	 * concurrent tools/list and tools/call (see plan §10 Threading Model).
	 */
	TArray<FFuzzyCandidate> ScoreFuzzyMatches(
		const FString& Needle,
		const TArray<FString>& KeysSnapshot,
		int32 TopN);
}
