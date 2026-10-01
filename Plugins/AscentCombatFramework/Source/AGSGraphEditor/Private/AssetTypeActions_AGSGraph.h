// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AssetTypeActions_Base.h"

class FAssetTypeActions_AGSGraph : public FAssetTypeActions_Base
{
public:
	FAssetTypeActions_AGSGraph(EAssetTypeCategories::Type InAssetCategory);

	virtual FText GetName() const override;
	virtual FColor GetTypeColor() const override;
	virtual UClass* GetSupportedClass() const override;
	virtual void OpenAssetEditor(const TArray<UObject*>& InObjects, TSharedPtr<class IToolkitHost> EditWithinLevelEditor = TSharedPtr<IToolkitHost>()) override;
	virtual uint32 GetCategories() override;

private:
	EAssetTypeCategories::Type MyAssetCategory;
};