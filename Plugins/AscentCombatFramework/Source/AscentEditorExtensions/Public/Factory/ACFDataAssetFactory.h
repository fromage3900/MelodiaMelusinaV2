// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Factories/DataAssetFactory.h"
#include <Engine/DataAsset.h>

#include "ACFDataAssetFactory.generated.h"


/**
 *
 */
UCLASS(Blueprintable, NotBlueprintType /*Abstract,*/)
class ASCENTEDITOREXTENSIONS_API UACFDataAssetFactory : public UDataAssetFactory {
    GENERATED_BODY()

public:
    // The name this factory should name assets when they're created. If empty, will use default name of the class.
    UPROPERTY(EditDefaultsOnly, Category = "Asset Settings")
    FString DefaultAssetName;

    // If the factory should spawn a class picker window when creating the asset.
    UPROPERTY(EditDefaultsOnly, Category = "Class Picker")
    bool UseClassPicker = true;

    UACFDataAssetFactory();

    // Must be set before using the factory
    UClass* DataAssetClass;

    // UObject interface implementation
    virtual uint32 GetMenuCategories() const override;
 //   virtual bool ConfigureProperties() override;
    virtual FString GetDefaultNewAssetName() const override;
    // End of implementation

    // UFactory interface implementation
    virtual UObject* FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn) override;
    // End of implementation

private:
    UPROPERTY()
    UClass* OldClass;
};
