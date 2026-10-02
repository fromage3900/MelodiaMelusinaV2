// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Game/ACFPlayerController.h"
#include "ATSTargetingComponent.h"
#include "Actors/ACFCharacter.h"
#include "CCMPlayerCameraManager.h"
#include "Components/ACFInteractionComponent.h"
#include "GameFramework/PlayerController.h"
#include "Interfaces/ACFEntityInterface.h"
#include <Components/ActorComponent.h>
#include <Net/UnrealNetwork.h>
#include <TimerManager.h>
#include "Components/ACFTeamComponent.h"
#include "ACFTeamManagerSubsystem.h"
#include <Engine/World.h>

AACFPlayerController::AACFPlayerController()
{
	// APlayerController's constructor does NOT set bCanEverTick = true,
	// so without this our Tick() (and the BP Event Tick of derived blueprints)
	// would never run, regardless of the Blueprint "Start with Tick Enabled" flag.
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = true;
}

void AACFPlayerController::BeginPlay()
{
	Super::BeginPlay();
	secondsFromLastCameraInput = 0.f;
}

void AACFPlayerController::Tick(float DeltaSeconds)
{
	if (FMath::IsNearlyZero(RotationInput.Yaw)) {
		const FTimespan timeDiff = FDateTime::Now() - lastInput;
		secondsFromLastCameraInput = timeDiff.GetTotalSeconds();
	}
	else {
		lastInput = FDateTime::Now();
		secondsFromLastCameraInput = 0.f;
	}
	Super::Tick(DeltaSeconds);
}

float AACFPlayerController::GetXSensitivity_Implementation() const
{
	return 1.f;
}

float AACFPlayerController::GetYSensitivity_Implementation() const
{
	return 1.f;
}

FGameplayTag AACFPlayerController::GetEntityCombatTeam_Implementation() const
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

void AACFPlayerController::SetGenericTeamId(const FGenericTeamId& InTeamID)
{
	if (GetPawn()) {
		if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
			TeamAgent->SetGenericTeamId(InTeamID);
		}
	}
}

void AACFPlayerController::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
	if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
		const FGenericTeamId TeamTag = TeamSubsystem->FromTagToTeamId(inCombatTeam);
		SetGenericTeamId(TeamTag);
	}
}

FGenericTeamId AACFPlayerController::GetGenericTeamId() const
{
	if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
		return TeamAgent->GetGenericTeamId();
	}

	return FGenericTeamId::NoTeam;
}

ETeamAttitude::Type AACFPlayerController::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
	if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
		return TeamAgent->GetTeamAttitudeTowards(OtherTeam);
	}

	return ETeamAttitude::Neutral;
}



void AACFPlayerController::HandleNewEntityPossessed()
{
	PossessedEntity = Cast<IACFEntityInterface>(GetPawn());
	PossessedCharacter = Cast<AACFCharacter>(GetPawn());
	OnPossessedCharacterChanged.Broadcast(PossessedCharacter);
}

void AACFPlayerController::OnRep_Pawn()
{
	Super::OnRep_Pawn();
	HandleNewEntityPossessed();
}

void AACFPlayerController::OnPossess(APawn* aPawn)
{
	Super::OnPossess(aPawn);
	HandleNewEntityPossessed();
	if (aPawn) {
		const TObjectPtr<UACFDamageHandlerComponent> damageComp = aPawn->FindComponentByClass<UACFDamageHandlerComponent>();
		if (damageComp) {
			damageComp->OnOwnerDeath.AddDynamic(this, &AACFPlayerController::OnPossessedPawnDeath);
		}
	}
}



void AACFPlayerController::OnUnPossess()
{
	if (GetPawn()) {
		const TObjectPtr<UACFDamageHandlerComponent> damageComp = GetPawn()->FindComponentByClass<UACFDamageHandlerComponent>();
		if (damageComp) {
			damageComp->OnOwnerDeath.RemoveDynamic(this, &AACFPlayerController::OnPossessedPawnDeath);
		}
	}
	Super::OnUnPossess();
}

void AACFPlayerController::OnPossessedPawnDeath_Implementation()
{
}
