// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACMTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACMImpactsFXDataAsset.generated.h"

/**
 *
 */
UCLASS()
class COLLISIONSMANAGER_API UACMImpactsFXDataAsset : public UPrimaryDataAsset {
    GENERATED_BODY()

protected:
    /**
     * Maps specific UDamageType classes to their corresponding impact effects array.
     * This allows playing different impact FX based on the damage type.
     */
    UPROPERTY(EditDefaultsOnly, Category = ACM)
    TMap<TSubclassOf<class UDamageType>, FImpactsArray> ImpactFXsByDamageType;

public:
    UFUNCTION(BlueprintCallable, Category = ACM)
    bool TryGetImpactFX(const TSubclassOf<class UDamageType>& damageImpacting, class UPhysicalMaterial* materialImpacted, FBaseFX& outFXtoPlay) const;
};
