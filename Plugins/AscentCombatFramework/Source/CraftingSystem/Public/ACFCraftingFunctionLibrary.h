// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFItemsManagerComponent.h"
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "ACFCraftingFunctionLibrary.generated.h"


/**
 *
 */
UCLASS()
class CRAFTINGSYSTEM_API UACFCraftingFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFLibrary)
    static UACFItemsManagerComponent* GetItemManager(UObject* WorldContextObject, int32 playerIndex = 0);
};
