// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCoreTypes.h"
#include "CoreMinimal.h"
#include <UObject/Interface.h>

#include "ACFInteractableInterface.generated.h"


// This class does not need to be modified.
UINTERFACE(MinimalAPI)
class UACFInteractableInterface : public UInterface {
    GENERATED_BODY()
};

/**
 * Interface for actors that can be interacted with by a pawn.
 * Implement this interface to define interaction logic, availability, and display name.
 */
class ASCENTCOREINTERFACES_API IACFInteractableInterface {
    GENERATED_BODY()

public:
    /**
     * Called when the pawn performs a replicated interaction on this actor.
     *
     * @param Pawn The interacting pawn.
     * @param interactionType Optional string describing the interaction type (e.g., "Talk", "PickUp").
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");

    /**
     * Called when the pawn performs a local (non-replicated) interaction on this actor.
     *
     * @param Pawn The interacting pawn.
     * @param interactionType Optional string describing the interaction type.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnLocalInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");

    /**
     * Called when this actor enters the pawn's detection area and is considered interactable.
     *
     * @param Pawn The pawn that registered this interactable.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractableRegisteredByPawn(class APawn* Pawn);

    /**
     * Called when this actor exits the pawn's detection area or is no longer considered interactable.
     *
     * @param Pawn The pawn that unregistered this interactable.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractableUnregisteredByPawn(class APawn* Pawn);

    /**
     * Returns the display name of the interactable actor.
     * Used for UI purposes (e.g., interaction prompts).
     *
     * @return A localized text representing the name of the interactable.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    FText GetInteractableName();

    /**
     * Checks whether the actor can currently be interacted with by the specified pawn.
     * Used to filter available interactables.
     *
     * @param Pawn The interacting pawn.
     * @return True if the actor is interactable by the given pawn.
     */
    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    bool CanBeInteracted(class APawn* Pawn);
    virtual bool CanBeInteracted_Implementation(class APawn* Pawn)
    {
        return true;
    }
};
