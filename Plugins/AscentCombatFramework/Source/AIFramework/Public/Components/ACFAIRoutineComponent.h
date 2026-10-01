// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2025.
// All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Data/ACFAIRoutineDataAsset.h"
#include "ACFAIRoutineComponent.generated.h"

class UACFTask;
class UContextualAnimSceneAsset;

/**
 * Component that drives a daily AI routine based on a DataAsset.
 *
 * Responsibilities:
 * - Precomputes the schedule as minutes-since-midnight for each entry in the DataAsset.
 * - Tracks the current routine slot by GUID and handles transitions between slots.
 * - Spawns/starts task instances (UACFTask) when a new slot becomes active and stops previous tasks.
 *
 * Notes:
 * - The DataAsset entries are referenced by FGuid (EntryGuid) instead of array indices.
 * - If bSortTasksOnBuild is true, entries are sorted by time during BuildSchedule().
 */

 /** Broadcast when *a runtime task* owned by this component start. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRoutineTaskStart, UACFTask*, StartedTask);

/** Broadcast when *a runtime task* owned by this component ends. */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnRoutineTaskEnded, UACFTask*, EndedTask);

UCLASS(ClassGroup = (Custom), meta = (BlueprintSpawnableComponent))
class AIFRAMEWORK_API UACFAIRoutineComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UACFAIRoutineComponent();

	static FORCEINLINE int32 MinutesFromFRoutineTime(const FRoutineTime& fixedTime)
	{
		// Hour [0..23], Minute [0..59]
		const int32 minutes = static_cast<int32>(fixedTime.Hour) * 60 + static_cast<int32>(fixedTime.Minute);
		return FMath::Clamp(minutes, 0, 1439);
	}

	/** Called by tasks to notify this component that they have finished. */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Routine")
	FOnRoutineTaskEnded OnRoutineTaskEnded;

	/** Called by tasks to notify this component that they have started. */
	UPROPERTY(BlueprintAssignable, Category = "ACF|Routine")
	FOnRoutineTaskStart OnRoutineTaskStart;



	/** If true, sort DailyTasks ascending by time during BuildSchedule(). */
	UPROPERTY(EditAnywhere, Category = "ACF|Routine")
	bool bSortTasksOnBuild = true;

	/**
	 * Read the current apparent time-of-day from the DaySequence subsystem.
	 * @return Time in hours in the range [0..24], or 0 if unavailable.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	float GetTimeHours();

	/**
	 * Update the routine according to the current time (internally calls GetTimeHours()).
	 * Starts the new slot (if any) and stops the previous one.
	 * @return true if a new routine slot started in this call, false otherwise.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	bool UpdateByTime();

	/**
	 * Stop all currently active tasks (calls OnTaskEnded on each) and clears internal state.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	void StopAll();

	/**
	 * Convenience: start a routine slot by GUID (resolves to index and starts that entry).
	 * @param EntryGuid The GUID of the slot to start.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	void StartByGuid(const FGuid& EntryGuid);

	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	int32 FindEntryIndexByGuid(const FGuid& EntryGuid) const;

	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	FGuid AddTask(const FAIRoutineTask& Task);

	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	bool RemoveTask(const FGuid& TaskGuid);

	UFUNCTION(BlueprintPure, Category = "ACF|Routine")
	UACFTask* GetLastStartedTask() const { return LastStartedTask.Get(); }

	UFUNCTION(BlueprintPure, Category = "ACF|Routine")
	UACFAIRoutineDataAsset* GetRoutineDataAsset() const { return RoutineDataAsset; }

	UFUNCTION(BlueprintCallable, Category = "ACF|Routine")
	void SetRoutineDataAsset(UACFAIRoutineDataAsset* val) ;
protected:
	virtual void BeginPlay() override;

	/** Data asset defining routine time slots and their task templates. */
	UPROPERTY(EditAnywhere, Category = "ACF|Routine")
	UACFAIRoutineDataAsset* RoutineDataAsset = nullptr;

	UPROPERTY(Transient)
	TObjectPtr<UACFTask> LastStartedTask = nullptr;

	UPROPERTY(Transient)
	bool bStopInProgress = false;

	/** Active routine index, -1 if none. */
	UPROPERTY(Transient)
	FGuid CurrentEntryGuid;

	UPROPERTY(Transient)
	FGuid PendingNextGuid;

	// Tracks what we started today (by GUID)
	UPROPERTY(Transient)
	FGuid CurrentActiveGuid;

	// Cache the minute for the current active task (useful for debug/ties)
	UPROPERTY(Transient)
	int32 CurrentActiveMinute = -1;

	/** Runtime instances of the current routine's tasks. */
	UPROPERTY(Transient)
	TArray<TObjectPtr<UACFTask>> ActiveTasks;

	UPROPERTY()
	TArray<FAIRoutineTask> SortedDailyTasks;

private:
	/**
	 * Build the Minutes array from the DataAsset and normalize internal state.
	 * Applies sorting if bSortTasksOnBuild is true.
	 */
	void BuildSchedule();

	/**
	 * Helper: convert hours [0..24] to minutes [0..1439].
	 * @param Hours Time in hours.
	 * @return Minutes since midnight.
	 */
	int32 ToMinutes(float Hours);
	void RebuildTaskCache();
};
