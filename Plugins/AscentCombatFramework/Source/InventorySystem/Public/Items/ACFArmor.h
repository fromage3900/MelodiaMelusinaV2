// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Items/ACFEquippableItem.h"

#include "ACFArmor.generated.h"

class USkinnedAsset;
class UACFArmorSlotComponent;

/**
 * Represents an equippable armor item.
 * Provides a method to retrieve the armor's skinned mesh based on the owning actor.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFArmor : public UACFEquippableItem {
    GENERATED_BODY()

public:
    // Sets default values for this armor item
    UACFArmor();

    /**
     * Returns the skinned mesh asset used for this armor, based on the given actor.
     * Can be overridden in Blueprint to provide dynamic meshes for gender specific meshes
     * @param actorOwner The actor who owns or equips the armor
     * @return Pointer to USkinnedAsset
     */
    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    TSoftObjectPtr<USkinnedAsset> GetArmorMesh(AActor* actorOwner) const;

    UFUNCTION(Blueprintpure, Category = ACF)
    TSubclassOf<UACFArmorSlotComponent> GetArmorComponentClass() const
    {
        return ArmorComponentClass;
    }

protected:
    // The skeletal mesh component representing the visual appearance of the armor
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Armor")
    TArray<TSoftObjectPtr<USkinnedAsset>> ArmorMeshes;

    // The  mesh component to be spawned to represent the visual appearance of the armor
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Armor")
    TSubclassOf<UACFArmorSlotComponent> ArmorComponentClass;
};
