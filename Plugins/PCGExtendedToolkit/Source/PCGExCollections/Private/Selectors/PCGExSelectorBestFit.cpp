// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExSelectorBestFit.h"

#include "Core/PCGExAssetCollection.h"
#include "Core/PCGExContext.h"
#include "Data/PCGBasePointData.h"
#include "Data/PCGExData.h"
#include "Data/PCGExPointIO.h"
#include "Details/PCGExSettingsDetails.h"
#include "Selectors/PCGExSelectorHelpers.h"

#pragma region FPCGExEntryBestFitPickerOpBase

void FPCGExEntryBestFitPickerOpBase::OnSharedDataMissing(FPCGExContext* InContext) const
{
	PCGEX_LOG_MISSING_INPUT(InContext, FTEXT("Selector : Best Fit -- no entries with valid bounds. Check that the collection's entries have non-zero Staging.Bounds."))
}

bool FPCGExEntryBestFitPickerOpBase::OnInitForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade)
{
	const UPCGBasePointData* PointData = InDataFacade->Source->GetIn();
	if (!PointData)
	{
		return false;
	}

	BoundsMinRange = PointData->GetConstBoundsMinValueRange();
	BoundsMaxRange = PointData->GetConstBoundsMaxValueRange();
	if (bApplyPointScale)
	{
		TransformRange = PointData->GetConstTransformValueRange();
	}

	PoolSizeGetter = PoolSize.GetValueSetting();
	if (!PoolSizeGetter->Init(InDataFacade))
	{
		return false;
	}

	// Clamp AxisMask to a valid non-zero bitmask. Zero mask would make all scores identical.
	if (Metric != EPCGExBestFitMetric::ClosestVolume && (AxisMask & 0b111) == 0)
	{
		AxisMask = 0b111;
	}

	return true;
}

FVector FPCGExEntryBestFitPickerOpBase::GetPointExtents(int32 PointIndex) const
{
	using namespace PCGExCollections::Selectors;
	return bApplyPointScale
		? ExtentFromBoundsScaled(BoundsMinRange[PointIndex], BoundsMaxRange[PointIndex], TransformRange[PointIndex].GetScale3D())
		: ExtentFromBounds(BoundsMinRange[PointIndex], BoundsMaxRange[PointIndex]);
}

double FPCGExEntryBestFitPickerOpBase::ComputeScore(const FVector& P, int32 EntryIndex) const
{
	const FVector& E = Shared->EntryExtents[EntryIndex];
	const double Ve = Shared->EntryVolumes[EntryIndex];

	switch (Metric)
	{
	default:
	case EPCGExBestFitMetric::ClosestVolume:
	{
		const double Vp = P.X * P.Y * P.Z;
		const double MaxV = FMath::Max3(Ve, Vp, UE_DOUBLE_SMALL_NUMBER);
		return FMath::Abs(Ve - Vp) / MaxV;
	}
	case EPCGExBestFitMetric::ClosestPerAxis:
	{
		const double PerAxis[3] = {
			FMath::Abs(E.X - P.X),
			FMath::Abs(E.Y - P.Y),
			FMath::Abs(E.Z - P.Z)
		};
		double Accum = 0.0;
		for (int32 a = 0; a < 3; ++a)
		{
			if (!(AxisMask & (1 << a)))
			{
				continue;
			}
			Accum = (AxisAggregation == EPCGExBestFitAxisAggregation::Sum)
				? Accum + PerAxis[a]
				: FMath::Max(Accum, PerAxis[a]);
		}
		return Accum;
	}
	case EPCGExBestFitMetric::ClosestAspectRatio:
	{
		const FVector& Enorm = Shared->EntryExtentsMaxNorm[EntryIndex];
		const double PMax = FMath::Max3(P.X, P.Y, P.Z);
		const FVector Pnorm = PMax > UE_DOUBLE_SMALL_NUMBER ? P / PMax : FVector::ZeroVector;

		const double PerAxis[3] = {
			FMath::Abs(Enorm.X - Pnorm.X),
			FMath::Abs(Enorm.Y - Pnorm.Y),
			FMath::Abs(Enorm.Z - Pnorm.Z)
		};
		double Accum = 0.0;
		for (int32 a = 0; a < 3; ++a)
		{
			if (!(AxisMask & (1 << a)))
			{
				continue;
			}
			Accum = (AxisAggregation == EPCGExBestFitAxisAggregation::Sum)
				? Accum + PerAxis[a]
				: FMath::Max(Accum, PerAxis[a]);
		}

		if (VolumeInfluence > 0.0)
		{
			const double Vp = P.X * P.Y * P.Z;
			const double MaxV = FMath::Max3(Ve, Vp, UE_DOUBLE_SMALL_NUMBER);
			const double VolumeScore = FMath::Abs(Ve - Vp) / MaxV;
			Accum += VolumeInfluence * VolumeScore;
		}
		return Accum;
	}
	}
}

