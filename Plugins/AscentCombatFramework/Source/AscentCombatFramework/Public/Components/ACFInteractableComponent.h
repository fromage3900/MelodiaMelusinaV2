// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "GameplayTagContainer.h"
#include "Game/ACFTypes.h"
#include "CCMTypes.h"

#include "ACFInteractableComponent.generated.h"

// ── Delegates ────────────────────────────────────────────────────────────────

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnACFInteractionOccurred, APawn*, InteractorPawn);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnACFInteractionStateChanged, EACFInteractionState, NewState);

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Add this component to any actor to make it interactable. No code needed on the actor.
 *
 * UACFInteractionComponent detects this component automatically and drives the full
 * interaction lifecycle (register, interact, unregister, state tracking) without
 * requiring the actor to implement IACFInteractableInterface.
 *
 * If the actor does implement IACFInteractableInterface, both paths are respected:
 * the component handles state/ability/events, the interface adds custom actor logic on top.
 *
 * Being a USceneComponent, position it inside the actor in the editor viewport:
 * its world transform is the motion-warp destination used by UACFInteractActionAbility.
 */
UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTCOMBATFRAMEWORK_API UACFInteractableComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    UACFInteractableComponent();

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

    // ── Interaction callbacks ─────────────────────────────────────────────────
    // Called automatically by UACFInteractionComponent.
    // Can also be called manually from Blueprint if custom wiring is needed.

    /**
     * Server: triggers InteractionActionTag on the interactor's ability system,
     * sets state to Busy, and broadcasts OnInteractionOccurred.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void HandleInteractedByPawn(class APawn* Pawn, const FString& InteractionType);

    /**
     * Client: broadcasts OnLocalInteractionOccurred.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void HandleLocalInteractedByPawn(class APawn* Pawn, const FString& InteractionType);

    /**
     * Called when a pawn enters the detection area and registers this interactable.
     * Stores the registered interactor and broadcasts OnInteractorRegistered.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void HandleInteractableRegisteredByPawn(class APawn* Pawn);

    /**
     * Called when the registered pawn leaves the detection area.
     * Clears the stored interactor, broadcasts OnInteractorUnregistered,
     * and resets the interaction state to Free when bResetStateOnUnregister is true.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void HandleInteractableUnregisteredByPawn(class APawn* Pawn);

    // ── State management ──────────────────────────────────────────────────────

    /**
     * Explicitly ends the current interaction and resets state to Free.
     * Call this from the ability's OnActionEnded or a Blueprint event.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void EndInteraction();

    // ── Getters ──────────────────────────────────────────────────────────────

    /** Returns the display name for UI interaction prompts. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    FText GetInteractableName() const { return DefaultInteractableName; }

    /**
     * Returns the optional examination/inspection texts to display in the
     * interaction widget (e.g. "Examine" prompts). Empty by default.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    const TArray<FText>& GetExaminationTexts() const { return ExaminationTexts; }

    /**
     * Returns the examination text at the given index, or an empty FText if
     * out of range. Convenience for widgets that paginate through the entries.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    FText GetExaminationTextAt(int32 Index) const
    {
        return ExaminationTexts.IsValidIndex(Index) ? ExaminationTexts[Index] : FText::GetEmpty();
    }

    /** Number of examination texts configured on this component. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    int32 GetNumExaminationTexts() const { return ExaminationTexts.Num(); }

    /**
     * Returns whether this interactable can currently accept a new interaction.
     * False when disabled or state is Busy (and bAllowInteractionWhileBusy is false).
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    bool CanBeInteracted(class APawn* Pawn) const;

    /** Current interaction state (Free / Busy). Replicated to all clients. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    EACFInteractionState GetInteractionState() const { return InteractionState; }

    /** The gameplay tag of the action ability triggered on the interacting pawn. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    FGameplayTag GetInteractionActionTag() const { return InteractionActionTag; }

    /** The optional montage override for the interactor's UACFInteractActionAbility. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    UAnimMontage* GetInteractionMontageOverride() const { return InteractionMontageOverride; }

    /** The optional camera event triggered by the interactor's UACFInteractActionAbility. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    FName GetInteractionCameraEventName() const { return CameraEventName; }

    /** Whether the local camera should lock onto the owner actor during interaction. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    bool ShouldLockCameraOnOwner() const { return bLockCameraOnOwner; }

    /** Lock type used when locking the camera on the owner actor. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    ELockType GetLockCameraType() const { return LockCameraType; }

    /** Interpolation strength used when locking the camera on the owner actor. */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    float GetLockCameraStrength() const { return LockCameraStrength; }

    /** Whether interaction is currently enabled (hard toggle). */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    bool IsInteractionEnabled() const { return bInteractionEnabled; }

    /**
     * Returns the pawn currently in an active interaction (state == Busy).
     * Null when no interaction is in progress.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    APawn* GetInteractingPawn() const { return InteractionState == EACFInteractionState::EBusy ? LastInteractorPawn.Get() : nullptr; }

    /** The last pawn that successfully interacted with the owner (server). */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    APawn* GetLastInteractorPawn() const { return LastInteractorPawn.Get(); }

    /** The pawn currently registered inside the detection area (in range, not necessarily interacting). */
    UFUNCTION(BlueprintPure, Category = "ACF|Interactable")
    APawn* GetCurrentRegisteredInteractor() const { return CurrentRegisteredInteractor.Get(); }

    // ── Setters ───────────────────────────────────────────────────────────────

    /** Hard-enables or disables interaction (independent from state). */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void SetInteractionEnabled(bool bEnabled);

    /** Directly overrides the interaction state. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Interactable")
    void SetInteractionState(EACFInteractionState NewState);

private:
    /** EditCondition helper — true when InteractionActionTag is assigned. */
    UFUNCTION()
    bool HasInteractionActionTag() const { return InteractionActionTag.IsValid(); }

    /** EditCondition helper — true when tag is set AND bLockCameraOnOwner is true. */
    UFUNCTION()
    bool HasInteractionActionTagAndLock() const { return InteractionActionTag.IsValid() && bLockCameraOnOwner; }

