// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExSelectorClassic.h"

#include "Containers/PCGExManagedObjects.h"
#include "Selectors/PCGExBuiltinPickerOperations.h"

TSharedPtr<FPCGExEntryPickerOperation> UPCGExSelectorClassicFactoryData::CreateEntryOperation(FPCGExContext* InContext) const
{
	switch (Config.Mode)
	{
	case EPCGExDistribution::Index:
	{
		TSharedPtr<FPCGExEntryIndexPickerOp> NewOp = MakeShared<FPCGExEntryIndexPickerOp>();
		NewOp->IndexConfig = Config.IndexConfig;
		return NewOp;
	}
	case EPCGExDistribution::Random:
		return MakeShared<FPCGExEntryRandomPickerOp>();
	case EPCGExDistribution::WeightedRandom:
	default:
		return MakeShared<FPCGExEntryWeightedRandomPickerOp>();
	}
}

UPCGExFactoryData* UPCGExSelectorClassicFactoryProviderSettings::CreateFactory(FPCGExContext* InContext, UPCGExFactoryData* InFactory) const
{
	UPCGExSelectorClassicFactoryData* NewFactory = InContext->ManagedObjects->New<UPCGExSelectorClassicFactoryData>();
	NewFactory->BaseConfig = BaseConfig;
	NewFactory->Config = Config;
	return Super::CreateFactory(InContext, NewFactory);
}

#if WITH_EDITOR
FString UPCGExSelectorClassicFactoryProviderSettings::GetDisplayName() const
{
	switch (Config.Mode)
	{
	default:
	case EPCGExDistribution::Index:
		return TEXT("Select : Indexed on ") + PCGExMetaHelpers::GetSelectorDisplayName(Config.IndexConfig.IndexSource);
	case EPCGExDistribution::Random:
		return TEXT("Select : Random");
	case EPCGExDistribution::WeightedRandom:
		return TEXT("Select : Weighted Random");
	}
}
#endif
