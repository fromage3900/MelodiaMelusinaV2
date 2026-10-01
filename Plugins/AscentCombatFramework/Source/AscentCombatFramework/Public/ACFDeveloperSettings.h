// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "Game/ACFTypes.h"
#include <AttributeSet.h>
#include <Curves/CurveFloat.h>
#include <GameplayTagContainer.h>

#include "ACFDeveloperSettings.generated.h"

UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Combat Settings"))
class ASCENTCOMBATFRAMEWORK_API UACFDeveloperSettings : public UDeveloperSettings {
    GENERATED_BODY()

public:
    UACFDeveloperSettings();

    /*Default COMBAT TAGS */

    UPROPERTY(EditAnywhere, config, meta = (Categories = "Actions"), Category = "ACF|Default Tags")
    FGameplayTag DefaultHitState;

    UPROPERTY(EditAnywhere, config, meta = (Categories = "Actions"), Category = "ACF|Default Tags")
    FGameplayTag DefaultDeathState;

    /** When true, the game is running as a demo build (e.g. for packaging). Use UACFFunctionLibrary::IsDemoVersion() to read at runtime. */
    UPROPERTY(EditAnywhere, config, Category = "ACF|Packaging")
    bool bIsDemoVersion = false;
};
