// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCoreTypes.h"
#include "CoreMinimal.h"
#include <UObject/Interface.h>
#include "ACFEntityInterface.generated.h"

// This class does not need to be modified.
UINTERFACE(MinimalAPI)
class UACFEntityInterface : public UInterface {
    GENERATED_BODY()
};

/**
 * 
 */
class ASCENTCOREINTERFACES_API IACFEntityInterface {
    GENERATED_BODY()

    // Add interface functions to this class. This is the class that will be inherited to implement this interface.
public:
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    FGameplayTag GetEntityCombatTeam() const;

    /*Returns the radius of a sphere that can include all the mesh of the character. 
    Used for warp and distance calculations*/
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	float GetEntityExtentRadius() const;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool IsEntityAlive() const;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void AssignTeamToEntity(FGameplayTag inCombatTeam);
};
