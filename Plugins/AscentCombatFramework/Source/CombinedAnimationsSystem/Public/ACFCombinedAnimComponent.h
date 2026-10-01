// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include <ContextualAnimSceneActorComponent.h>

#include "ACFCombinedAnimComponent.generated.h"

/**
 * Component responsible for managing combined (contextual) animations on a character.
 * Wraps a UContextualAnimSceneActorComponent and provides extra functionalities
 */
UCLASS(ClassGroup = (ACF), abstract, meta = (BlueprintSpawnableComponent))
class COMBINEDANIMATIONSSYSTEM_API UACFCombinedAnimComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFCombinedAnimComponent();

    /**
     * Returns whether ability triggers should be locked during contextual animations.
     * @return True if ability triggers are locked during combined animations.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|CombinedAnimations")
    bool GetLockAbilityTriggersDuringCombinedAnims() const { return bLockAbilityTriggersDuringCombinedAnims; }

    /**
     * Returns whether the character can be hit while in a contextual animation.
     * @return True if the actor is damageable during combined animations.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|CombinedAnimations")
    bool GetCanBeHitDuringCombinedAnims() const { return bCanBeHitDuringCombinedAnims; }

    /**
     * Returns whether the character can be hit while in a contextual animation.
     * @return True if the actor is damageable during combined animations.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|CombinedAnimations")
    bool GetIsPlayingContextualAnim() const { return bIsPlayingAContextualAnim; }

    /**
     * Returns the internal contextual animation component.
     * @return Pointer to the UContextualAnimSceneActorComponent used by this actor.
     */
    UFUNCTION(BlueprintPure, Category = "ACF|CombinedAnimations")
    UContextualAnimSceneActorComponent* GetContextualAnimComponent() const { return combinedAnimationComponent; }

    /**
     * Sets whether ability triggers should be locked during contextual animations.
     * @param val True to lock abilities, false to allow them.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|CombinedAnimations")
    void SetLockAbilityTriggersDuringCombinedAnims(bool val) { bLockAbilityTriggersDuringCombinedAnims = val; }

    /**
     * Sets whether the character can be hit while in a contextual animation.
     * @param val True to allow damage, false to make the actor invulnerable during the animation.
     */
    UFUNCTION(BlueprintCallable, Category = "ACF|CombinedAnimations")
    void SetCanBeHitDuringCombinedAnims(bool val) { bCanBeHitDuringCombinedAnims = val; }

protected:
    /** If true, the actor can be hit while in a contextual animation */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    bool bCanBeHitDuringCombinedAnims = false;

    /** If true, ability triggers will be locked while in a contextual animation */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
    bool bLockAbilityTriggersDuringCombinedAnims = true;

    /**
     * Called when the actor successfully joins a contextual animation scene.
     * Override to apply logic such as movement lock, FX, etc.
     */
    UFUNCTION(BlueprintNativeEvent, Category = "ACF")
    void OnJoinedScene();

    /**
     * Called when the actor leaves a contextual animation scene.
     * Override to restore previous behavior after scene ends.
     */
    UFUNCTION(BlueprintNativeEvent, Category = "ACF")
    void OnLeftScene();

    // Called when the game starts
    virtual void BeginPlay() override;

    // Cleans up bindings to the contextual anim component (important for World Partition streaming)
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    TObjectPtr<UContextualAnimSceneActorComponent> combinedAnimationComponent = nullptr;

private:
    UFUNCTION()
    void HandleJoinedScene(UContextualAnimSceneActorComponent* SceneActorComponent);

    UFUNCTION()
    void HandleLeftScene(UContextualAnimSceneActorComponent* SceneActorComponent);

    bool bIsPlayingAContextualAnim;
};
