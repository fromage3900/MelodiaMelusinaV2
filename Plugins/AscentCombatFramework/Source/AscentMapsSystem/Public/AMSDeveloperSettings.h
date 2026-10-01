// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include <GameplayTagContainer.h>

#include "AMSDeveloperSettings.generated.h"


class UAMSMarkersConfigDataAsset;
class UAMSCompassConfigDataAsset;

/**
 *
 */
UCLASS(config = Plugins, Defaultconfig, meta = (DisplayName = "Ascent Navigation Settings"))
class ASCENTMAPSSYSTEM_API UAMSDeveloperSettings : public UDeveloperSettings {
    GENERATED_BODY()

public:
    UAMSMarkersConfigDataAsset* GetMarkerIconConfig() const;


protected:
    UPROPERTY(config, EditAnywhere, Category = Style, meta = (AllowedClasses = "/Script/AscentMapsSystem.AMSMarkersConfigDataAsset"))
    FSoftObjectPath MarkerIconConfig;

};
