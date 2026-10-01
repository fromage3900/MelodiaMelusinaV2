// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Animation/ACFAnimTypes.h"
#include "CoreMinimal.h"
#include "Engine/DataAsset.h"

#include "ACFAnimsetDataAsset.generated.h"

class UACFIKLayer;
class UACFClimbingLayer;

/**
 * Designer-facing data asset that declares which animation layer classes a character can use.
 * Add one to UACFCharacterDataAsset::Fragments via ACFAnimsetFragment to populate the
 * AnimInstance layer look-up tables (MovesetLayers, OverlayLayers, RiderLayers, IK, Climbing)
 * at initialisation time. Does not change the active moveset or overlay — that remains
 * driven by equipment/weapon logic through UACFCharacterMovementComponent.
 */
UCLASS(BlueprintType)
class CHARACTERCONTROLLER_API UACFAnimsetDataAsset : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    // Moveset layers available to the character (tag → anim layer class)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (TitleProperty = "TagName"), Category = "ACF|Movesets")
    TArray<FMoveset> MovesetLayers;

    // Overlay layers available to the character (tag → anim layer class)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (TitleProperty = "TagName"), Category = "ACF|Overlays")
    TArray<FOverlayLayer> OverlayLayers;

    // Rider layers available to the character (tag → anim layer class)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (TitleProperty = "TagName"), Category = "ACF|Rider")
    TArray<FRiderLayer> RiderLayers;

    // IK layer class to assign (leave blank to keep the existing one)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|IK")
    TSubclassOf<UACFIKLayer> IKLayer;

    // Climbing layer class to assign (leave blank to keep the existing one)
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Climbing")
    TSubclassOf<UACFClimbingLayer> ClimbingLayer;
};
