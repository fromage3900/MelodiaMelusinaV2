// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Factory/ACFDataAssetFactory.h"
#include "ACFAssetCreatorClassPicker.h"
#include "ACFEditorSubsystem.h"

UACFDataAssetFactory::UACFDataAssetFactory()
{
    bCreateNew = true;
    bEditAfterNew = true;
    DefaultAssetName = "NewDataAsset";
}

FString UACFDataAssetFactory::GetDefaultNewAssetName() const
{
    if (DefaultAssetName.IsEmpty()) {
        return Super::GetDefaultNewAssetName();
    }

    return DefaultAssetName;
}



UObject* UACFDataAssetFactory::FactoryCreateNew(UClass* InClass, UObject* InParent, FName InName, EObjectFlags Flags, UObject* Context, FFeedbackContext* Warn)
{
    return Super::FactoryCreateNew(InClass, InParent, InName, Flags, Context, Warn);
}

uint32 UACFDataAssetFactory::GetMenuCategories() const
{
    if (SupportedClass == nullptr || SupportedClass == UBlueprint::StaticClass() || GetOuter()->GetName() == "/Engine/Transient") {
        return 0;
    }

    return Super::GetMenuCategories();
}

/*
bool UACFDataAssetFactory::ConfigureProperties()
{
    if (UseClassPicker) {
        TSharedRef<SACFAssetCreatorClassPicker> Dialog = SNew(SACFAssetCreatorClassPicker);
        return Dialog->ConfigureProperties(this);
    }

    return true;
}*/

