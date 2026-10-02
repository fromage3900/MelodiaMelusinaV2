// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AGSGraphEdge.h"
#include <GameplayTagContainer.h>
#include "AQSEdge.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTQUESTSYSTEM_API UAQSEdge : public UAGSGraphEdge
{
    GENERATED_BODY()

public: 

      UAQSEdge();

    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE FName GetTransitionName() const {
        return TransitionName;
    }

protected: 

    UPROPERTY(EditDefaultsOnly, Category = AQS)
    FName TransitionName;
};
