// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "CoreMinimal.h"

#include "ACFSlowAnimNotifyState.generated.h"

class USkeletalMeshComponent;
/**
 *
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFSlowAnimNotifyState : public UAnimNotifyState {
    GENERATED_BODY()

    void NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference) override;

    void NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float previousRate = 1.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float slowRate = 0.2f;
};
