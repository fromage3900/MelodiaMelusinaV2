// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/ACFActionAbility.h"

#include "ACFInteractActionAbility.generated.h"

class UACFInteractableComponent;

/**
 * Default action ability for pawn-initiated interactions.
 *
 * Assign this ability (or a Blueprint subclass) to the interactor's ability set using the
 * same GameplayTag stored in UACFInteractableComponent::InteractionActionTag.
 * UACFInteractableComponent::HandleInteractedByPawn will then trigger it automatically.
 *
 * The ability:
 *  - Resolves UACFInteractableComponent from the actor the interactor is currently
 *    focusing (via UACFInteractionComponent::GetCurrentBestInteractableActor).
 *  - Overrides GetMontage() to use the component's MontageOverride when set,
 *    falling back to this ability's own animMontage.
 *  - Overrides GetWarpTransform() to return the component's world transform so
 *    the pawn smoothly flows to the position marked in the editor viewport.
 *
 * ActionConfig defaults to EMotionWarped with sync point "Interactable".
 * Add a MotionWarpingNotifyState in the montage to define the warp window, or
 * place UACFNotifyInteractWarp to update the warp target at a specific keyframe.
 */
UCLASS(Blueprintable, BlueprintType)
class ASCENTCOMBATFRAMEWORK_API UACFInteractActionAbility : public UACFActionAbility
{
    GENERATED_BODY()

public:
    UACFInteractActionAbility();

protected:
    /**
     * Returns the world transform of the interactable's UACFInteractableComponent
     * as the motion-warp target.
     */
    virtual FTransform GetWarpTransform_Implementation() override;

    /**
     * Returns the montage override from UACFInteractableComponent when present;
     * otherwise returns this ability's own animMontage.
     */
    virtual UAnimMontage* GetMontage_Implementation() const override;

    virtual void ClientsOnActionStarted_Implementation() override;
    virtual void ClientsOnNotablePointReached_Implementation() override;

    virtual void OnNotablePointReached_Implementation() override;

    virtual void EndAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayAbilityActivationInfo ActivationInfo, bool bReplicateEndAbility, bool bWasCancelled) override;

    virtual bool CanActivateAbility(const FGameplayAbilitySpecHandle Handle, const FGameplayAbilityActorInfo* ActorInfo,
        const FGameplayTagContainer* SourceTags = nullptr, const FGameplayTagContainer* TargetTags = nullptr,
        OUT FGameplayTagContainer* OptionalRelevantTags = nullptr) const override;

private:
    /** Resolves UACFInteractableComponent from the interactor's current best interactable. */
    UACFInteractableComponent* GetCurrentInteractableComponent() const;
};
