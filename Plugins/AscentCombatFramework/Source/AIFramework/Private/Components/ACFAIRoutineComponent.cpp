// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFAIRoutineComponent.h"
#include "ACFAIController.h"
#include "DaySequenceActor.h"
#include "GameFramework/Controller.h"
#include "DaySequenceSubsystem.h"
#include <Engine/World.h>

DEFINE_LOG_CATEGORY_STATIC(LogACFRoutine, Log, All);

UACFAIRoutineComponent::UACFAIRoutineComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	CurrentEntryGuid.Invalidate();
	PendingNextGuid.Invalidate();
}

void UACFAIRoutineComponent::BeginPlay()
{
	Super::BeginPlay();

	// Validate asset early to avoid crashes later.
	if (!GetRoutineDataAsset())
	{
		//UE_LOG(LogTemp, Error, TEXT("[Routine] Missing RoutineDataAsset on %s"), *GetNameSafe(GetOwner()));
		return;
	}

	BuildSchedule();
}

void UACFAIRoutineComponent::BuildSchedule()
{
	if (!GetRoutineDataAsset())
	{
		UE_LOG(LogACFRoutine, Warning, TEXT("[Routine] RoutineDataAsset is null on %s"), *GetNameSafe(GetOwner()));
		return;
	}

	RebuildTaskCache();
}

int32 UACFAIRoutineComponent::ToMinutes(float Hours)
{
	const int32 M = FMath::Clamp(FMath::RoundToInt(Hours * 60.f), 0, 1439);
	return M;
}

void UACFAIRoutineComponent::RebuildTaskCache()
{
	SortedDailyTasks.Reset();
	
	if (!GetRoutineDataAsset() || GetRoutineDataAsset()->DailyTasks.Num() == 0)
	{
		return;
	}
	
	// Copy and sort tasks by time (ascending)
	SortedDailyTasks = GetRoutineDataAsset()->DailyTasks;
	SortedDailyTasks.Sort([this](const FAIRoutineTask& A, const FAIRoutineTask& B)
	{
		return MinutesFromFRoutineTime(A.TaskTime) < MinutesFromFRoutineTime(B.TaskTime);
	});
	
}


bool UACFAIRoutineComponent::UpdateByTime()
{
	if (AController* const OwnerController = Cast<AController>(GetOwner())) {
		if (AACFAIController* const ACF = Cast<AACFAIController>(OwnerController)) {
			if (ACF->IsExecutingCommand()) {
				return false;
			}
		}
	}

	const float CurrentHours = GetTimeHours();
	if (SortedDailyTasks.Num() == 0)
	{
		return false;
	}
	
	const int32 NowMinutes = ToMinutes(CurrentHours);
	
	// Find the latest eligible task using reverse iteration on sorted array
	int32 BestIndex = INDEX_NONE;
	
	for (int32 i = SortedDailyTasks.Num() - 1; i >= 0; --i)
	{
		const int32 TaskMinute = MinutesFromFRoutineTime(SortedDailyTasks[i].TaskTime);
		if (TaskMinute <= NowMinutes)
		{
			BestIndex = i;
			break; // Found! It's the most recent eligible (array is sorted)
		}
	}
	
	// If no eligible task found (before first task), wrap to last task (cyclic behavior)
	if (BestIndex == INDEX_NONE)
	{
		BestIndex = SortedDailyTasks.Num() - 1; // Last task in sorted array
	}
	
	const FGuid& BestEligibleGuid = SortedDailyTasks[BestIndex].EntryGuid;
	
	// If we already started this GUID, do nothing (no retrigger)
	if (CurrentActiveGuid.IsValid() && CurrentActiveGuid == BestEligibleGuid)
	{
		return false;
	}
	
	// Transition to new task
	CurrentActiveGuid = BestEligibleGuid;
	
	StopAll();
	StartByGuid(BestEligibleGuid);
	
	return true;
}


