// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Actions/ACFHitAction.h"
#include "ACFActionsFunctionLibrary.h"
#include "Actions/ACFActionAbility.h"
#include "Actors/ACFCharacter.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/ACFQuadrupedMovementComponent.h"
#include "Game/ACFFunctionLibrary.h"

UACFHitAction::UACFHitAction()
{
	HitDirectionToMontageSectionMap.Add(EACFDirection::Front, FName("Front"));
	HitDirectionToMontageSectionMap.Add(EACFDirection::Back, FName("Back"));
	HitDirectionToMontageSectionMap.Add(EACFDirection::Right, FName("Right"));
	HitDirectionToMontageSectionMap.Add(EACFDirection::Left, FName("Left"));
	ActionConfig.bStopBehavioralThree = true;
	NetExecutionPolicy = EGameplayAbilityNetExecutionPolicy::LocalPredicted;

}

void UACFHitAction::OnActionStarted_Implementation()
{
	Super::OnActionStarted_Implementation();

	AACFCharacter* acfCharacter = Cast<AACFCharacter>(GetCharacterOwner());

	if (acfCharacter) {
		damageReceived = acfCharacter->GetLastDamageInfo();
		UACFAbilitySystemComponent* actionsMan = acfCharacter->GetActionsComponent();
		if (actionsMan) {
			// clears the input buffer
			actionsMan->StoreAbilityInBuffer(FGameplayTag());
		}
	}
}

void UACFHitAction::OnActionEnded_Implementation()
{
	Super::OnActionEnded_Implementation();
}

FName UACFHitAction::GetMontageSectionName_Implementation()
{

	const EACFDirection dir = damageReceived.DamageDirection;

	const FName* section = HitDirectionToMontageSectionMap.Find(dir);

	if (section) {
		return *section;
	}

	return Super::GetMontageSectionName_Implementation();
}
