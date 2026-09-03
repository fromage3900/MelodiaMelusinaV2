// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"

namespace PCGExClusters
{
	class FCluster;
}

namespace PCGEx
{
	class FScoredQueue;
	class FHashLookup;
}

namespace PCGExPathfinding
{
	class PCGEXELEMENTSPATHFINDING_API FSearchAllocations : public TSharedFromThis<FSearchAllocations>
	{
	protected:
		int32 NumNodes = 0;

	public:
		FSearchAllocations() = default;
		virtual ~FSearchAllocations() = default;

		TBitArray<> Visited;
		TArray<double> GScore;
		double GScoreInit = -1;
		TSharedPtr<PCGEx::FHashLookup> TravelStack;
		TSharedPtr<PCGEx::FScoredQueue> ScoredQueue;

		virtual void Init(const PCGExClusters::FCluster* InCluster);

		/** Allocates GScore and registers the sentinel Reset() must restore it to. */
		void InitGScore(const double InInitValue);

		virtual void Reset();

	protected:
		/** Sparse-resets one set of search state, driven by the queue's touched list.
		 * Valid as long as the search only dirties per-node state alongside queue enqueues. */
		void ResetSearchState(const TSharedPtr<PCGEx::FScoredQueue>& InQueue, TBitArray<>& InVisited, TArray<double>& InGScore, const double InGScoreInit, const TSharedPtr<PCGEx::FHashLookup>& InTravelStack) const;
	};
}
