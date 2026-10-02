// Copyright (C) Developed by Pask & OlssonDev, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAssetAction.h"
#include "AssetTypeActions/AssetTypeActions_Blueprint.h"
#include "CoreMinimal.h"
#include "Factory/ACFDataAssetFactory.h"
PRAGMA_DISABLE_DEPRECATION_WARNINGS
#include <AssetTypeActions/AssetTypeActions_DataAsset.h>
PRAGMA_ENABLE_DEPRECATION_WARNINGS

#define LOCTEXT_NAMESPACE "FAssetTypeActions_AssetCreatorBase"

class FAssetTypeActions_AssetCreatorBase : public FAssetTypeActions_Blueprint {
public:
    FAssetTypeActions_AssetCreatorBase(const FAssetActionSettings& InSettings, uint32 InCategory)
    {
        Settings = InSettings;
        Category = InCategory;
    };

    // IAssetTypeActions interface
    virtual FColor GetTypeColor() const override;
    virtual FText GetName() const override;
    virtual uint32 GetCategories() override;
    virtual UClass* GetSupportedClass() const override;
    virtual const TArray<FText>& GetSubMenus() const override;
    virtual UFactory* GetFactoryForBlueprintType(UBlueprint* InBlueprint) const override;

    // End of IAssetTypeActions interface

protected:
    FAssetActionSettings Settings;
    uint32 Category;
};

PRAGMA_DISABLE_DEPRECATION_WARNINGS
class FAssetTypeActions_ACFDataAsset : public FAssetTypeActions_DataAsset {
public:
    FAssetTypeActions_ACFDataAsset(UClass* InClass, const FAssetActionSettings& InSettings, uint32 InCategory)
        : AssetClass(InClass)
        , Category(InCategory)
    {
        FactoryInstance = NewObject<UACFDataAssetFactory>();
        FactoryInstance->SupportedClass = InClass;
        Settings = InSettings;
        Name = InClass->GetFName();
    }

    virtual FText GetName() const override { return FText::FromName(Name); }
    virtual UClass* GetSupportedClass() const override ;
    virtual uint32 GetCategories() override { return Category; }

    virtual UFactory* GetFactory() const { return FactoryInstance; }

    const TArray<FText>& GetSubMenus() const override
    {
        if (Settings.UseSubMenu && !Settings.SubCategoryName.IsEmpty()) {
            static TArray<FText> NewSubMenusArray;
            NewSubMenusArray.Empty();
            NewSubMenusArray.Add(Settings.SubCategoryName);

            return NewSubMenusArray;
        }

        return FAssetTypeActions_Base::GetSubMenus();
    }

private:
    UClass* AssetClass;
    FName Name;
    uint32 Category;
    UACFDataAssetFactory* FactoryInstance;
    FAssetActionSettings Settings;
};
PRAGMA_ENABLE_DEPRECATION_WARNINGS

#undef LOCTEXT_NAMESPACE
