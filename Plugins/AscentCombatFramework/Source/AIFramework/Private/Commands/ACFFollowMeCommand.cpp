// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Commands/ACFFollowMeCommand.h"

#include "AIController.h"
#include "Components/ACFSplineFollowerComponent.h"
#include "Components/SplineComponent.h"
#include "ACFAIController.h"
#include "Logging.h"


UACFFollowMeCommand::UACFFollowMeCommand()
{
    SplinePath = nullptr;
    TargetPawn = nullptr;
    SplineFollowerComponent = nullptr;
}

void UACFFollowMeCommand::SetupCommand(USplineComponent* InSpline, APawn* InTargetPawn)
{
    SplinePath = InSpline;
    TargetPawn = InTargetPawn;
}

void UACFFollowMeCommand::ExecuteCommand_Implementation(AACFAIController* AIController)
{
    Super::ExecuteCommand_Implementation(AIController);

    /** Validate inputs */
    if (!SplinePath || !TargetPawn) {
        UE_LOG(ACFAILog, Error, TEXT("FollowMeCommand: Spline or TargetPawn not set! Call SetupCommand first"));
        FinishExecution(false);
        return;
    }


    if (!AIController) {
        UE_LOG(ACFAILog, Error, TEXT("FollowMeCommand: Owner is not an AIController"));
         FinishExecution(false);
        return;
    }

    /** Find  SplineFollowerComponent */
    SplineFollowerComponent = AIController->FindComponentByClass<UACFSplineFollowerComponent>();
    if (!SplineFollowerComponent) {
        /** Create component if it doesn't exist */
        UE_LOG(ACFAILog, Error, TEXT("FollowMeCommand: SplineFollowerComponent is not an AIController"));
         FinishExecution(false);
        return;
    }

    /** Bind to completion events */
    SplineFollowerComponent->OnSplineCompleted.AddDynamic(this, &UACFFollowMeCommand::HandleSplineCompleted);
    SplineFollowerComponent->OnFollowingStopped.AddDynamic(this, &UACFFollowMeCommand::HandleFollowingStopped);

    /** Start following */
    SplineFollowerComponent->StartFollowing(SplinePath, TargetPawn);
}

void UACFFollowMeCommand::EndCommand_Implementation(class AACFAIController* controller)
{
    Super::EndCommand_Implementation(controller);

      /** Unbind delegates before cleanup */
    if (SplineFollowerComponent)
    {
        SplineFollowerComponent->OnSplineCompleted.RemoveDynamic(this, &UACFFollowMeCommand::HandleSplineCompleted);
        SplineFollowerComponent->OnFollowingStopped.RemoveDynamic(this, &UACFFollowMeCommand::HandleFollowingStopped);
        
        /** Stop following if still active */
        if (SplineFollowerComponent->IsFollowing())
        {
            SplineFollowerComponent->StopFollowing();
        }
    }


    /** Clear references */
    SplinePath = nullptr;
    TargetPawn = nullptr;
    SplineFollowerComponent = nullptr;
}

void UACFFollowMeCommand::HandleSplineCompleted()
{
    UE_LOG(ACFAILog, Log, TEXT("FollowMeCommand: Spline completed successfully"));
    
    /** Command completed successfully */
    FinishExecution(true);
}

void UACFFollowMeCommand::HandleFollowingStopped()
{
    /** Only end if we haven't already */
    if (SplineFollowerComponent && !SplineFollowerComponent->IsFollowing())
    {
        UE_LOG(ACFAILog, Log, TEXT("FollowMeCommand: Following stopped"));
    }
}