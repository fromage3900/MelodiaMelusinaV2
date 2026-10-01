// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACMTypes.h"
#include "CoreMinimal.h"
#include "Items/ACFEquippableItem.h"
#include <Engine/StaticMesh.h>

#include "ACFProjectile.generated.h"

class AACFProjectileActor;
class UStaticMesh;

/**
 * Represents a projectile that can be equipped and fired
 */
UCLASS()
class INVENTORYSYSTEM_API UACFProjectile : public UACFEquippableItem {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    UACFProjectile();

    /**
     * Returns the attribute modifier
     * @return The attribute set modifier.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UStaticMesh* GetProjectileMesh() const
    {
        return ProjectileMesh.LoadSynchronous();
    }

    //virtual TSubclassOf<AACFItemActor> GetItemActorClass_Implementation() const override { return ProjectileClass; }

    // The Mesh to be used when this weapon is equipped
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Projectile")
    TSoftObjectPtr<UStaticMesh> ProjectileMesh;

    // For physically simulated projectiles, the projectile class to be spawned
    UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = "ACF|Projectile")
    TSubclassOf<AACFProjectileActor> ProjectileClass;
};
