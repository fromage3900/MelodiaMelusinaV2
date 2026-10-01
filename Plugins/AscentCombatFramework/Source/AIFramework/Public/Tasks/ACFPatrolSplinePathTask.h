// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFTask.h"
#include "ACFPatrolSplinePathTask.generated.h"

class AACFSplinePath;

/**
 * Routine task that configures the AI to patrol on a spline path.
 */
UCLASS(BlueprintType, Blueprintable, EditInlineNew)
class AIFRAMEWORK_API UACFPatrolSplinePathTask : public UACFTask
{
	GENERATED_BODY()

public:
	/** Path used by the patrol system. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol")
	TObjectPtr<AACFSplinePath> SplinePath = nullptr;

	/** If true, forces patrol type to FollowSpline when applying the path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol")
	bool bForceFollowSpline = true;

	/** If true, starts patrol movement immediately by requesting the next waypoint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol")
	bool bStartMovementOnTaskStart = true;

	virtual void OnTaskStarted_Implementation(const APawn* ControlledPawn) override;
	virtual void OnTaskEnded_Implementation() override;

private:
	UPROPERTY(Transient)
	TObjectPtr<class UACFAIPatrolComponent> CachedPatrolComponent = nullptr;
};
