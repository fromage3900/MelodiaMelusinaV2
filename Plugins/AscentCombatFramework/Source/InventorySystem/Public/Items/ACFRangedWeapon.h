// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ACFShootingComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFWeapon.h"

#include "ACFRangedWeapon.generated.h"

/**
 *
 */
UCLASS()
class INVENTORYSYSTEM_API UACFRangedWeapon : public UACFWeapon {
    GENERATED_BODY()

public:
    UACFRangedWeapon();

    UFUNCTION(BlueprintPure, Category = ACF)
    EShootingType GetShootingType() const
    {
        return ShootingType;
    }

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = "ACF|Weapon|Ranged")
    EShootingType ShootingType = EShootingType::EProjectile;

    UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "ShootingType == EShootingType::ESwipeTrace"), EditAnywhere, Category = "ACF|Weapon|Ranged")
    float ShootRadius = 1.f;

private:
};
