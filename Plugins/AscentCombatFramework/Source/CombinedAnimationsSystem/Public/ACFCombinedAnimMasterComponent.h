// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "ACFCombinedAnimComponent.h"
#include "CASTypes.h"

#include "ACFCombinedAnimMasterComponent.generated.h"

class UACFCombinedAnimationsDataAsset;

/**
 * Component used on characters that act as masters in a combined animation scenario.
 * Responsible for selecting and evaluating appropriate combined animations and executions
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent), BlueprintType, Blueprintable)
class COMBINEDANIMATIONSSYSTEM_API UACFCombinedAnimMasterComponent : public UACFCombinedAnimComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFCombinedAnimMasterComponent();

    /**
     * Checks if the given actor is eligible to play the specified combined animation with this master.
     *
     * @param combinedAnim The animation configuration to validate.
     * @param targetActor The actor to evaluate as a potential animation partner.
     * @return True if the animation can be played with the given actor.
     */
    UFUNCTION(BlueprintPure, Category = ACF)
    bool CanPlayCombinedAnimWithActor(const FCombinedAnimConfig& combinedAnim, AActor* targetActor);

    /**
     * Searches for the most suitable combined animation that can be played with the given actor.
     *
     * @param targetActor The potential animation partner.
     * @param outCombinedAnim The best matching animation config found.
     * @return True if a suitable combined animation was found.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool TryGetBestCombinedAnimForActor(AActor* targetActor, FCombinedAnimConfig& outCombinedAnim);

    /**
     * Returns all combined animation configs whose AnimTag matches the given tag.
     *
     * @param AnimTag The gameplay tag to filter by.
     * @param outCombinedAnims Output array filled with matching animation configs.
     * @return True if at least one matching animation was found.
     */
    UFUNCTION(BlueprintCallable, Category = ACF)
    bool GetContextualAnimsByTag(const FGameplayTag& AnimTag, TArray<FCombinedAnimConfig>& outCombinedAnims);

protected:
    /** Reference to the data asset containing all possible combined animations for this master */
    UPROPERTY(EditAnywhere, Category = ACF)
    UACFCombinedAnimationsDataAsset* CombinedAnimations;

    // Called when the game starts
    virtual void BeginPlay() override;
};
