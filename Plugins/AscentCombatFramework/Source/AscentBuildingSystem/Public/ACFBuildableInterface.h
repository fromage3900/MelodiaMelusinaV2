// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include <UObject/Interface.h>

#include "ACFBuildableInterface.generated.h"

UINTERFACE(MinimalAPI)
class UACFBuildableInterface : public UInterface {
    GENERATED_BODY()
};

class UACFBuildableEntityComponent;
struct FGameplayTag;

/**
 *
 */
class ASCENTBUILDINGSYSTEM_API IACFBuildableInterface {
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnPlaced();

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnDismantled();

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    bool IsPlacementValid(const FVector& Location, const FRotator& Rotation);
    virtual bool IsPlacementValid_Implementation(const FVector& Location, const FRotator& Rotation)
    {
        return true;
    }

    virtual UACFBuildableEntityComponent* GetBuildingSystemComponent() const { return nullptr; };
};
