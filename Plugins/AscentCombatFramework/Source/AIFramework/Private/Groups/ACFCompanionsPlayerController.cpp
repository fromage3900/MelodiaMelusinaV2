// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#include "Groups/ACFCompanionsPlayerController.h"
#include "Components/ACFCompanionGroupAIComponent.h"
#include "Actors/ACFCharacter.h"
#include <Net/UnrealNetwork.h>
#include "Interfaces/ACFEntityInterface.h"
#include "GameFramework/PlayerController.h"


AACFCompanionsPlayerController::AACFCompanionsPlayerController()
{
	CompanionsComponent = CreateDefaultSubobject<UACFCompanionGroupAIComponent>("CompanionsComp");
}

void AACFCompanionsPlayerController::BeginPlay()
{
	Super::BeginPlay();
}


void AACFCompanionsPlayerController::SwitchToNearestCompanion(float blendTime /*= 0.5f */)
{
	if (!CompanionsComponent || !PossessedCharacter)
		return;

	class AACFCharacter* companion = CompanionsComponent->GetAgentNearestTo(PossessedCharacter->GetActorLocation());

	if (!companion) {
		return;
	}

	SwitchPossessionToCharacer(companion, blendTime);
}



void AACFCompanionsPlayerController::SwitchPossessionToCharacer_Implementation(class AACFCharacter* inCharacter, float blendTime /*= 0.5f */)
{
	if (!CompanionsComponent || !PossessedEntity) {
		return;
	}

	AACFCharacter* oldPossessedChar = Cast< AACFCharacter>(PossessedEntity);
	if (oldPossessedChar) {
		Internal_SwitchPossessionTo(inCharacter);
		SetViewTargetWithBlend(oldPossessedChar, blendTime);
	}
}

bool AACFCompanionsPlayerController::SwitchPossessionToCharacer_Validate(class AACFCharacter* inCharacter, float blendTime /*= 0.5f */)
{
	return true;
}



UACFGroupAIComponent* AACFCompanionsPlayerController::GetOwningGroup_Implementation()
{
	return CompanionsComponent;
}

bool AACFCompanionsPlayerController::IsPartOfGroup_Implementation()
{
	return (CompanionsComponent != nullptr && CompanionsComponent->GetGroupSize() != 0);
}

void AACFCompanionsPlayerController::Internal_SwitchPossessionTo(AACFCharacter* inCharacter)
{
	CompanionsComponent->RemoveAgentFromGroup(inCharacter);
	inCharacter->GetController()->Destroy(true);
	AACFCharacter* oldPossessedChar = Cast<AACFCharacter>(GetPawn());

	Possess(inCharacter);
	if (oldPossessedChar) {
		oldPossessedChar->SpawnDefaultController();
		CompanionsComponent->AddExistingCharacterToGroup(oldPossessedChar);
	}
}