#pragma endregion

#pragma region FPCGExEntryBestFitTopKPickerOp

int32 FPCGExEntryBestFitTopKPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());
	const TArray<int32>& ValidEntryIndices = Shared->ValidEntryIndices;
	const TArray<double>& EntryWeights = Shared->EntryWeights;

	if (ValidEntryIndices.IsEmpty())
	{
		return -1;
	}

	const FVector P = GetPointExtents(PointIndex);
	const int32 N = ValidEntryIndices.Num();
	const int32 K = FMath::Clamp(FMath::RoundToInt(PoolSizeGetter->Read(PointIndex)), 1, N);

	// Score + sort. Inline allocator covers typical category sizes.
	TArray<TPair<double, int32>, TInlineAllocator<32>> Scored;
	Scored.Reserve(N);
	for (const int32 i : ValidEntryIndices)
	{
		Scored.Emplace(ComputeScore(P, i), i);
	}
	Scored.Sort([](const TPair<double, int32>& A, const TPair<double, int32>& B)
	{
		return A.Key < B.Key;
	});

	// Pool = first K, plus any ties at the K-th score to avoid arbitrary tie-breaking.
	const double Cutoff = Scored[K - 1].Key;
	TArray<int32, TInlineAllocator<32>> Pool;
	TArray<double, TInlineAllocator<32>> Cumulative;
	double TotalWeight = 0.0;

	for (const TPair<double, int32>& S : Scored)
	{
		if (S.Key > Cutoff + UE_DOUBLE_KINDA_SMALL_NUMBER)
		{
			break;
		}
		Pool.Add(S.Value);
		TotalWeight += EntryWeights[S.Value];
		Cumulative.Add(TotalWeight);
	}

	const int32 k = PCGExCollections::Selectors::RollCumulativeWeighted(MakeArrayView(Cumulative), TotalWeight, Seed);
	return k == INDEX_NONE ? -1 : Target->Indices[Pool[k]];
}

#pragma endregion

#pragma region FPCGExEntryBestFitTolerancePickerOp

int32 FPCGExEntryBestFitTolerancePickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());
	const TArray<int32>& ValidEntryIndices = Shared->ValidEntryIndices;
	const TArray<double>& EntryWeights = Shared->EntryWeights;

	if (ValidEntryIndices.IsEmpty())
	{
		return -1;
	}

	const FVector P = GetPointExtents(PointIndex);
	const double Tolerance = FMath::Max(0.0, PoolSizeGetter->Read(PointIndex));

	// Single pass: score and track best.
	TArray<TPair<double, int32>, TInlineAllocator<32>> Scored;
	Scored.Reserve(ValidEntryIndices.Num());
	double BestScore = TNumericLimits<double>::Max();
	for (const int32 i : ValidEntryIndices)
	{
		const double S = ComputeScore(P, i);
		Scored.Emplace(S, i);
		if (S < BestScore)
		{
			BestScore = S;
		}
	}

	// Pool = entries within Tolerance * BestScore of the best score.
	// When BestScore is ~0 (perfect fit), the cutoff also ~0 → only perfect-tie entries pool together.
	const double Cutoff = BestScore * (1.0 + Tolerance) + UE_DOUBLE_KINDA_SMALL_NUMBER;

	TArray<int32, TInlineAllocator<32>> Pool;
	TArray<double, TInlineAllocator<32>> Cumulative;
	double TotalWeight = 0.0;

	for (const TPair<double, int32>& S : Scored)
	{
		if (S.Key > Cutoff)
		{
			continue;
		}
		Pool.Add(S.Value);
		TotalWeight += EntryWeights[S.Value];
		Cumulative.Add(TotalWeight);
	}

	const int32 k = PCGExCollections::Selectors::RollCumulativeWeighted(MakeArrayView(Cumulative), TotalWeight, Seed);
	return k == INDEX_NONE ? -1 : Target->Indices[Pool[k]];
}

#pragma endregion

#pragma region UPCGExSelectorBestFitFactoryData

