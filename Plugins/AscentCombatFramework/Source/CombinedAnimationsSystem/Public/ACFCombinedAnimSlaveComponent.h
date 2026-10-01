// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCombinedAnimComponent.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "ACFCombinedAnimSlaveComponent.generated.h"

/**
 * Component used on characters that can play contextual combined animations as slaves.
 * Evaluates animation tags and animation conditions to determine eligibility.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class COMBINEDANIMATIONSSYSTEM_API UACFCombinedAnimSlaveComponent : public UACFCombinedAnimComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFCombinedAnimSlaveComponent();

    /**
     * Sets the animation tags used by this slave to determine compatibility with combined animations.
     *
     * @param val The animation tags to assign.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetAnimTags(FGameplayTagContainer val) { AnimTags = val; }

    /**
     * Returns the animation tags currently set for this slave.
     *
     * @return The animation tags.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTagContainer GetAnimTags() const { return AnimTags; }

    /**
     * Checks if the slave can start a specific combined animation, based on its tags and conditions.
     *
     * @param combinedAnim The combined animation configuration to check.
     * @param animMaster The character attempting to synchronize this animation.
     * @return True if the slave can participate in the animation.
     */
    UFUNCTION(BlueprintCallable, Category = CAS)
    bool CanStartCombinedAnimation(const FCombinedAnimConfig& combinedAnim, const class ACharacter* animMaster);

    UFUNCTION(BlueprintCallable, Category = CAS)
    bool CanBeAmbushed(APawn* Pawn);

    /**
     * Replaces the array of starting conditions evaluated by this slave component.
     * Used by character fragments (e.g. UACFExecutionConditionsFragment) to inject
     * execution / contextual-anim conditions from a DataAsset at initialization time.
     *
     * @param InConditions The new conditions to use. Existing conditions are discarded.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetAnimStartingConditions(const TArray<class UCASAnimCondition*>& InConditions) { AnimStartingConditions = InConditions; }

    /** Returns the conditions currently evaluated by this slave component. */
    UFUNCTION(BlueprintPure, Category = ACF)
    const TArray<class UCASAnimCondition*>& GetAnimStartingConditions() const { return AnimStartingConditions; }

protected:
    UPROPERTY(EditAnywhere, Category = ACF)
    FGameplayTagContainer AnimTags;

    UPROPERTY(EditAnywhere, Category = ACF)
    FGameplayTag AmbushTag;

    UPROPERTY(EditDefaultsOnly, Instanced, Category = ACF)
    TArray<class UCASAnimCondition*> AnimStartingConditions;

    // Called when the game starts
    virtual void BeginPlay() override;

    bool VerifyConditions(const FCombinedAnimConfig& combinedAnim, const class ACharacter* animMaster);
};
