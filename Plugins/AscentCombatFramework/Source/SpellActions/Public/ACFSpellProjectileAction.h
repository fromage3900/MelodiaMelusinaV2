// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Actions/ACFActionAbility.h"
#include "Actions/ACFComboAction.h"
#include "CoreMinimal.h"

#include "ACFSpellProjectileAction.generated.h"

class UACFProjectile;

/**
 * Action that spawns a projectile as part of a combo step.
 * Allows configuration of projectile class, direction, and launch sockets.
 */
UCLASS()
class SPELLACTIONS_API UACFSpellProjectileAction : public UACFComboAction {
    GENERATED_BODY()

public:
    // Sets default values for this action
    UACFSpellProjectileAction();

protected:
    /**
     * Class of the projectile to spawn when this action is executed.
     */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    TSubclassOf<class UACFProjectile> ProjectileClass;

    /**
     * The direction in which the projectile will be shot.
     */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    EShootDirection ShootDirection;

    /**
     * The socket(s) from which the projectile will be launched.
     * Index corresponds to the combo counter at the moment of execution.
     */
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACF)
    TArray<FName> LaunchSocketNames;

    /**
     * Gets the socket name to use for projectile launch based on current combo state.
     * @return The name of the socket to launch from.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FName GetDesiredSocketName() const;

    virtual void OnNotablePointReached_Implementation() override;
};
