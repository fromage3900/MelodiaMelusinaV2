// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExSelectorRangeBased.h"

#include "PCGExPropertyTypes.h"
#include "Containers/PCGExManagedObjects.h"
#include "Core/PCGExAssetCollection.h"
#include "Core/PCGExContext.h"
#include "Data/PCGExData.h"
#include "Details/PCGExSettingsDetails.h"
#include "Selectors/PCGExSelectorHelpers.h"

namespace PCGExSelectorRangeBased
{
	constexpr double RangeTieEpsilon = 1e-6;

	// Resolve a numeric property on an entry as double. Accepts any PCG-numeric property
	// (Double/Float/Int32/Int64/Bool) transparently via the type-erased TryGetPropertyValue.
	bool ResolveNumericAsDouble(const FPCGExAssetCollectionEntry* Entry, const UPCGExAssetCollection* Collection, FName Name, double& OutValue)
	{
		return Entry->TryGetPropertyValue<double>(Collection, Name, OutValue);
	}

	// Resolve a Vector2D-style range property on an entry. Any vector-compatible property
	// projects via TryGetPropertyValue<FVector2D> -- FVector drops Z to give (X, Y),
	// FVector4 drops Z/W. X -> Min, Y -> Max.
	bool ResolveRangeFromVector(const FPCGExAssetCollectionEntry* Entry, const UPCGExAssetCollection* Collection, FName Name, double& OutMin, double& OutMax)
	{
		FVector2D XY = FVector2D::ZeroVector;
		if (!Entry->TryGetPropertyValue<FVector2D>(Collection, Name, XY))
		{
			return false;
		}
		OutMin = XY.X;
		OutMax = XY.Y;
		return true;
	}

	// Resolve one axis's (Min, Max) for one entry, applying SourceMode + auto-swap.
	// Returns false if the property could not be resolved on this entry/axis combination.
	bool ResolveAxisForEntry(const FPCGExSelectorRangeAxis& Axis, const FPCGExAssetCollectionEntry* Entry, const UPCGExAssetCollection* Collection, double& OutMin, double& OutMax)
	{
		bool bResolved = false;
		double Min = 0.0;
		double Max = 0.0;
		switch (Axis.SourceMode)
		{
		case EPCGExRangeSourceMode::TwoNumerics:
			bResolved = ResolveNumericAsDouble(Entry, Collection, Axis.MinPropertyName, Min)
				&& ResolveNumericAsDouble(Entry, Collection, Axis.MaxPropertyName, Max);
			break;
		case EPCGExRangeSourceMode::Vector2:
			bResolved = ResolveRangeFromVector(Entry, Collection, Axis.RangePropertyName, Min, Max);
			break;
		}
		if (!bResolved)
		{
			return false;
		}
		// Auto-swap out-of-order ranges -- matches PCGEx convention for numeric range inputs.
		if (Min > Max)
		{
			Swap(Min, Max);
		}
		OutMin = Min;
		OutMax = Max;
		return true;
	}
}

#pragma region FPCGExEntryRangeBasedPickerOpBase

void FPCGExEntryRangeBasedPickerOpBase::OnSharedDataMissing(FPCGExContext* InContext) const
{
	PCGEX_LOG_MISSING_INPUT(InContext, FTEXT("Selector : Range-Based -- no entries resolved every configured axis. Check property names and types in the collection."))
}

bool FPCGExEntryRangeBasedPickerOpBase::OnInitForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade)
{
	const int32 AxisCount = Axes.Num();
	if (AxisCount == 0)
	{
		PCGEX_LOG_MISSING_INPUT(InContext, FTEXT("Selector : Range-Based -- Axes array is empty. At least one axis is required."))
		return false;
	}

	ValueGetters.SetNum(AxisCount);
	for (int32 A = 0; A < AxisCount; ++A)
	{
		ValueGetters[A] = Axes[A].ValueSource.GetValueSetting();
		if (!ValueGetters[A]->Init(InDataFacade))
		{
			return false;
		}
	}

	return true;
}

#pragma endregion

#pragma region FPCGExEntryRangeWeightedRandomPickerOp

