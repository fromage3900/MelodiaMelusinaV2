// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTags.h"
#include <Engine/Texture2D.h>

#include "ACFBuildRecipe.generated.h"

struct FBaseItem;

/**
 * Data Asset that defines a building recipe used by the Ascent Building System.
 * Contains the type of buildable actor, required materials, items returned after dismantle,
 * and UI-related data like name and icon.
 */
UCLASS()
class ASCENTBUILDINGSYSTEM_API UACFBuildRecipe : public UPrimaryDataAsset {
    GENERATED_BODY()

public:
    /** Display name of the building, used for UI purposes. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
    FText BuildingName;

    /** Icon of the building, displayed in UI. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
    TObjectPtr<UTexture2D> BuildingIcon;

    /** Description of the building, used for UI purposes. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
    FText Description;

    /** Actor type to be built. Must implement IACFBuildableInterface. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building", meta = (MustImplement = "/Script/AscentBuildingSystem.ACFBuildableInterface"))
    TSoftClassPtr<AActor> ItemType;

    /** Items required to construct this building. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
    TArray<FBaseItem> RequiredItems;

    /** Items returned when this building is dismantled. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Building")
    TArray<FBaseItem> ReturnedItems;
};
