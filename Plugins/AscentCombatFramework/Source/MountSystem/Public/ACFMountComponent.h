// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFMountableComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <GameplayTagContainer.h>

#include "ACFMountComponent.generated.h"

class UACFGroupAIComponent;


UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class MOUNTSYSTEM_API UACFMountComponent : public UACFMountableComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFMountComponent();

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE bool IsCompanion() const
    {
        return bIsPlayerCompanion;
    }

protected:
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bIsPlayerCompanion = false;

    virtual void SetMounted(bool inMounted) override;


};
