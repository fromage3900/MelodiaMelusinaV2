// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AMSDeveloperSettings.h"
#include "AMSMarkersConfigDataAsset.h"

UAMSMarkersConfigDataAsset* UAMSDeveloperSettings::GetMarkerIconConfig() const
{
    return Cast<UAMSMarkersConfigDataAsset>(MarkerIconConfig.TryLoad());
}
