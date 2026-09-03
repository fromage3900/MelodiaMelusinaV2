// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "AssetDefinitionDefault.h"
#include "PCGExDataAssetFactory.h"
#include "PCGExPropertySchemaAsset.h"

#include "PCGExPropertySchemaAssetFactory.generated.h"

UCLASS()
class UPCGExPropertySchemaAssetFactory : public UPCGExDataAssetFactoryBase
{
	GENERATED_BODY()

public:
	UPCGExPropertySchemaAssetFactory()
	{
		SupportedClass = UPCGExPropertySchemaAsset::StaticClass();
	}
};

UCLASS()
class UAssetDefinition_PCGExPropertySchemaAsset : public UAssetDefinitionDefault
{
	GENERATED_BODY()

public:
	virtual FText GetAssetDisplayName() const override
	{
		return INVTEXT("Property Schema");
	}

	virtual FLinearColor GetAssetColor() const override
	{
		return FLinearColor(FColor(0x4F, 0xD8, 0x95));
	}

	virtual FText GetAssetDescription(const FAssetData& AssetData) const override
	{
		return INVTEXT("A composable and inheritable library of properties definition.");
	}

	virtual TSoftClassPtr<UObject> GetAssetClass() const override
	{
		return UPCGExPropertySchemaAsset::StaticClass();
	}

	virtual TConstArrayView<FAssetCategoryPath> GetAssetCategories() const override
	{
		static const auto Categories = {FAssetCategoryPath(INVTEXT("PCGEx")) / INVTEXT("Core")};
		return Categories;
	}
};
