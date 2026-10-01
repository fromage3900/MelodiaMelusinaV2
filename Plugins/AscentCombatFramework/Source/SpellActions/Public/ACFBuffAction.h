// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFBuffAction.generated.h"

/**
 *
 */
UCLASS()
class SPELLACTIONS_API UACFBuffAction : public UACFActionAbility {
    GENERATED_BODY()

protected:
    /*Timed buffer to be applied by this ability */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACF)
    FTimedAttributeSetModifier BuffToApply;

    virtual void OnNotablePointReached_Implementation() override;
};
