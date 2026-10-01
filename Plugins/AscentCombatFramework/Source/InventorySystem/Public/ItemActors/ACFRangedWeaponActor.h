// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFWeaponActor.h"
#include "CoreMinimal.h"
#include "Components/ACFShootingComponent.h"

#include "ACFRangedWeaponActor.generated.h"

class UACFRangedWeapon;


/**
 * Actor class representing a ranged weapon in the ACF framework.
 * Handles logic for shooting projectiles in various ways and managing reloading behavior.
 */
UCLASS()
class INVENTORYSYSTEM_API AACFRangedWeaponActor : public AACFWeaponActor {
    GENERATED_BODY()

public:
    // Sets default values for this actor
    AACFRangedWeaponActor();

    
    /**
     * Shoots a projectile using the owner's eyesight direction.
     * @param deltaRot Optional rotation offset applied to the aim direction.
     * @param charge Multiplier affecting projectile behavior (e.g., speed or damage).
     * @param projectileOverride Optional projectile class to override the default one.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    virtual void Shoot(const FRotator& deltaRot = FRotator::ZeroRotator, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr);

    /**
     * Shoots a projectile at a specific target actor.
     * @param target Actor to shoot at.
     * @param randomDeviation Amount of random deviation (in degrees) applied to the aim.
     * @param charge Multiplier affecting projectile behavior.
     * @param projectileOverride Optional projectile class to override the default one.
     */
    UFUNCTION(BlueprintCallable,  Category = ACF)
    virtual void ShootAtActor(const AActor* target, float randomDeviation = 5.f, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr);

    /*Shoots at the provided direction */
    UFUNCTION(BlueprintCallable,  Category = ACF)
    void ShootAtDirection(const FRotator& direction, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr);

    /*Tries to swipe shoot in the direction of the provided actor*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool SwipeTraceShootAtActor(const AActor* target, FHitResult& outResult, float randomDeviation = 5.f);

    /*Tries to swipe shoot following the targetType rule*/
    UFUNCTION(BlueprintCallable,  Category = ACF)
    bool SwipeTraceShoot(EShootTargetType targetType, FHitResult& outResult);

    /*Tries to shoot the provided projectile or the one equipped in the Ammo slot following the targetType rule*/
    UFUNCTION(BlueprintCallable,Category = ACF)
    void ShootProjectile(EShootTargetType targetType = EShootTargetType::WeaponTowardsFocus, float charge = 1.f, TSubclassOf<class UACFProjectile> projectileOverride = nullptr);

    UFUNCTION(BlueprintCallable, Category = ACF)
    void Reload(bool bTryToEquipAmmo);

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnReload();
    
    /*
    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetProjectileSpeed() const
    {
        return ShootingComp ? ShootingComp->GetProjectileSpeed() : -1.f;
    }*/

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetAmmoMagazine() const
    {
        return ShootingComp->GetAmmoMagazine();
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE float GetCurrentAmmo() const
    {
        return ShootingComp->GetCurrentAmmoInMagazine();
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE FVector GetShootingSocket() const
    {
        return ShootingComp->GetShootingSocketPosition();
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    EShootingType GetShootingType() const;


    UFUNCTION(BlueprintPure, Category = ACF)
    FORCEINLINE UACFShootingComponent* GetShootingComponent() const
    {
        return ShootingComp;
    }

    UFUNCTION(BlueprintPure, Category = ACF)
    bool CanShoot() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    bool NeedsReload() const;

    UFUNCTION(BlueprintPure, Category = ACF)
    UACFRangedWeapon* GetRangedWeaponDefinition() const;
   

    virtual void OnRep_ItemOwner() override;

    void InitShooting();

   virtual void InitItemActor(APawn* inOwner, UACFItem* inItemDefinition) override;


protected:
    virtual void BeginPlay() override;

    UPROPERTY(BlueprintReadOnly, VisibleAnywhere, Category = ACF)
    TObjectPtr<class UACFShootingComponent> ShootingComp;
};
