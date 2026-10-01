// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFWeaponActor.h"
#include "CoreMinimal.h"
#include "Items/ACFMeleeWeapon.h"

#include "ACFMeleeWeaponActor.generated.h"

class UACFMeleeWeapon;
/**
 * Delegate triggered when the melee weapon hits a target during a swing.
 * Broadcasts the hit result of the collision.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnWeaponHit, FHitResult, HitResult);

/**
 * A melee weapon class that handles swing detection and triggers hit events.
 */
UCLASS()
class INVENTORYSYSTEM_API AACFMeleeWeaponActor : public AACFWeaponActor {
    GENERATED_BODY()

public:

    AACFMeleeWeaponActor();

    // Delegate called when the weapon hits a valid target
    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnWeaponHit OnWeaponHit;

    /**
     * Starts the weapon swing and begins collision detection using trace channels.
     * @param traceChannels List of trace profile names to use during the swing.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StartWeaponSwing(const TArray<FName>& traceChannels);

    /**
     * Stops the weapon swing and ends collision detection.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void StopWeaponSwing();

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFMeleeWeapon* GetMeleeWeaponDefinition() const
    {
        return Cast<UACFMeleeWeapon>(GetItemDefinition());
    }

    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

protected:
    virtual void OnWeaponUnsheathed_Implementation() override;

    virtual void OnWeaponSheathed_Implementation() override;

private:
    UFUNCTION()
    void HandleAttackHit(const FHitResult& HitResult);

    UPROPERTY()
    float VFXCylinderHeight;
};
