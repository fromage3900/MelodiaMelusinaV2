// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Helpers/PCGExBucketDispatchHelpers.h"

#include "Containers/PCGExScopedContainers.h"
#include "Data/PCGExPointIO.h"
#include "Helpers/PCGExPointArrayDataHelpers.h"

namespace PCGExBucketDispatchHelpers
{
	void DispatchBuckets(
		TConstArrayView<TSharedPtr<PCGExData::FPointIOCollection>> Buckets,
		const TSharedPtr<PCGExData::FPointIOCollection>& UnmatchedBucket,
		TConstArrayView<int32> Counts,
		TConstArrayView<TSharedPtr<PCGExMT::TScopedArray<int32>>> ScopedIndices,
		int32 NumPoints,
		FCreateIOFn CreateIO)
	{
		const int32 NumBuckets = Buckets.Num();
		const int32 UnmatchedIdx = NumBuckets;

		check(Counts.Num() == NumBuckets + 1);
		check(ScopedIndices.Num() == NumBuckets + 1);

		// Single-bucket zero-copy optimization: if every point landed in one bucket, Forward it.
		int32 SingleBucket = -1;
		for (int32 i = 0; i <= UnmatchedIdx; i++)
		{
			if (Counts[i] == NumPoints)
			{
				SingleBucket = i;
				break;
			}
		}

		if (SingleBucket >= 0)
		{
			if (SingleBucket == UnmatchedIdx)
			{
				if (UnmatchedBucket)
				{
					(void)CreateIO(UnmatchedBucket.ToSharedRef(), PCGExData::EIOInit::Forward);
				}
			}
			else
			{
				(void)CreateIO(Buckets[SingleBucket].ToSharedRef(), PCGExData::EIOInit::Forward);
			}
			return;
		}

		// Mixed distribution: create a new output per non-empty named bucket.
		for (int32 i = 0; i < NumBuckets; i++)
		{
			if (Counts[i] <= 0)
			{
				continue;
			}

			TArray<int32> ReadIndices;
			ScopedIndices[i]->Collapse(ReadIndices);

			TSharedPtr<PCGExData::FPointIO> BucketIO = CreateIO(Buckets[i].ToSharedRef(), PCGExData::EIOInit::New);
			if (!BucketIO)
			{
				continue;
			}

			PCGExPointArrayDataHelpers::SetNumPointsAllocated(BucketIO->GetOut(), ReadIndices.Num(), BucketIO->GetAllocations());
			BucketIO->InheritProperties(ReadIndices, BucketIO->GetAllocations());
		}

		// Unmatched bucket (only when the caller opted in by passing a non-null collection).
		if (UnmatchedBucket && Counts[UnmatchedIdx] > 0)
		{
			TArray<int32> ReadIndices;
			ScopedIndices[UnmatchedIdx]->Collapse(ReadIndices);

			TSharedPtr<PCGExData::FPointIO> UnmatchedIO = CreateIO(UnmatchedBucket.ToSharedRef(), PCGExData::EIOInit::New);
			if (!UnmatchedIO)
			{
				return;
			}

			PCGExPointArrayDataHelpers::SetNumPointsAllocated(UnmatchedIO->GetOut(), ReadIndices.Num(), UnmatchedIO->GetAllocations());
			UnmatchedIO->InheritProperties(ReadIndices, UnmatchedIO->GetAllocations());
		}
	}
}