public:

    // ── Events ────────────────────────────────────────────────────────────────

    /** Fired (server) when a pawn successfully interacts with the owner. */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Interactable")
    FOnACFInteractionOccurred OnInteractionOccurred;

    /** Fired when a pawn registers the owner as a potential interactable (enters range). */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Interactable")
    FOnACFInteractionOccurred OnInteractorRegistered;

    /** Fired when a pawn unregisters the owner (leaves range). */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Interactable")
    FOnACFInteractionOccurred OnInteractorUnregistered;

    /** Fired (client) when the local interaction callback arrives. */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Interactable")
    FOnACFInteractionOccurred OnLocalInteractionOccurred;

    /** Fired whenever the interaction state changes (Free ↔ Busy). */
    UPROPERTY(BlueprintAssignable, Category = "ACF|Interactable")
    FOnACFInteractionStateChanged OnInteractionStateChanged;

protected:
    // ── Identity ──────────────────────────────────────────────────────────────

    /**
     * Display name used in interaction UI prompts (e.g. "Open Chest", "Talk to NPC").
     * Also used by examination widgets as the title of the inspected object.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable")
    FText DefaultInteractableName;

    // ── Action Ability ────────────────────────────────────────────────────────

    /**
     * Gameplay tag of the action ability to trigger on the interacting pawn.
     * The pawn must have this ability granted in its UACFAbilitySystemComponent.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Action Ability",
        meta = (Categories = "Actions,Ability"))
    FGameplayTag InteractionActionTag;

    /**
     * Optional montage override for the interactor's UACFInteractActionAbility.
     * When set, the ability plays this montage instead of its own default.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Action Ability",
        meta = (EditCondition = "HasInteractionActionTag()"))
    TObjectPtr<UAnimMontage> InteractionMontageOverride;

    /**
     * Optional camera event triggered when the interaction action ability starts.
     * Only used when InteractionActionTag is set.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Action Ability",
        meta = (EditCondition = "HasInteractionActionTag()"))
    FName CameraEventName = NAME_None;

    /**
     * When true, the local camera is locked onto the owner actor for the duration
     * of the interaction (client-only). Released at NotablePoint / ability end.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Action Ability",
        meta = (EditCondition = "HasInteractionActionTag()"))
    bool bLockCameraOnOwner = false;

    /** Axis constraint used when locking the camera on the owner actor. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Action Ability",
        meta = (EditCondition = "HasInteractionActionTagAndLock()", EditConditionHides))
    ELockType LockCameraType = ELockType::EAllAxis;

    /** Interpolation strength for the camera lock (higher = snappier). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Action Ability",
        meta = (EditCondition = "HasInteractionActionTagAndLock()", EditConditionHides, ClampMin = "0.1"))
    float LockCameraStrength = 5.f;

    // ── Behaviour ─────────────────────────────────────────────────────────────

    /**
     * Hard toggle. Set to false to permanently disable this interactable
     * without destroying the component.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Behaviour")
    bool bInteractionEnabled = true;

    /**
     * When true, multiple pawns can trigger this interactable simultaneously
     * (state never becomes Busy).  Default: false.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Behaviour")
    bool bAllowInteractionWhileBusy = false;

    /**
     * When true, the interaction state is automatically reset to Free when the
     * last registered interactor unregisters (leaves the detection area).
     * When false, call EndInteraction() explicitly from gameplay code.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Behaviour")
    bool bResetStateOnUnregister = false;

    // ── Examination ───────────────────────────────────────────────────────────

    /**
     * Optional pages of localized text shown by interaction/examination widgets
     * (e.g. an "Examine" popup with one or more pages). Leave empty for
     * interactables that don't need a textual prompt body.
     */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF|Interactable|Examination", meta = (MultiLine = true))
    TArray<FText> ExaminationTexts;

private:
    /** Current interaction state. Replicated so clients can react to Busy/Free changes. */
    UPROPERTY(ReplicatedUsing = OnRep_InteractionState, VisibleInstanceOnly, Category = "ACF|Interactable|Behaviour")
    EACFInteractionState InteractionState = EACFInteractionState::EFree;

    /** Last pawn that successfully interacted (server-side). */
    UPROPERTY(Transient)
    TWeakObjectPtr<APawn> LastInteractorPawn;

    /** Pawn currently registered inside the detection area. */
    UPROPERTY(Transient)
    TWeakObjectPtr<APawn> CurrentRegisteredInteractor;

    /** Internal helper to change state and broadcast the delegate. */
    void Internal_SetState(EACFInteractionState NewState);

    UFUNCTION()
    void OnRep_InteractionState();
};
