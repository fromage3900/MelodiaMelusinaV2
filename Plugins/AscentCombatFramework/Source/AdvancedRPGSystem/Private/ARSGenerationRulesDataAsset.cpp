// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ARSGenerationRulesDataAsset.h"
#include "ARSTypes.h"
#include "GameplayTagContainer.h"

bool UARSGenerationRulesDataAsset::TryGetGenerationRulesForPrimaryAttributes(const FGameplayTag& primaryAttribute, FGenerationRule& outRule) const
{
    if (AttributesGenerationRules.Contains(primaryAttribute)) {
        outRule = *(AttributesGenerationRules.FindByKey(primaryAttribute));
        return true;
    }
    return false;
}
