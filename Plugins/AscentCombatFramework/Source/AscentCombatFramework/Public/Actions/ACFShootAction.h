// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFItemTypes.h"
#include "Actions/ACFActionAbility.h"
#include "CoreMinimal.h"

#include "ACFShootAction.generated.h"

/**
 * Ability used to perform a ranged attack by spawning a projectile.
 * Supports directional offset, projectile override, and target filtering.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFShootAction : public UACFActionAbility {
    GENERATED_BODY()

    UACFShootAction();

protected:


    /** Optional override for the projectile class to spawn */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ACF)
    TSubclassOf<class UACFProjectile> ProjectileOverride;

    /** Directional offset applied to the controller rotation */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ACF)
    FRotator DeltaDirection;

    /** Target selection logic for the shooting action */
    UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ACF)
    EShootTargetType SwipeTargetType;

    UFUNCTION(BlueprintPure, Category = ACF)
    bool GetSwipeResult(FHitResult& outResult) const;

    UFUNCTION(BlueprintPure, Category = ACF)
    AACFRangedWeaponActor* GetRangedWeapon() const
    {
        return rangedWeapon;
    }

    // Checks if the ability can be activated based on the current actor info and tag
    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayTagContainer* SourceTags = nullptr, const FGameplayTagContainer* TargetTags = nullptr, OUT FGameplayTagContainer* OptionalRelevantTags = nullptr)
        const override;
    virtual void OnNotablePointReached_Implementation() override;
    virtual void OnActionStarted_Implementation() override;
private:
    bool bSwipeSuccess = false;

    FHitResult ShootResult;

    TObjectPtr<AACFRangedWeaponActor> rangedWeapon;
};
