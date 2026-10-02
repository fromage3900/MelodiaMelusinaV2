// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Items/ACFWorldItem.h"
#include <Curves/CurveFloat.h>
#include <GameplayTagContainer.h>

#include "ACFInventorySettings.generated.h"

UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Inventory Settings"))
class INVENTORYSYSTEM_API UACFInventorySettings : public UDeveloperSettings {
    GENERATED_BODY()

public:
    UACFInventorySettings();

    UPROPERTY(EditAnywhere, config, Category = "ACF| Defaults")
    FText DefaultCurrencyName = FText::FromString(TEXT("Coins"));

    UPROPERTY(EditAnywhere, config, Category = "ACF| Defaults")
    TSubclassOf<class AACFWorldItem> WorldItemClass;

    UPROPERTY(EditAnywhere, config, Category = "ACF| Defaults")
    TArray<TEnumAsByte<ECollisionChannel>> DefaultDamageTraceChannel;
};
