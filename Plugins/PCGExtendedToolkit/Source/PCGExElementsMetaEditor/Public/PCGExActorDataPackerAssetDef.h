// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "AssetDefinitionDefault.h"
#include "Elements/PCGExPackActorData.h"

#include "PCGExActorDataPackerAssetDef.generated.h"

UCLASS()
class UAssetDefinition_PCGExCustomActorDataPacker : public UAssetDefinitionDefault
{
	GENERATED_BODY()

public:
	virtual FText GetAssetDisplayName() const override
	{
		return INVTEXT("PCGEx Actor Data Packer");
	}

	virtual FLinearColor GetAssetColor() const override
	{
		return FLinearColor(FColor(195, 124, 40));
	}

	virtual FText GetAssetDescription(const FAssetData& AssetData) const override
	{
		return INVTEXT("Custom logic for packing actor component data onto PCG points.");
	}

	virtual TSoftClassPtr<UObject> GetAssetClass() const override
	{
		return UPCGExCustomActorDataPacker::StaticClass();
	}

	virtual TConstArrayView<FAssetCategoryPath> GetAssetCategories() const override
	{
		static const auto Categories = {FAssetCategoryPath(INVTEXT("PCGEx"))};
		return Categories;
	}
};