TSharedPtr<FPCGExEntryPickerOperation> UPCGExSelectorBestFitFactoryData::CreateEntryOperation(FPCGExContext* InContext) const
{
	TSharedPtr<FPCGExEntryBestFitPickerOpBase> NewOp;

	switch (Config.PoolStrategy)
	{
	default:
	case EPCGExBestFitPoolStrategy::TopK:
		NewOp = MakeShared<FPCGExEntryBestFitTopKPickerOp>();
		break;
	case EPCGExBestFitPoolStrategy::Tolerance:
		NewOp = MakeShared<FPCGExEntryBestFitTolerancePickerOp>();
		break;
	}

	NewOp->Metric = Config.Metric;
	NewOp->AxisMask = Config.AxisMask;
	NewOp->AxisAggregation = Config.AxisAggregation;
	NewOp->VolumeInfluence = Config.VolumeInfluence;
	NewOp->bApplyPointScale = Config.bApplyPointScale;
	// Pick the shorthand that matches the chosen strategy -- op reads a single PoolSize regardless.
	NewOp->PoolSize = (Config.PoolStrategy == EPCGExBestFitPoolStrategy::TopK) ? Config.TopK : Config.Tolerance;
	return NewOp;
}

TSharedPtr<PCGExCollections::FSelectorSharedData> UPCGExSelectorBestFitFactoryData::BuildSharedData(
	const UPCGExAssetCollection* Collection,
	const PCGExAssetCollection::FCategory* Target) const
{
	if (!Collection || !Target)
	{
		return nullptr;
	}

	const int32 N = Target->Entries.Num();

	TSharedPtr<FPCGExBestFitSharedData> NewShared = MakeShared<FPCGExBestFitSharedData>();
	NewShared->EntryExtents.SetNumUninitialized(N);
	NewShared->EntryExtentsMaxNorm.SetNumUninitialized(N);
	NewShared->EntryVolumes.SetNumUninitialized(N);
	NewShared->EntryWeights.SetNumUninitialized(N);
	NewShared->ValidEntryIndices.Reserve(N);

	for (int32 i = 0; i < N; ++i)
	{
		const FPCGExAssetCollectionEntry* Entry = Target->Entries[i];
		FVector Ext = FVector::ZeroVector;
		double Vol = 0.0;

		if (Entry && Entry->Staging.Bounds.IsValid)
		{
			Ext = Entry->Staging.Bounds.GetExtent();
			Vol = Ext.X * Ext.Y * Ext.Z;
		}

		NewShared->EntryExtents[i] = Ext;
		NewShared->EntryVolumes[i] = Vol;
		NewShared->EntryWeights[i] = PCGExCollections::Selectors::EntryEffectiveWeight(Entry);

		// Max-component normalized for AspectRatio metric. Zero when Ext is degenerate.
		const double MaxExt = FMath::Max3(Ext.X, Ext.Y, Ext.Z);
		NewShared->EntryExtentsMaxNorm[i] = MaxExt > UE_DOUBLE_SMALL_NUMBER ? Ext / MaxExt : FVector::ZeroVector;

		if (Vol > UE_DOUBLE_SMALL_NUMBER)
		{
			NewShared->ValidEntryIndices.Add(i);
		}
	}

	// Caller (op's PrepareForData) reports the error when Shared is null.
	if (NewShared->ValidEntryIndices.IsEmpty())
	{
		return nullptr;
	}

	return NewShared;
}

#pragma endregion

#pragma region UPCGExSelectorBestFitFactoryProviderSettings

UPCGExFactoryData* UPCGExSelectorBestFitFactoryProviderSettings::CreateFactory(FPCGExContext* InContext, UPCGExFactoryData* InFactory) const
{
	UPCGExSelectorBestFitFactoryData* NewFactory = InContext->ManagedObjects->New<UPCGExSelectorBestFitFactoryData>();
	NewFactory->BaseConfig = BaseConfig;
	NewFactory->Config = Config;
	return Super::CreateFactory(InContext, NewFactory);
}

#if WITH_EDITOR
FString UPCGExSelectorBestFitFactoryProviderSettings::GetDisplayName() const
{
	switch (Config.Metric)
	{
	default:
	case EPCGExBestFitMetric::ClosestVolume:
		return TEXT("Select : Fit Volume");
	case EPCGExBestFitMetric::ClosestPerAxis:
		return TEXT("Select : Fit Per-Axis");
	case EPCGExBestFitMetric::ClosestAspectRatio:
		return TEXT("Select : Fit Aspect");
	}
}
#endif

#pragma endregion
