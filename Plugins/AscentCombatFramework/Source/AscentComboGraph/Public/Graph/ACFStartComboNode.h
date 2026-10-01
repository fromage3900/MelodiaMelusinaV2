// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Graph/ACFComboNode.h"
#include <GameplayTagContainer.h>

#include "ACFStartComboNode.generated.h"


/**
 *
 */
UCLASS()
class ASCENTCOMBOGRAPH_API UACFStartComboNode : public UACFComboNode {
    GENERATED_BODY()

public:
    UACFStartComboNode();

#if WITH_EDITOR

    virtual FText GetNodeTitle() const
    {
        if (ComboMontage) {
            return FText::FromString(ComboMontage->GetName().Left(12));
        }
        return FText::FromString("Start Combo");
    }

#endif

    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetTriggeringAction() const {
        return triggeringAction;
    }

protected:
    UPROPERTY(EditAnywhere, Category = ACF)
    FGameplayTag triggeringAction;
};
