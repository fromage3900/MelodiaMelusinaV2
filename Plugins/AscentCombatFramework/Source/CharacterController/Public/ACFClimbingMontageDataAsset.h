// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#pragma once

#include "ACFClimbingTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFClimbingMontageDataAsset.generated.h"

/**
 * Data asset that maps climbing directions to animation montages and
 * the corresponding ACF action ability tags.
 *
 * Create a Blueprint subclass of this asset and fill in one entry per
 * direction your skeleton supports.  Assign it to UACFLedgeClimbingComponent.
 */
UCLASS(BlueprintType, Blueprintable, Category = ACF)
class CHARACTERCONTROLLER_API UACFClimbingMontageDataAsset : public UDataAsset
{
    GENERATED_BODY()

public:
    /**
     * Returns the entry for the requested direction.
     * @param Direction    The climbing direction to look up.
     * @param OutEntry     Filled with the matching entry if found.
     * @return             True if an entry was found.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool GetEntryForDirection(EClimbingDirection Direction, FClimbingDirectionEntry& OutEntry) const;

    /**
     * Retrieves just the montage for a given direction (convenience wrapper).
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    UAnimMontage* GetMontageForDirection(EClimbingDirection Direction) const;

    /**
     * Retrieves just the ability tag for a given direction.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetAbilityTagForDirection(EClimbingDirection Direction) const;

    /**
     * The angle (degrees) used to classify the input vector into one of the
     * 8 cardinal directions.  Default 22.5° gives equal 45° sectors.
     */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF, meta = (ClampMin = "5.0", ClampMax = "45.0"))
    float DirectionAngleThreshold = 22.5f;

protected:
    /** All direction-to-montage/ability mappings for this character skeleton. */
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    TArray<FClimbingDirectionEntry> DirectionEntries;
};
