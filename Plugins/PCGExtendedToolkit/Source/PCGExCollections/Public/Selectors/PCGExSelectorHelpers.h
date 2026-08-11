// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Core/PCGExAssetCollection.h"
#include "Math/RandomStream.h"
#include "Selectors/PCGExEntryPickerOperation.h"
#include "Selectors/PCGExSelectorSharedData.h"

namespace PCGExData
{
	class FFacade;
}

struct FPCGExContext;

/**
 * Shared utilities for selector implementations. All inline / header-only -- no .cpp.
 * Lives outside any UCLASS / USTRUCT so it has zero reflection / link-time cost.
 *
 * Use these whenever a new selector needs the same primitive (weight resolution, extent
 * extraction, weighted roll) to keep the hot-path logic single-sourced.
 */
namespace PCGExCollections::Selectors
{
	/**
	 * Canonical entry weight conversion. `+ 1` because authored Weight=0 still represents a
	 * valid entry that should be pickable (just at minimum probability). Casting to double
	 * pre-empts integer overflow in cumulative sums for large weights / large categories.
	 */
	FORCEINLINE double EntryEffectiveWeight(const FPCGExAssetCollectionEntry* Entry)
	{
		return Entry ? static_cast<double>(Entry->Weight + 1) : 0.0;
	}

	/** Half-size extent from PCG bounds-min / bounds-max. */
	FORCEINLINE FVector ExtentFromBounds(const FVector& Min, const FVector& Max)
	{
		return (Max - Min) * 0.5;
	}

	/** Half-size extent from PCG bounds-min / bounds-max, scaled by the point's transform scale (abs). */
	FORCEINLINE FVector ExtentFromBoundsScaled(const FVector& Min, const FVector& Max, const FVector& Scale)
	{
		return (Max - Min) * 0.5 * Scale.GetAbs();
	}

	/**
	 * Roll a uniform value in [0, Total] and return the first index k where Cumulative[k] >= Roll.
	 * Caller builds Cumulative in parallel to a pool/match array; this returns the pool index.
	 *
	 * @return INDEX_NONE for empty / non-positive-total inputs; otherwise an index in [0, Cumulative.Num()).
	 *         The fallback "last entry" is returned only on numerical drift (Roll just past Cumulative.Last()).
	 */
	FORCEINLINE int32 RollCumulativeWeighted(TArrayView<const double> Cumulative, double Total, int32 Seed)
	{
		if (Cumulative.IsEmpty() || Total <= 0.0)
		{
			return INDEX_NONE;
		}
		const double Roll = FRandomStream(Seed).FRandRange(0.0, Total);
		for (int32 k = 0; k < Cumulative.Num(); ++k)
		{
			if (Roll <= Cumulative[k])
			{
				return k;
			}
		}
		// Numerical drift fallback -- last bucket wins.
		return Cumulative.Num() - 1;
	}

	/**
	 * Streaming variant: caller provides N and a weight getter (callable taking int32 -> double).
	 * Saves an allocation when the caller already has weights addressable by index and doesn't
	 * need to materialize a Cumulative array.
	 *
	 * @return INDEX_NONE for empty / non-positive-total inputs; otherwise k in [0, N).
	 */
	template <typename WeightFn>
	FORCEINLINE int32 RollWeightedStreaming(int32 N, WeightFn&& GetWeight, double Total, int32 Seed)
	{
		if (N <= 0 || Total <= 0.0)
		{
			return INDEX_NONE;
		}
		const double Roll = FRandomStream(Seed).FRandRange(0.0, Total);
		double Acc = 0.0;
		for (int32 k = 0; k < N; ++k)
		{
			Acc += GetWeight(k);
			if (Roll <= Acc)
			{
				return k;
			}
		}
		return N - 1;
	}

	/**
	 * Entry picker base for selectors that consume typed FSelectorSharedData. Handles the
	 * common skeleton:
	 *   1. Forward PrepareForData to FPCGExEntryPickerOperation.
	 *   2. Cast SharedData → typed Shared. If null, invoke OnSharedDataMissing then bail.
	 *   3. Defer remaining init to OnInitForData (subclass).
	 *
	 * Subclasses must implement OnInitForData. OnSharedDataMissing is optional -- default
	 * is silent. Concrete pickers typically log a selector-specific message there.
	 */
	template <typename TSharedDataType>
	class TTypedSharedPickerOpBase : public FPCGExEntryPickerOperation
	{
	public:
		/** Typed view of the base SharedData. Resolved in PrepareForData. */
		TSharedPtr<TSharedDataType> Shared;

		virtual bool PrepareForData(
			FPCGExContext* InContext,
			const TSharedRef<PCGExData::FFacade>& InDataFacade,
			PCGExAssetCollection::FCategory* InTarget,
			const UPCGExAssetCollection* InOwningCollection) override
		{
			if (!FPCGExEntryPickerOperation::PrepareForData(InContext, InDataFacade, InTarget, InOwningCollection))
			{
				return false;
			}
			Shared = StaticCastSharedPtr<TSharedDataType>(SharedData);
			if (!Shared)
			{
				OnSharedDataMissing(InContext);
				return false;
			}
			return OnInitForData(InContext, InDataFacade);
		}

	protected:
		/** Called when typed shared-data could not be acquired. Override to emit a selector-specific error. */
		virtual void OnSharedDataMissing(FPCGExContext* InContext) const
		{
		}

		/** Called after Shared is acquired. Subclasses initialize getters / validate config here. */
		virtual bool OnInitForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade) = 0;
	};
}
