// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Animation/AnimInstance.h"
#include "CoreMinimal.h"

#include "ACFAnimLayer.generated.h"

/**
 *
 */
UCLASS()
class CHARACTERCONTROLLER_API UACFAnimLayer : public UAnimInstance {
    GENERATED_BODY()

public:
    /*Called when this layer is activated*/
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnActivated();
    virtual void OnActivated_Implementation();

    /*Called when the action is finished. Normally if BindActionToAnimation is set to true
        this is called when the animation is finished*/
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnDeactivated();
    virtual void OnDeactivated_Implementation();
};
