  // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Interfaces/ACFInteractableInterface.h"

#include "ACFBaseInteractableActor.generated.h"

class UACFInteractableComponent;
class USceneComponent;

/**
 * Base class for interactable actors.
 *
 * UACFInteractableComponent drives the full interaction lifecycle automatically
 * (state tracking, ability triggering, delegates). No manual forwarding needed.
 *
 * IACFInteractableInterface is implemented here as empty BlueprintNativeEvents
 * so subclasses (Blueprint or C++) can hook into interaction events with
 * custom logic on top of what the component already handles.
 */
UCLASS(Blueprintable, BlueprintType, ClassGroup = (ACF), Abstract)
class ASCENTCOMBATFRAMEWORK_API AACFBaseInteractableActor : public AActor, public IACFInteractableInterface
{
    GENERATED_BODY()

public:
    AACFBaseInteractableActor();

    // ── IACFInteractableInterface ─────────────────────────────────────────────
    // Override these in subclasses to react to interaction events.
    // The component already handles state/abilities/delegates automatically.

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Interactable")
    void OnInteractedByPawn(APawn* Pawn, const FString& interactionType);
    virtual void OnInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType) override {}

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Interactable")
    void OnLocalInteractedByPawn(APawn* Pawn, const FString& interactionType);
    virtual void OnLocalInteractedByPawn_Implementation(APawn* Pawn, const FString& interactionType) override {}

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Interactable")
    void OnInteractableRegisteredByPawn(APawn* Pawn);
    virtual void OnInteractableRegisteredByPawn_Implementation(APawn* Pawn) override {}

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Interactable")
    void OnInteractableUnregisteredByPawn(APawn* Pawn);
    virtual void OnInteractableUnregisteredByPawn_Implementation(APawn* Pawn) override {}

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Interactable")
    FText GetInteractableName();
    virtual FText GetInteractableName_Implementation() override;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "ACF|Interactable")
    bool CanBeInteracted(APawn* Pawn);
    virtual bool CanBeInteracted_Implementation(APawn* Pawn) override { return true; }

    // ── Accessors ─────────────────────────────────────────────────────────────

    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    UACFInteractableComponent* GetInteractableComponent() const { return InteractableComponent; }

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Interactable")
    TObjectPtr<UACFInteractableComponent> InteractableComponent;
};
