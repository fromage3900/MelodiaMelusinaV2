// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Actions/ACFChooserAction.h"
#include "ACFSustainedChooserAction.generated.h"

/**
 * Chooser action with sustained/hold-release mechanics.
 *
 * Combines:
 * - Deterministic weighted random selection from UACFChooserAction (network-ready)
 * - Hold/release input behavior (sustained mechanics)
 *
 * Use Cases:
 * - Charge attacks with animation variety
 * - Block stances with directional variations
 * - Aim modes with weapon-specific poses
 *
 * GAS Compliance:
 * - Inherits all network-ready chooser logic from UACFChooserAction
 * - Uses prediction key as random seed
 * - Perfect client-server synchronization
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew)
class ASCENTCOMBATFRAMEWORK_API UACFSustainedChooserAction : public UACFChooserAction
{
    GENERATED_BODY()

public:
    UACFSustainedChooserAction();

    // Inherits all chooser properties from UACFChooserAction:
    // - ChooserTable
    // - Randomize
    // - WeightColumnIndex
    // - RepeatProbabilityMultiplier
    // - SetChooserParams()

    // ============================================================================
    // SUSTAINED ACTION PROPERTIES (copied from UACFSustainedAction)
    // ============================================================================

    /** State of the sustained action */
    UPROPERTY(BlueprintReadOnly, Category = "ACF")
    ESustainedActionState ActionState = ESustainedActionState::ENotStarted;

    /** Tag of the action to trigger when released */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    FGameplayTag ReleaseActionTag;

    /** Priority of the release action */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    EActionPriority ReleaseActionPriority = EActionPriority::EHigh;

    /** Called when input is released */
    UFUNCTION(BlueprintCallable, Category = "ACF")
    virtual void ReleaseAction();

    /** Play a specific section of the montage */
    UFUNCTION(BlueprintCallable, Category = "ACF")
    void PlayActionSection(FName sectionName);

    /** Get elapsed time since action started */
    UFUNCTION(BlueprintPure, Category = "ACF")
    float GetActionElapsedTime() const;

private:
    /** Server RPC to play montage section on server (replicates to all clients) */
    UFUNCTION(Server, Reliable)
    void Server_PlayActionSection(FName sectionName);

protected:
    virtual void OnActionStarted_Implementation() override;
    virtual void OnActionEnded_Implementation() override;

private:
    /** Time when action started */
    float startTime = 0.f;
};
