// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExBuiltinPickerOperations.h"

#include "Data/PCGExData.h"
#include "Details/PCGExSettingsDetails.h"
#include "Math/PCGExMath.h"

#pragma region FPCGExEntryWeightedRandomPickerOp

int32 FPCGExEntryWeightedRandomPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());
	return Target->GetPickRandomWeighted(Seed);
}

#pragma endregion

#pragma region FPCGExEntryRandomPickerOp

int32 FPCGExEntryRandomPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());
	return Target->GetPickRandom(Seed);
}

#pragma endregion

#pragma region FPCGExEntryIndexPickerOp

bool FPCGExEntryIndexPickerOp::PrepareForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade, PCGExAssetCollection::FCategory* InTarget, const UPCGExAssetCollection* InOwningCollection)
{
	if (!FPCGExEntryPickerOperation::PrepareForData(InContext, InDataFacade, InTarget, InOwningCollection))
	{
		return false;
	}

	const bool bWantsMinMax = IndexConfig.bRemapIndexToCollectionSize;
	IndexGetter = IndexConfig.GetValueSettingIndex();
	if (!IndexGetter->Init(InDataFacade, !bWantsMinMax, bWantsMinMax))
	{
		return false;
	}

	MaxInputIndex = IndexGetter->Max();
	return true;
}

int32 FPCGExEntryIndexPickerOp::Pick(int32 PointIndex, int32 Seed, FPCGExPickerScratchBase* Scratch) const
{
	checkSlow(Target && !Target->IsEmpty());

	const int32 MaxIndex = Target->Num() - 1;
	double UserIndex = IndexGetter->Read(PointIndex);

	if (IndexConfig.bRemapIndexToCollectionSize && MaxInputIndex > 0)
	{
		UserIndex = PCGExMath::Remap(UserIndex, 0, MaxInputIndex, 0, MaxIndex);
		UserIndex = PCGExMath::TruncateDbl(UserIndex, IndexConfig.TruncateRemap);
	}

	const int32 Sanitized = PCGExMath::SanitizeIndex(static_cast<int32>(UserIndex), MaxIndex, IndexConfig.IndexSafety);
	return Target->GetPick(Sanitized, IndexConfig.PickMode);
}

#pragma endregion

#pragma region FPCGExMicroWeightedRandomPickerOp

int32 FPCGExMicroWeightedRandomPickerOp::Pick(const PCGExAssetCollection::FMicroCache* InMicroCache, int32 PointIndex, int32 Seed) const
{
	if (!InMicroCache || InMicroCache->IsEmpty())
	{
		return -1;
	}
	return InMicroCache->GetPickRandomWeighted(Seed);
}

#pragma endregion

#pragma region FPCGExMicroRandomPickerOp

int32 FPCGExMicroRandomPickerOp::Pick(const PCGExAssetCollection::FMicroCache* InMicroCache, int32 PointIndex, int32 Seed) const
{
	if (!InMicroCache || InMicroCache->IsEmpty())
	{
		return -1;
	}
	return InMicroCache->GetPickRandom(Seed);
}

#pragma endregion

#pragma region FPCGExMicroIndexPickerOp

bool FPCGExMicroIndexPickerOp::PrepareForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade)
{
	if (!FPCGExMicroEntryPickerOperation::PrepareForData(InContext, InDataFacade))
	{
		return false;
	}

	IndexGetter = IndexConfig.GetValueSettingIndex();
	if (!IndexGetter->Init(InDataFacade, true, false))
	{
		return false;
	}

	MaxInputIndex = IndexGetter->Max();
	return true;
}

int32 FPCGExMicroIndexPickerOp::Pick(const PCGExAssetCollection::FMicroCache* InMicroCache, int32 PointIndex, int32 Seed) const
{
	if (!InMicroCache || InMicroCache->IsEmpty())
	{
		return -1;
	}

	const int32 Index = IndexGetter ? static_cast<int32>(IndexGetter->Read(PointIndex)) : 0;
	const int32 Sanitized = PCGExMath::SanitizeIndex(Index, InMicroCache->Num() - 1, IndexConfig.IndexSafety);
	return InMicroCache->GetPick(Sanitized, IndexConfig.PickMode);
}

#pragma endregion
