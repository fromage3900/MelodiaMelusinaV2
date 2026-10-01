// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ACFTask.h"
#include "ACFRandomPatrolAroundPointTask.generated.h"

class AActor;

/**
 * Routine task that switches the AI to random patrol around a point.
 */
UCLASS(BlueprintType, Blueprintable, EditInlineNew)
class AIFRAMEWORK_API UACFRandomPatrolAroundPointTask : public UACFTask
{
	GENERATED_BODY()

public:
	/** If true, uses pawn location as patrol center when the task starts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol")
	bool bUsePawnLocationAsCenter = true;

	/** Actor used as patrol center when bUsePawnLocationAsCenter is false. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol", meta = (EditCondition = "!bUsePawnLocationAsCenter"))
	TObjectPtr<AActor> PatrolCenterActor = nullptr;

	/** Radius used by random patrol point generation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol", meta = (ClampMin = "0.0"))
	float PatrolRadius = 1500.f;

	/** If true, writes the selected center as AI home location. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol")
	bool bSetHomeLocationToPatrolCenter = true;

	/** If true, starts patrol movement immediately by requesting a random waypoint. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Routine|Patrol")
	bool bStartMovementOnTaskStart = true;

	virtual void OnTaskStarted_Implementation(const APawn* ControlledPawn) override;
	virtual void OnTaskEnded_Implementation() override;

private:
	UPROPERTY(Transient)
	TObjectPtr<class UACFAIPatrolComponent> CachedPatrolComponent = nullptr;
};
