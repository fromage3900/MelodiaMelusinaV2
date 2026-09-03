// SPDX-License-Identifier: MIT
// Survivor C (Action + namespace did_you_mean fuzzy match) — plan §3.C.
// Plan: Plugins/Monolith/Docs/plans/2026-05-27-mcp-llm-ergonomics.md

#include "MonolithFuzzyMatch.h"
#include "Algo/LevenshteinDistance.h"
#include "Algo/StableSort.h"

namespace MonolithFuzzyMatchDetail
{
	TArray<FFuzzyCandidate> ScoreFuzzyMatches(
		const FString& Needle,
		const TArray<FString>& KeysSnapshot,
		int32 TopN)
	{
		TArray<FFuzzyCandidate> Result;

		if (Needle.IsEmpty() || KeysSnapshot.Num() == 0 || TopN <= 0)
		{
			return Result;
		}

		// Score every candidate. Pattern matches the verified precedent at
		// Engine/Plugins/Animation/IKRig/Source/IKRigEditor/Private/RigEditor/
		// IKRigAutoCharacterizer.cpp:1761:
		//
		//   const float Score = 1.0f - (
		//     static_cast<float>(Algo::LevenshteinDistance(NameToMatchStr, CurrentNameStr))
		//     / WorstCase);
		//
		// WorstCase guards against div-by-zero for two empty strings (already
		// excluded by the Needle.IsEmpty check above, but cheap defence) and
		// normalises across needle/candidate length disparity.
		TArray<FFuzzyCandidate> All;
		All.Reserve(KeysSnapshot.Num());

		for (const FString& Key : KeysSnapshot)
		{
			const int32 Distance = Algo::LevenshteinDistance(Needle, Key);
			const int32 MaxLen = FMath::Max(Needle.Len(), Key.Len());
			const float WorstCase = MaxLen > 0 ? static_cast<float>(MaxLen) : 1.0f;
			const float Score = 1.0f - (static_cast<float>(Distance) / WorstCase);

			FFuzzyCandidate C;
			C.Key = Key;
			C.Score = Score;
			All.Add(MoveTemp(C));
		}

		// Sort descending by Score. Use StableSort so equal-score candidates
		// retain insertion order (KeysSnapshot order), which the dispatch path
		// already controls via the registry's TMap iteration order.
		Algo::StableSort(All, [](const FFuzzyCandidate& A, const FFuzzyCandidate& B)
		{
			return A.Score > B.Score;
		});

		const int32 Take = FMath::Min(TopN, All.Num());
		Result.Reserve(Take);
		for (int32 i = 0; i < Take; ++i)
		{
			Result.Add(All[i]);
		}
		return Result;
	}
}