int32 FPCGExEntryRangeWeightedRandomPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());

	TArray<double, TInlineAllocator<8>> PointValues;
	ReadPointValues(PointIndex, PointValues);

	const TArray<int32>& ValidEntryIndices = Shared->ValidEntryIndices;
	const TArray<double>& EntryWeights = Shared->EntryWeights;

	// Scan valid entries; accumulate cumulative weights for entries that pass all axes.
	TArray<int32, TInlineAllocator<32>> Matches;
	TArray<double, TInlineAllocator<32>> Cumulative;
	double TotalWeight = 0.0;

	for (const int32 i : ValidEntryIndices)
	{
		if (!MatchesAllAxes(i, PointValues.GetData()))
		{
			continue;
		}
		TotalWeight += EntryWeights[i];
		Matches.Add(i);
		Cumulative.Add(TotalWeight);
	}

	const int32 k = PCGExCollections::Selectors::RollCumulativeWeighted(MakeArrayView(Cumulative), TotalWeight, Seed);
	return k == INDEX_NONE ? -1 : Target->Indices[Matches[k]];
}

#pragma endregion

#pragma region FPCGExEntryRangeFirstMatchPickerOp

int32 FPCGExEntryRangeFirstMatchPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());

	TArray<double, TInlineAllocator<8>> PointValues;
	ReadPointValues(PointIndex, PointValues);

	// ValidEntryIndices is built in ascending entry order, so iterating it preserves
	// "first in entry order" semantics while skipping unresolved entries.
	for (const int32 i : Shared->ValidEntryIndices)
	{
		if (MatchesAllAxes(i, PointValues.GetData()))
		{
			return Target->Indices[i];
		}
	}

	return -1;
}

#pragma endregion

#pragma region FPCGExEntryRangeNarrowestPickerOp

int32 FPCGExEntryRangeNarrowestPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());

	const int32 AxisCount = Shared->AxisCount;

	TArray<double, TInlineAllocator<8>> PointValues;
	ReadPointValues(PointIndex, PointValues);

	const TArray<int32>& ValidEntryIndices = Shared->ValidEntryIndices;
	const TArray<double>& EntryMins = Shared->EntryMins;
	const TArray<double>& EntryMaxs = Shared->EntryMaxs;
	const TArray<double>& EntryWeights = Shared->EntryWeights;

	// Hypervolume = product of per-axis widths. For AxisCount=1 this is just (Max - Min), so
	// behavior is identical to the original single-axis Narrowest. For AxisCount>1 this picks
	// the most specific range region -- the geometric analogue of "narrowest".
	double MinHypervolume = TNumericLimits<double>::Max();
	TArray<int32, TInlineAllocator<8>> TieBucket;

	for (const int32 i : ValidEntryIndices)
	{
		if (!MatchesAllAxes(i, PointValues.GetData()))
		{
			continue;
		}

		const int32 Base = i * AxisCount;
		double Hypervolume = 1.0;
		for (int32 A = 0; A < AxisCount; ++A)
		{
			Hypervolume *= (EntryMaxs[Base + A] - EntryMins[Base + A]);
		}

		if (Hypervolume < MinHypervolume - PCGExSelectorRangeBased::RangeTieEpsilon)
		{
			MinHypervolume = Hypervolume;
			TieBucket.Reset();
			TieBucket.Add(i);
		}
		else if (FMath::Abs(Hypervolume - MinHypervolume) <= PCGExSelectorRangeBased::RangeTieEpsilon)
		{
			TieBucket.Add(i);
		}
	}

	if (TieBucket.IsEmpty())
	{
		return -1;
	}
	if (TieBucket.Num() == 1)
	{
		return Target->Indices[TieBucket[0]];
	}

	// Tie-break by weight via streaming roll (no need to materialize a cumulative array).
	double TotalWeight = 0.0;
	for (const int32 i : TieBucket)
	{
		TotalWeight += EntryWeights[i];
	}
	if (TotalWeight <= 0.0)
	{
		return Target->Indices[TieBucket[0]];
	}

	const int32 k = PCGExCollections::Selectors::RollWeightedStreaming(
		TieBucket.Num(),
		[&](int32 LocalIdx)
		{
			return EntryWeights[TieBucket[LocalIdx]];
		},
		TotalWeight, Seed);
	return Target->Indices[TieBucket[k]];
}

#pragma endregion

#pragma region UPCGExSelectorRangeBasedFactoryData

TSharedPtr<FPCGExEntryPickerOperation> UPCGExSelectorRangeBasedFactoryData::CreateEntryOperation(FPCGExContext* InContext) const
{
	TSharedPtr<FPCGExEntryRangeBasedPickerOpBase> NewOp;

	switch (Config.OverlapMode)
	{
	default:
	case EPCGExRangeOverlapMode::WeightedRandom:
		NewOp = MakeShared<FPCGExEntryRangeWeightedRandomPickerOp>();
		break;
	case EPCGExRangeOverlapMode::FirstMatch:
		NewOp = MakeShared<FPCGExEntryRangeFirstMatchPickerOp>();
		break;
	case EPCGExRangeOverlapMode::NarrowestWins:
		NewOp = MakeShared<FPCGExEntryRangeNarrowestPickerOp>();
		break;
	}

	// Per-axis ValueSource drives per-facade getters; per-entry property names are consumed
	// only by BuildSharedData. Copying Axes wholesale keeps the op self-contained for getter init.
	NewOp->Axes = Config.Axes;
	return NewOp;
}

