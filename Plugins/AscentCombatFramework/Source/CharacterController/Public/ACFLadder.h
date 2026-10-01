// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/ACFInteractableInterface.h"

#include "ACFLadder.generated.h"

/**
 * Base ladder actor for ACF ladder climbing.
 *
 * Exposes IACFInteractableInterface as BlueprintNativeEvent so child Blueprints
 * can implement the full interaction and climbing logic without an extra C++ subclass.
 * Components (mesh, reach points, HasValidPlacement) are defined in the BP child.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (DisplayName = "ACF Ladder"))
class CHARACTERCONTROLLER_API AACFLadder : public AActor, public IACFInteractableInterface
{
    GENERATED_BODY()

public:
    AACFLadder();

    // ── IACFInteractableInterface ─────────────────────────────────────────────

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");
    virtual void OnInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnLocalInteractedByPawn(class APawn* Pawn, const FString& interactionType = "");
    virtual void OnLocalInteractedByPawn_Implementation(class APawn* Pawn, const FString& interactionType = "") override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractableRegisteredByPawn(class APawn* Pawn);
    virtual void OnInteractableRegisteredByPawn_Implementation(class APawn* Pawn) override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnInteractableUnregisteredByPawn(class APawn* Pawn);
    virtual void OnInteractableUnregisteredByPawn_Implementation(class APawn* Pawn) override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    FText GetInteractableName();
    virtual FText GetInteractableName_Implementation() override;
};
