// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Tasks/ACFInteractSmartObjectsTask.h"

#include "AIController.h"
#include "SmartObjectBlueprintFunctionLibrary.h"
#include "AI/AITask_UseGameplayBehaviorSmartObject.h"
#include "SmartObjectRequestTypes.h"
#include "SmartObjectSubsystem.h"
#include "Components/ACFAIRoutineComponent.h"
#include <Engine/World.h>
#include <GameFramework/Controller.h>


void UACFInteractSmartObjectsTask::OnTaskStarted_Implementation(const APawn* ControlledPawn)
{
	Super::OnTaskStarted_Implementation(ControlledPawn);
	
	FindSmartObject(ControlledPawn);
}

void UACFInteractSmartObjectsTask::OnTaskEnded_Implementation()
{
	Super::OnTaskEnded_Implementation();
	// If AI task is still running, cancel it: this will trigger OnSOAITaskFinished
	if (ActiveSOAITask)
	{
		ActiveSOAITask->ExternalCancel();
		ActiveSOAITask = nullptr;
		return; // Release will happen in OnSOAITaskFinished
	}

	// Fallback: release claim here only if still valid
	if (TaskClaimHandle.IsValid() && Controller && Controller->GetWorld())
	{
		if (USmartObjectSubsystem* Subsys = Controller->GetWorld()->GetSubsystem<USmartObjectSubsystem>())
		{
			Subsys->MarkSlotAsFree(TaskClaimHandle);
		}
		TaskClaimHandle.Invalidate();
	}
}

/**
 * Search for a suitable Smart Object around the pawn using the configured filters,
 * then claim one and trigger the interaction.
 *
 * @param ControlledPawn Pawn performing the search/interaction. Must be valid and have a World.
 */
void UACFInteractSmartObjectsTask::FindSmartObject(const APawn* ControlledPawn)
{
	if (!ControlledPawn)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TASK] FindSmartObject: ControlledPawn is null."));
		return;
	}

	if (UWorld* World = ControlledPawn->GetWorld())
	{
		USmartObjectSubsystem* SmartObjectSubsystem = World->GetSubsystem<USmartObjectSubsystem>();
		if (!SmartObjectSubsystem)
		{
			UE_LOG(LogTemp, Warning, TEXT("[TASK] SmartObjectSubsystem not found."));
			return;
		}

		TArray<FSmartObjectRequestResult> SmartObjectResults;

		FSmartObjectRequest Request;
		FSmartObjectRequestFilter Filter;

		// Designer-configured filters
		Filter.UserTags                  = UserTags;
		Filter.ActivityRequirements      = ActivityRequirements;
		Filter.BehaviorDefinitionClasses = BehaviorDefinitionClasses;
		Filter.ClaimPriority             = ClaimPriority;
		
		Request.Filter   = Filter;
		
		// Spatial query (axis-aligned box centered on the pawn)
		Request.QueryBox = FBox(
			ControlledPawn->GetActorLocation() - QueryBoxDimension,
			ControlledPawn->GetActorLocation() + QueryBoxDimension);

		SmartObjectSubsystem->FindSmartObjects(Request, SmartObjectResults);

		if (SmartObjectResults.Num() > 0)
		{
			// Simple random pick (could be replaced by best score / nearest, etc.)
			const int32 RandomIndex = FMath::RandRange(0, SmartObjectResults.Num() - 1);

			// Use the same ClaimPriority chosen by designers (instead of hardcoding Normal)
			FSmartObjectClaimHandle ClaimHandle =
				USmartObjectBlueprintFunctionLibrary::MarkSmartObjectSlotAsClaimed(
					World, SmartObjectResults[RandomIndex].SlotHandle, ControlledPawn, ClaimPriority);

			if (USmartObjectBlueprintFunctionLibrary::IsValidSmartObjectClaimHandle(ClaimHandle))
			{
				InteractSmartObject(ControlledPawn, ClaimHandle);
				return;
			}
		}
		else
		{
			UE_LOG(LogTemp, Log, TEXT("[TASK] No Smart Objects found in query box."));
		}
	}
	else
	{
		UE_LOG(LogTemp, Warning, TEXT("[TASK] FindSmartObject: World is null."));
	}
}

/**
 * Start the Gameplay Behavior task that moves to and uses the claimed Smart Object.
 *
 * @param ControlledPawn The pawn that will interact with the claimed Smart Object.
 * @param ClaimHandle    A valid claim handle obtained from the subsystem.
 */
void UACFInteractSmartObjectsTask::InteractSmartObject(
	const APawn* ControlledPawn,
	FSmartObjectClaimHandle& ClaimHandle)
{
	AAIController* AiController = Cast<AAIController>(ControlledPawn->GetController());
	if (!AiController)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TASK] InteractSmartObject: AIController not found."));
		return;
	}

	// Create and start the built-in AI task to move to and use the Smart Object
	ActiveSOAITask =
		UAITask_UseGameplayBehaviorSmartObject::MoveToAndUseSmartObjectWithGameplayBehavior(
			AiController, ClaimHandle, /*bLockAILogic=*/false, ClaimPriority);

	if (!ActiveSOAITask)
	{
		UE_LOG(LogTemp, Warning, TEXT("[TASK] Failed to create UAITask_UseGameplayBehaviorSmartObject."));
		return;
	}
	TaskClaimHandle = ClaimHandle;
	ActiveSOAITask->ReadyForActivation();
}

void UACFInteractSmartObjectsTask::OnSOAITaskFinished()
{
	// Release the claim once, safely
	if (TaskClaimHandle.IsValid() && Controller && Controller->GetWorld())
	{
		if (USmartObjectSubsystem* Subsys = Controller->GetWorld()->GetSubsystem<USmartObjectSubsystem>())
		{
			Subsys->MarkSlotAsFree(TaskClaimHandle);
		}
		TaskClaimHandle.Invalidate();
	}
	
	ActiveSOAITask = nullptr;
}


