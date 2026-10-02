// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "GameplayTagContainer.h"

#include "ACFConquestFunctionLibrary.generated.h"


class UACFConqueringComponent;
class AACFAssaultPoint;

/**
 *
 */
UCLASS()
class UNITSSYSTEM_API UACFConquestFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFConquestLibrary)
    static UACFConqueringComponent* GetLocalConqueringComponent(const UObject* WorldContextObject);

    UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = ACFConquestLibrary)
    static AACFAssaultPoint* GetAssaultPoint(const UObject* WorldContextObject, const FGameplayTag& pointTag);


};
