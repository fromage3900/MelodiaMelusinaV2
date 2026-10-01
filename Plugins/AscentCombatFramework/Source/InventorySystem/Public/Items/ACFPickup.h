// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFWorldItem.h"
#include "ARSTypes.h"
#include "Components/CapsuleComponent.h"
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "ACFPickup.generated.h"

/**
 * Represents a pickup item in the world that can be collected by characters.
 * Supports pickup on overlap and automatic equipment, as well as applying effects or buffs upon pickup.
 */
UCLASS()
class INVENTORYSYSTEM_API AACFPickup : public AACFWorldItem {
    GENERATED_BODY()

public:
    // Sets default values for this actor's properties
    AACFPickup();

protected:
    // Called when the game starts or when spawned
    virtual void BeginPlay() override;

    // If true, the pickup will be collected automatically when overlapping
    UPROPERTY(EditAnywhere, Category = ACF)
    bool bPickOnOverlap = true;

    // If true, the item will be automatically equipped when picked up
    UPROPERTY(EditAnywhere, Category = ACF)
    bool bAutoEquipOnPick = true;

    // The capsule component used to detect pickup overlap
    UPROPERTY(VisibleAnywhere, Category = ACF)
    TObjectPtr<UCapsuleComponent> PickUpCapsule;

    // List of permanent effects (e.g., stat modifications) applied when the item is picked up
    UPROPERTY(EditAnywhere, Category = ACF)
    TArray<FStatisticValue> OnPickupEffect;

    // List of temporary buffs applied to the character upon picking up the item
    UPROPERTY(EditAnywhere, Category = ACF)
    TArray<FTimedAttributeSetModifier> OnPickupBuff;

    // INTERACTION INTERFACE
    /* called when player interact with object of this class */
    virtual void OnInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;
    virtual void OnInteractableRegisteredByPawn_Implementation(class APawn* Pawn) override;
    // END INTERFACE
public:
};
