// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Commands/ACFGoThereCommand.h"
#include "ACFAIController.h"
#include <AITypes.h>
#include <CollisionQueryParams.h>
#include <Kismet/KismetSystemLibrary.h>
#include <Engine/World.h>

void UACFGoThereCommand::ExecuteCommand_Implementation(class AACFAIController* controller)
{
    FVector EyesLocation;
    FRotator EyesRotation;

    AActor* CharacterOwner = GetAIController()->GetLeadActorBK();

    if (CharacterOwner) {
        CharacterOwner->GetActorEyesViewPoint(EyesLocation, EyesRotation);

        FVector ShotDirection = EyesRotation.Vector();
        FVector TraceEnd = EyesLocation + (ShotDirection * 50000);

        FHitResult Hit;
        bool const IsHit = LineTrace(EyesLocation, TraceEnd, Hit);
        if (IsHit) {
            FVector ImpactLocation = Hit.ImpactPoint;

            if (bDrawDebug) {
                UKismetSystemLibrary::DrawDebugSphere(controller, ImpactLocation, 100.f, 12.f, FLinearColor::Green, 5.f);
            }

            controller->MoveToLocation(ImpactLocation, 50.f, true, true, true, false);
            FinishExecution(true);
        }
    }
    FinishExecution(false);
}

void UACFGoThereCommand::EndCommand_Implementation(class AACFAIController* controller)
{
}

bool UACFGoThereCommand::LineTrace(const FVector& start, const FVector& end, FHitResult& outResults)
{
    AActor* CharacterOwner = GetAIController()->GetLeadActorBK();
    FCollisionQueryParams QueryParams;
    QueryParams.AddIgnoredActor(CharacterOwner);

    FCollisionObjectQueryParams objQueryParams;
    objQueryParams.AddObjectTypesToQuery(ECC_WorldStatic);
    return GetWorld()->LineTraceSingleByObjectType(outResults, start, end, objQueryParams, QueryParams);
}
