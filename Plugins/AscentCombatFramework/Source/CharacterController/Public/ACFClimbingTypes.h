// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2024. All Rights Reserved.

#pragma once

#include "Animation/AnimMontage.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "ACFClimbingTypes.generated.h"

/**
 * Cardinal directions used to select the appropriate climbing montage
 * when jumping between grip points.
 */
UENUM(BlueprintType)
enum class EClimbingDirection : uint8
{
    Up      UMETA(DisplayName = "Up"),
    Down    UMETA(DisplayName = "Down"),
    Left    UMETA(DisplayName = "Left"),
    Right   UMETA(DisplayName = "Right"),
    UpLeft  UMETA(DisplayName = "UpLeft"),
    UpRight UMETA(DisplayName = "UpRight"),
    DownLeft UMETA(DisplayName = "DownLeft"),
    DownRight UMETA(DisplayName = "DownRight"),
};

/**
 * Maps a climbing direction to an animation montage and a gameplay ability tag.
 * Used inside UACFClimbingMontageDataAsset.
 */
USTRUCT(BlueprintType)
struct CHARACTERCONTROLLER_API FClimbingDirectionEntry
{
    GENERATED_BODY()

    FClimbingDirectionEntry()
    {
        Direction = EClimbingDirection::Up;
        Montage = nullptr;
        AbilityTag = FGameplayTag();
    }

    /** The direction this entry covers. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    EClimbingDirection Direction;

    /** Montage to play when moving in this direction between grip points. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TObjectPtr<UAnimMontage> Montage;

    /** Tag of the ACF action ability to trigger for this direction. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Actions"), Category = ACF)
    FGameplayTag AbilityTag;

    FORCEINLINE bool operator==(const EClimbingDirection& Other) const { return Direction == Other; }
    FORCEINLINE bool operator!=(const EClimbingDirection& Other) const { return Direction != Other; }
};

UCLASS()
class CHARACTERCONTROLLER_API UACFClimbingTypes : public UObject
{
    GENERATED_BODY()
};
