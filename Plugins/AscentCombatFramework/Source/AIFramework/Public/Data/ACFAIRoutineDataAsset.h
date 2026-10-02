// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2025.
// All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ACFAITypes.h"
#include "ACFAIRoutineDataAsset.generated.h"

/**
 * Data asset that defines a daily routine schedule for an AI.
 *
 * Each entry in `DailyTasks` represents a time slot (HH:MM) and the set of task templates
 * (UACFTask instances) that must start at that time. At runtime the routine component
 * resolves the current slot by time-of-day and instantiates/starts the listed tasks.
 *
 * Notes:
 * - Time-of-day is interpreted in minutes since midnight (see FRoutineTime / ToMinutesSinceMidnight()).
 * - Each entry should have a unique EntryGuid (used to reference slots without relying on array index).
 * - Order is not required; the routine component can sort by time on build if enabled.
 */
UCLASS(BlueprintType)
class AIFRAMEWORK_API UACFAIRoutineDataAsset : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	/** Routine entries for a single day. Each element defines start time, tasks, and optional contextual anim. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="ACF|AI Routine")
	TArray<FAIRoutineTask> DailyTasks;
};
