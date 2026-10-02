// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFRiderAIController.h"
#include "ACFRiderComponent.h"
#include "ACFTeamManagerSubsystem.h"
#include "Interfaces/ACFEntityInterface.h"
#include "Kismet/KismetMathLibrary.h"
#include <Camera/PlayerCameraManager.h>
#include <GameFramework/Controller.h>
#include <GenericTeamAgentInterface.h>
#include <Kismet/GameplayStatics.h>
#include <Engine/World.h>

AACFRiderAIController::AACFRiderAIController()
{
    OffsetRotCorrection = FRotator(0.f, 0.f, 0.f);
    ClampMin = FRotator(-90.f, -90.f, -10.f);
    ClampMax = FRotator(90.f, 90.f, 10.f);
}

void AACFRiderAIController::UpdateControlRotation(float DeltaTime, bool bUpdatePawn /*= true*/)
{
    if (bOverrideControlWithMountRotation && riderComp && riderComp->IsRiding()) {
        const APawn* mount = riderComp->GetMount();
        if (mount) {
            FRotator mountRot = mount->GetControlRotation();
            mountRot += OffsetRotCorrection;
            const FRotator deltaRot = UKismetMathLibrary::NormalizedDeltaRotator(mountRot, GetPawn()->GetActorRotation());
            if (deltaRot.Yaw <= ClampMax.Yaw && deltaRot.Yaw >= ClampMin.Yaw && deltaRot.Pitch <= ClampMax.Pitch && deltaRot.Pitch >= ClampMin.Pitch && deltaRot.Pitch <= ClampMax.Pitch && deltaRot.Pitch >= ClampMin.Pitch) {
                SetControlRotation(mountRot);
            } else {
                Super::UpdateControlRotation(DeltaTime, bUpdatePawn);
            }

        } else {
            Super::UpdateControlRotation(DeltaTime, bUpdatePawn);
        }
    } else {
        Super::UpdateControlRotation(DeltaTime, bUpdatePawn);
    }
}

void AACFRiderAIController::OnPossess(APawn* InPawn)
{
    Super::OnPossess(InPawn);
    SetRiderCompReference();
}

void AACFRiderAIController::OnUnPossess()
{
    Super::OnUnPossess();
    riderComp = nullptr;
}

void AACFRiderAIController::GetPlayerViewPoint(FVector& out_Location, FRotator& out_Rotation) const
{
    APlayerController* pc = Cast<APlayerController>(GetMountController().Get());

    if (pc) {
        pc->GetPlayerViewPoint(out_Location, out_Rotation);
    } else {
        Super::GetPlayerViewPoint(out_Location, out_Rotation);
    }
}

void AACFRiderAIController::SetRiderCompReference()
{
    const APawn* possessedPawn = GetPawn();

    ensure(possessedPawn);
    riderComp = possessedPawn->FindComponentByClass<UACFRiderComponent>();
}

TObjectPtr<AController> AACFRiderAIController::GetMountController() const
{
    if (riderComp) {
        const APawn* mount = riderComp->GetMount();
        if (mount) {
            return mount->GetController();
        }
    }
    return nullptr;
} 


FGameplayTag AACFRiderAIController::GetEntityCombatTeam_Implementation() const
{
    if (GetPawn()) {
        // Try ACF interface first
        if (GetPawn()->Implements<UACFEntityInterface>()) {
            return IACFEntityInterface::Execute_GetEntityCombatTeam(GetPawn());
        }

        // Fallback to Unreal's GenericTeamAgent
        if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
            if (UWorld* World = GetWorld()) {
                if (UACFTeamManagerSubsystem* TeamSubsystem = World->GetSubsystem<UACFTeamManagerSubsystem>()) {
                    return TeamSubsystem->FromTeamIdToTag(TeamAgent->GetGenericTeamId());
                }
            }
        }
    }

    return FGameplayTag();
}

void AACFRiderAIController::SetGenericTeamId(const FGenericTeamId& InTeamID)
{
    Super::SetGenericTeamId(InTeamID);

    if (GetPawn()) {
        if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
            TeamAgent->SetGenericTeamId(InTeamID);
        }
    }
}

void AACFRiderAIController::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
    if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
        const FGenericTeamId TeamTag = TeamSubsystem->FromTagToTeamId(inCombatTeam);
        SetGenericTeamId(TeamTag);
    }
}

FGenericTeamId AACFRiderAIController::GetGenericTeamId() const
{
    if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
        return TeamAgent->GetGenericTeamId();
    }

    return FGenericTeamId::NoTeam;
}

ETeamAttitude::Type AACFRiderAIController::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
    if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
        return TeamAgent->GetTeamAttitudeTowards(OtherTeam);
    }

    return ETeamAttitude::Neutral;
}