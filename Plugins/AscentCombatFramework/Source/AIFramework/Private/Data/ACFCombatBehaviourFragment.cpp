// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Data/ACFCombatBehaviourFragment.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFCombatBehaviourComponent.h"
#include "AIController.h"
#include "GameFramework/Pawn.h"

void UACFCombatBehaviourFragment::ApplyFragment_Implementation(APawn* pawnOwner)
{
	if (!CombatBehaviour || !pawnOwner) return;

	AACFCharacter* ACFChar = Cast<AACFCharacter>(pawnOwner);
	if (!ACFChar) return;

	AAIController* AICont = Cast<AAIController>(ACFChar->GetController());
	if (!AICont) return;

	UACFCombatBehaviourComponent* CombatComp = AICont->FindComponentByClass<UACFCombatBehaviourComponent>();
	if (CombatComp)
	{
		CombatComp->SetCombatBehaviour(CombatBehaviour);
	}
}
