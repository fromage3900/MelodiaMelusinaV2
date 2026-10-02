// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ARSLevelingSystemDataAsset.h"

void UARSLevelingSystemDataAsset::GetAllAttributesValueByLevel(const int32 level, TArray<FAttribute>& outAttributes) const
{
    for (const auto& localatt : AttributesByLevelCurves) {
        if (localatt.ValueByLevelCurve) {
            FAttribute item(localatt.PrimaryAttributesTag, localatt.ValueByLevelCurve->GetFloatValue(level));
            outAttributes.AddUnique(item);
        }
    }
}




