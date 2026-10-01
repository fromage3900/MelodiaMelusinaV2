// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Items/ACFItem.h"

#include "ACFQuestItem.generated.h"


/**
 * Represents a quest-specific item in the inventory system.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFQuestItem : public UACFItem {
    GENERATED_BODY()

public:
    UACFQuestItem();
};
