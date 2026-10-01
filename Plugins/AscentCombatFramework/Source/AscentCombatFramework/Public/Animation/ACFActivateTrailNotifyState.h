// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "CoreMinimal.h"
#include "Game/ACFTypes.h"

#include "ACFActivateTrailNotifyState.generated.h"

/**
 * AnimNotifyState that activates ONLY trail FX (no collision trace) on the character's
 * collision manager or on its equipped weapons, based on TrailTarget.
 * Use this when you want visual trails without enabling damage detection.
 */
UCLASS()
class ASCENTCOMBATFRAMEWORK_API UACFActivateTrailNotifyState : public UAnimNotifyState
{
	GENERATED_BODY()

public:
	/** Where to play trails: character's collision component or main/offhand/both weapons. */
	UPROPERTY(EditAnywhere, Category = ACF)
	EDamageActivationType TrailTarget = EDamageActivationType::ERight;

	/** Trace/trail names to play (must match names in the collision manager's DamageTraces). Empty = all trails. */
	UPROPERTY(EditAnywhere, Category = ACF)
	TArray<FName> TrailNames;

	virtual void NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference) override;
	virtual void NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
};