void UACFAIRoutineComponent::StartByGuid(const FGuid& EntryGuid)
{
	const int32 EntryIndex = FindEntryIndexByGuid(EntryGuid);
	if (EntryIndex == INDEX_NONE)
	{
		UE_LOG(LogACFRoutine, Warning, TEXT("[Routine] StartByGuid: GUID not found: %s"),
		       *EntryGuid.ToString(EGuidFormats::DigitsWithHyphens));
		return;
	}

	AController* OwnerController = Cast<AController>(GetOwner());
	APawn* ControlledPawn = OwnerController ? OwnerController->GetPawn() : nullptr;
	if (!ControlledPawn)
	{
		UE_LOG(LogACFRoutine, Warning, TEXT("[Routine] StartByGuid: Pawn is null"));
		return;
	}

	for (FAIRoutineTask& Task : GetRoutineDataAsset()->DailyTasks)
	{
		if (Task.EntryGuid == EntryGuid)
		{
			if (!Task.RoutineTask) return;
			Task.RoutineTask->Internal_OnTaskStarted(ControlledPawn);
			OnRoutineTaskStart.Broadcast(Task.RoutineTask);
			ActiveTasks.Add(Task.RoutineTask);
			LastStartedTask = Task.RoutineTask;

			CurrentEntryGuid = EntryGuid;
		}
	}
}


int32 UACFAIRoutineComponent::FindEntryIndexByGuid(const FGuid& EntryGuid) const
{
	if (!GetRoutineDataAsset()) return INDEX_NONE;
	const TArray<FAIRoutineTask>& Entries = GetRoutineDataAsset()->DailyTasks;
	for (int32 EntryIndex = 0; EntryIndex < Entries.Num(); EntryIndex++)
	{
		if (Entries[EntryIndex].EntryGuid == EntryGuid)
			return EntryIndex;
	}
	return INDEX_NONE;
}


FGuid UACFAIRoutineComponent::AddTask(const FAIRoutineTask& Task)
{
	// Find the correct insertion position to maintain sorting
	const int32 TaskMinute = MinutesFromFRoutineTime(Task.TaskTime);
	
	int32 InsertIndex = 0;
	for (int32 i = 0; i < SortedDailyTasks.Num(); ++i)
	{
		const int32 ExistingMinute = MinutesFromFRoutineTime(SortedDailyTasks[i].TaskTime);
		if (TaskMinute < ExistingMinute)
		{
			InsertIndex = i;
			break;
		}
		InsertIndex = i + 1;
	}
	
	SortedDailyTasks.Insert(Task, InsertIndex);
	return Task.EntryGuid;
}

bool UACFAIRoutineComponent::RemoveTask(const FGuid& TaskGuid)
{
	const int32 RemovedCount = SortedDailyTasks.RemoveAll([&TaskGuid](const FAIRoutineTask& Task)
	{
		return Task.EntryGuid == TaskGuid;
	});
	
	if (RemovedCount > 0)
	{
		UE_LOG(LogACFRoutine, Log, TEXT("%s: Removed task %s"), 
		       *GetNameSafe(GetOwner()), *TaskGuid.ToString());
		
		// If we removed the currently active task, invalidate it
		if (CurrentActiveGuid == TaskGuid)
		{
			CurrentActiveGuid.Invalidate();
		}
		
		return true;
	}
	
	return false;
}


void UACFAIRoutineComponent::SetRoutineDataAsset(UACFAIRoutineDataAsset* val)
{
	RoutineDataAsset = val;
	BuildSchedule();
}

void UACFAIRoutineComponent::StopAll()
{
	bStopInProgress = true;

	int32 sentEndCalls = 0;

	for (UACFTask* task : ActiveTasks)
	{
		if (task)
		{
			task->OnTaskEnded();
			OnRoutineTaskEnded.Broadcast(task);
			++sentEndCalls;
		}
	}
	ActiveTasks.Reset();
}


float UACFAIRoutineComponent::GetTimeHours()
{
	AController* Controller = Cast<AController>(GetOwner());
	if (!Controller)
	{
		UE_LOG(LogACFRoutine, Warning, TEXT("[Routine] GetTimeHours: Owner is not a Controller (%s)"),
		       *GetNameSafe(GetOwner()));
		return 0.f;
	}

	UWorld* World = Controller->GetWorld();
	if (!World)
	{
		UE_LOG(LogACFRoutine, Warning, TEXT("[Routine] GetTimeHours: World is null"));
		return 0.f;
	}

	if (UDaySequenceSubsystem* DaySequence = World->GetSubsystem<UDaySequenceSubsystem>())
	{
		ADaySequenceActor* DaySequencerActor = DaySequence->GetDaySequenceActor();
		if (DaySequencerActor)
		{
			const float H = DaySequencerActor->GetApparentTimeOfDay();
			return H;
		}
	}
	return 0.f;
}
