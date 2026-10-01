// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#pragma once

#include "CoreMinimal.h"
#include "ACFChooserAction.h"
#include "GameplayTagContainer.h"
#include "ACFDirectionalChooserAction.generated.h"

UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFGameplayTagsWrapper : public UObject
{
    GENERATED_BODY()

public:
    UPROPERTY()
    FGameplayTagContainer Tags;
};

/**
 * A specialized action class that chooses animations based on input direction
 * Uses float ranges for more precise direction-based animation selection
 */
UCLASS(Blueprintable, BlueprintType, DefaultToInstanced, EditInlineNew)
class ASCENTCOMBATFRAMEWORK_API UACFDirectionalChooserAction : public UACFChooserAction
{
    GENERATED_BODY()

public:
    UACFDirectionalChooserAction();

    /** 
     * Get the current input direction in degrees (-180 to 180)
     * @return Direction angle where:
     * 0 = Forward
     * 90 = Right
     * -90 = Left
     * 180/-180 = Back
     */
    UFUNCTION(BlueprintCallable, BlueprintPure, Category = "ACF|Directional Action", 
              meta=(Keywords="Direction,Angle,Input"))
    float GetInputDirection() const;

    /** Tags to be used in the chooser conditions */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chooser")
    FGameplayTagContainer ChooserTags;

    /** Current input direction in degrees (-180 to 180) */
    UPROPERTY(BlueprintReadOnly, Category = "ACF|Directional Action")
    float CachedInputDirection;

protected:
    /** Override to set direction parameters */
    virtual void SetChooserParams_Implementation() override;

    /** UObject wrapper for our gameplay tags */
    UPROPERTY()
    UACFGameplayTagsWrapper* TagsWrapper;
};
