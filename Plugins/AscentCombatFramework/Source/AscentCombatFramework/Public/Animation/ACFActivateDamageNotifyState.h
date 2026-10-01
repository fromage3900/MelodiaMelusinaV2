// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "CoreMinimal.h"
#include "Game/ACFTypes.h"

#include "ACFActivateDamageNotifyState.generated.h"


/**
 * AnimNotifyState used to activate specific damage types during an animation.
 * Allows configuring which damage type and which trace channels are enabled
 * for the duration of the notify state.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFActivateDamageNotifyState : public UAnimNotifyState {
    GENERATED_BODY()
public:
    /** Default constructor */
    UACFActivateDamageNotifyState();

protected:
    /** Type of damage to activate while this notify is running */
    UPROPERTY(EditAnywhere, Category = ACF)
    EDamageActivationType DamageToActivate;

    /** List of trace channels or socket names to activate for collision checks */
    UPROPERTY(EditAnywhere, Category = ACF)
    TArray<FName> TraceChannels;

    virtual void NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference) override;
    virtual void NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
};
