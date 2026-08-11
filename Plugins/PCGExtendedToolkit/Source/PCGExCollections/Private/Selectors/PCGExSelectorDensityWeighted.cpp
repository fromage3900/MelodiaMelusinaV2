// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExSelectorDensityWeighted.h"

#include "Containers/PCGExManagedObjects.h"
#include "Data/PCGExData.h"
#include "Details/PCGExSettingsDetails.h"
#include "Selectors/PCGExSelectorHelpers.h"

#pragma region FPCGExEntryDensityWeightedPickerOp

void FPCGExEntryDensityWeightedPickerOp::OnSharedDataMissing(FPCGExContext* InContext) const
{
	PCGEX_LOG_MISSING_INPUT(InContext, FTEXT("Selector : Density-Weighted -- failed to build shared weight tables. Check that the target category has at least one valid entry."))
}

bool FPCGExEntryDensityWeightedPickerOp::OnInitForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade)
{
	DensityGetter = DensitySource.GetValueSetting();
	if (!DensityGetter->Init(InDataFacade))
	{
		return false;
	}

	return true;
}

int32 FPCGExEntryDensityWeightedPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());

	double Density = DensityGetter ? DensityGetter->Read(PointIndex) : 1.0;

	// Out-of-range policy: either clamp, or skip the point entirely.
	if (Density < 0.0 || Density > 1.0)
	{
		if (OutOfRangePolicy == EPCGExDensityOutOfRangePolicy::SkipPoint)
		{
			return -1;
		}
		Density = FMath::Clamp(Density, 0.0, 1.0);
	}

	const int32 N = Target->Num();
	const TArray<double>& EntryWeights = Shared->EntryWeights;
	const TArray<double>& EntryLogWeights = Shared->EntryLogWeights;

	// Build per-point effective weights. Inline allocator covers typical category sizes
	// without heap pressure. O(N) per pick -- acceptable for the usual small-N cases.
	TArray<double, TInlineAllocator<32>> EffectiveWeights;
	EffectiveWeights.SetNumUninitialized(N);
	double TotalWeight = 0.0;

	switch (Mode)
	{
	case EPCGExDensityWeightMode::WeightModulation:
	{
		// exponent = lerp(1, density*2, DensityInfluence)
		// DI=0               -> exp=1               -> plain weighted (parity with WeightedRandom)
		// DI=1 & density=0   -> exp=0               -> uniform (all weights become 1)
		// DI=1 & density=0.5 -> exp=1               -> plain weighted
		// DI=1 & density=1   -> exp=2               -> amplified bias toward higher weights
		// Pow(W, Exp) rewritten as exp(LogW * Exp). Shared data hosts LogW once per category --
		// per-pick cost drops from one log+one exp to one exp, with no precision change for W >= 0.
		const double Exponent = FMath::Lerp(1.0, Density * 2.0, DensityInfluence);
		for (int32 i = 0; i < N; ++i)
		{
			EffectiveWeights[i] = FMath::Exp(EntryLogWeights[i] * Exponent);
			TotalWeight += EffectiveWeights[i];
		}
		break;
	}
	case EPCGExDensityWeightMode::RandomnessModulation:
	{
		// effective_density = (1 - DI) + DI * density, then effective_weight = lerp(1, W, effective_density)
		// DI=0               -> eff=1               -> plain weighted (parity with WeightedRandom)
		// DI=1 & density=1   -> eff=1               -> plain weighted
		// DI=1 & density=0   -> eff=0               -> uniform
		const double EffectiveDensity = (1.0 - DensityInfluence) + DensityInfluence * Density;
		for (int32 i = 0; i < N; ++i)
		{
			EffectiveWeights[i] = FMath::Lerp(1.0, EntryWeights[i], EffectiveDensity);
			TotalWeight += EffectiveWeights[i];
		}
		break;
	}
	}

	const int32 k = PCGExCollections::Selectors::RollWeightedStreaming(
		N,
		[&](int32 LocalIdx)
		{
			return EffectiveWeights[LocalIdx];
		},
		TotalWeight, Seed);
	return k == INDEX_NONE ? -1 : Target->Indices[k];
}

#pragma endregion

#pragma region UPCGExSelectorDensityWeightedFactoryData

TSharedPtr<FPCGExEntryPickerOperation> UPCGExSelectorDensityWeightedFactoryData::CreateEntryOperation(FPCGExContext* InContext) const
{
	TSharedPtr<FPCGExEntryDensityWeightedPickerOp> NewOp = MakeShared<FPCGExEntryDensityWeightedPickerOp>();
	NewOp->Mode = Config.Mode;
	NewOp->DensityInfluence = Config.DensityInfluence;
	NewOp->OutOfRangePolicy = Config.OutOfRangePolicy;
	NewOp->DensitySource = Config.DensitySource;
	return NewOp;
}

TSharedPtr<PCGExCollections::FSelectorSharedData> UPCGExSelectorDensityWeightedFactoryData::BuildSharedData(
	const UPCGExAssetCollection* Collection,
	const PCGExAssetCollection::FCategory* Target) const
{
	if (!Collection || !Target)
	{
		return nullptr;
	}

	const int32 N = Target->Entries.Num();
	if (N == 0)
	{
		return nullptr;
	}

	TSharedPtr<FPCGExDensityWeightedSharedData> NewShared = MakeShared<FPCGExDensityWeightedSharedData>();
	NewShared->EntryWeights.SetNumUninitialized(N);
	NewShared->EntryLogWeights.SetNumUninitialized(N);

	for (int32 i = 0; i < N; ++i)
	{
		const double W = PCGExCollections::Selectors::EntryEffectiveWeight(Target->Entries[i]);
		NewShared->EntryWeights[i] = W;
		// EntryEffectiveWeight returns Weight + 1, so W >= 1 for any valid entry -- log is well-defined.
		// W==0 only occurs when Entry is null; we treat that as log(1)=0 to keep Exp() finite (Pow path
		// would have produced 0^Exp anyway, which is the same numerical floor when the entry can't be picked).
		NewShared->EntryLogWeights[i] = W > 0.0 ? FMath::Loge(W) : 0.0;
	}

	return NewShared;
}

#pragma endregion

#pragma region UPCGExSelectorDensityWeightedFactoryProviderSettings

UPCGExFactoryData* UPCGExSelectorDensityWeightedFactoryProviderSettings::CreateFactory(FPCGExContext* InContext, UPCGExFactoryData* InFactory) const
{
	UPCGExSelectorDensityWeightedFactoryData* NewFactory = InContext->ManagedObjects->New<UPCGExSelectorDensityWeightedFactoryData>();
	NewFactory->BaseConfig = BaseConfig;
	NewFactory->Config = Config;
	return Super::CreateFactory(InContext, NewFactory);
}

#if WITH_EDITOR
FString UPCGExSelectorDensityWeightedFactoryProviderSettings::GetDisplayName() const
{
	switch (Config.Mode)
	{
	default:
	case EPCGExDensityWeightMode::WeightModulation:
		return TEXT("Select : Weight Mod");
	case EPCGExDensityWeightMode::RandomnessModulation:
		return TEXT("Select : Randomness Mod");
	}
}
#endif

#pragma endregion