TSharedPtr<PCGExCollections::FSelectorSharedData> UPCGExSelectorRangeBasedFactoryData::BuildSharedData(
	const UPCGExAssetCollection* Collection,
	const PCGExAssetCollection::FCategory* Target) const
{
	if (!Collection || !Target)
	{
		return nullptr;
	}

	const int32 AxisCount = Config.Axes.Num();
	if (AxisCount == 0)
	{
		return nullptr;
	}

	const int32 N = Target->Entries.Num();
	if (N == 0)
	{
		return nullptr;
	}

	TSharedPtr<FPCGExRangeBasedSharedData> NewShared = MakeShared<FPCGExRangeBasedSharedData>();
	NewShared->AxisCount = AxisCount;
	NewShared->EntryCount = N;
	NewShared->EntryMins.SetNumUninitialized(N * AxisCount);
	NewShared->EntryMaxs.SetNumUninitialized(N * AxisCount);
	NewShared->EntryWeights.SetNumZeroed(N);

	NewShared->AxisBoundaryModes.SetNumUninitialized(AxisCount);
	for (int32 A = 0; A < AxisCount; ++A)
	{
		NewShared->AxisBoundaryModes[A] = Config.Axes[A].BoundaryMode;
	}

	// Entries are valid only when every axis resolved; partial resolution => entry excluded entirely.
	// Excluded entries get a sentinel range (Min=1, Max=-1) per axis so MatchesAllAxes can never accept them.
	auto MarkInvalid = [&](int32 Base)
	{
		for (int32 A = 0; A < AxisCount; ++A)
		{
			NewShared->EntryMins[Base + A] = 1.0;
			NewShared->EntryMaxs[Base + A] = -1.0;
		}
	};

	NewShared->ValidEntryIndices.Reserve(N);
	for (int32 i = 0; i < N; ++i)
	{
		const FPCGExAssetCollectionEntry* Entry = Target->Entries[i];
		const int32 Base = i * AxisCount;

		if (!Entry)
		{
			MarkInvalid(Base);
			continue;
		}

		bool bAllResolved = true;
		for (int32 A = 0; A < AxisCount; ++A)
		{
			double Min = 0.0;
			double Max = 0.0;
			if (!PCGExSelectorRangeBased::ResolveAxisForEntry(Config.Axes[A], Entry, Collection, Min, Max))
			{
				bAllResolved = false;
				break;
			}
			NewShared->EntryMins[Base + A] = Min;
			NewShared->EntryMaxs[Base + A] = Max;
		}

		if (!bAllResolved)
		{
			MarkInvalid(Base);
			continue;
		}

		NewShared->EntryWeights[i] = PCGExCollections::Selectors::EntryEffectiveWeight(Entry);
		NewShared->ValidEntryIndices.Add(i);
	}

	// Caller (op's PrepareForData → OnSharedDataMissing) reports the error when Shared is null.
	if (NewShared->ValidEntryIndices.IsEmpty())
	{
		return nullptr;
	}

	return NewShared;
}

#pragma endregion

#pragma region UPCGExSelectorRangeBasedFactoryProviderSettings

UPCGExFactoryData* UPCGExSelectorRangeBasedFactoryProviderSettings::CreateFactory(FPCGExContext* InContext, UPCGExFactoryData* InFactory) const
{
	UPCGExSelectorRangeBasedFactoryData* NewFactory = InContext->ManagedObjects->New<UPCGExSelectorRangeBasedFactoryData>();
	NewFactory->BaseConfig = BaseConfig;
	NewFactory->Config = Config;
	return Super::CreateFactory(InContext, NewFactory);
}

#if WITH_EDITOR
FString UPCGExSelectorRangeBasedFactoryProviderSettings::GetDisplayName() const
{
	switch (Config.OverlapMode)
	{
	default:
	case EPCGExRangeOverlapMode::WeightedRandom:
		return TEXT("Select : Range Weighted");
	case EPCGExRangeOverlapMode::FirstMatch:
		return TEXT("Select : Range First");
	case EPCGExRangeOverlapMode::NarrowestWins:
		return TEXT("Select : Range Narrowest");
	}
}
#endif

#pragma endregion
