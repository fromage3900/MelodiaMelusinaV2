// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFBaseAIController.h"
#include "ACFTeamManagerSubsystem.h"
#include "Components/ACFTeamComponent.h"
#include "GameplayTagContainer.h"
#include "Interfaces/ACFEntityInterface.h"
#include <Engine/World.h>
#include "ACFAIManagerSubsystem.h"

void AACFBaseAIController::OnPossess(APawn* possPawn)
{
	Super::OnPossess(possPawn);
	PossessedEntity = Cast<IACFEntityInterface>(GetPawn());

	if (UACFAIManagerSubsystem* AISubsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		AISubsystem->RegisterAI(this);
	}
}

void AACFBaseAIController::OnUnPossess()
{
	Super::OnUnPossess();
	if (UACFAIManagerSubsystem* AISubsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		AISubsystem->UnregisterAI(this);
	}

}

AACFBaseAIController::AACFBaseAIController(const FObjectInitializer& ObjectInitializer)
{
}

FGameplayTag AACFBaseAIController::GetEntityCombatTeam_Implementation() const
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

void AACFBaseAIController::SetGenericTeamId(const FGenericTeamId& InTeamID)
{
	Super::SetGenericTeamId(InTeamID);

	if (GetPawn()) {
		if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
			TeamAgent->SetGenericTeamId(InTeamID);
		}
	}
}

void AACFBaseAIController::AssignTeamToEntity_Implementation(FGameplayTag inCombatTeam)
{
	if (UACFTeamManagerSubsystem* TeamSubsystem = GetWorld()->GetSubsystem<UACFTeamManagerSubsystem>()) {
		const FGenericTeamId TeamTag = TeamSubsystem->FromTagToTeamId(inCombatTeam);
		SetGenericTeamId(TeamTag);
	}
}

FGenericTeamId AACFBaseAIController::GetGenericTeamId() const
{
	if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
		return TeamAgent->GetGenericTeamId();
	}

	return FGenericTeamId::NoTeam;
}

ETeamAttitude::Type AACFBaseAIController::GetTeamAttitudeTowards(const AActor& OtherTeam) const
{
	if (IGenericTeamAgentInterface* TeamAgent = Cast<IGenericTeamAgentInterface>(GetPawn())) {
		return TeamAgent->GetTeamAttitudeTowards(OtherTeam);
	}

	return ETeamAttitude::Neutral;
}