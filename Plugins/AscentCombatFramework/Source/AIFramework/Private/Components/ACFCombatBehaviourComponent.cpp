// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Components/ACFCombatBehaviourComponent.h"
#include "ACFAIController.h"
#include "ACFActionCondition.h"
#include "ACFCombatBehaviorDataAsset.h"
#include "ATSTargetingFunctionLibrary.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFAIManagerComponent.h"
#include "Components/ACFCharacterMovementComponent.h"
#include "Components/ACFEquipmentComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "Game/ACFTypes.h"
#include <GameFramework/GameStateBase.h>
#include <Kismet/GameplayStatics.h>
#include <Logging.h>
#include "ACFBaseAIController.h"
#include "Components/ACFAbilitySystemComponent.h"
#include "ACFAIManagerSubsystem.h"
#include "Engine/World.h"



UACFCombatBehaviourComponent::UACFCombatBehaviourComponent()
{
}

bool UACFCombatBehaviourComponent::TryGetBestConditionalAction(FActionChances& outAction) {

	if (!CombatBehaviour) {
		return false;
	}

	TArray<float> weights;
	TArray<FActionChances> executableActions;
	for (const FConditions& actionCond : CombatBehaviour->ActionByCondition) {
		const FActionChances action = actionCond;
		if (actionCond.ActionTag == FGameplayTag() || (VerifyCondition(actionCond) && UACFFunctionLibrary::ShouldExecuteAction(action, pawnOwner))) {
			executableActions.Add(actionCond);
			weights.Add(actionCond.Weight);
		}
	}
	const int32 index = UACFFunctionLibrary::ExtractIndexWithProbability(weights);
	if (executableActions.IsValidIndex(index)) {
		outAction = executableActions[index];
		return true;
	}
	return false;
}

void UACFCombatBehaviourComponent::InitBehavior(AACFBaseAIController* controller)
{
	if (!controller) {
		UE_LOG(ACFAILog, Error, TEXT("No controller for combat behaviour! - UACFCombatBehaviourComponent::InitBehavior"));
		return;
	}

	aiController = Cast<AACFAIController>(controller);
	pawnOwner = Cast<AACFCharacter>(controller->GetPawn());
	if (!pawnOwner) {
		UE_LOG(ACFAILog, Error, TEXT("No ACFCharacter for combat behaviour! - UACFCombatBehaviourComponent::InitBehavior"));
		return;
	}

	InternalCombatBehaviour = Cast<UACFCombatBehaviorDataAsset>(CombatBehaviour);
	moventComp = pawnOwner->GetACFCharacterMovementComponent();
	abilityComp = pawnOwner->FindComponentByClass<UACFAbilitySystemComponent>();
	if (moventComp && abilityComp) {
		moventComp->ResetStrafeMovement();
		abilityComp->TriggerAction(EngagingAction, EActionPriority::EHigh);
	}
	else {
		UE_LOG(ACFAILog, Error, TEXT("No Movement or Ability Component found for combat behaviour! - UACFCombatBehaviourComponent::InitBehavior"));
	}

	if (!InternalCombatBehaviour) {
		return ;
	}

	if (UACFAIManagerSubsystem* Subsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		Subsystem->AddAIToBattle(aiController);
	}
	if (CheckEquipment()) {
		TryEquipWeapon();
	}
}


bool UACFCombatBehaviourComponent::TryExecuteActionByCombatState(EAICombatState combatState)
{
	if (!InternalCombatBehaviour) {
		return false;
	}
	if (CheckEquipment()) {
		TryEquipWeapon();
		return false;
	}

	FActionsChances* actions = InternalCombatBehaviour->ActionByCombatState.Find(combatState);
	if (actions) {
		TArray<float> weights;
		TArray<FActionChances> executableActions;
		for (const auto& elem : actions->PossibleActions) {
			if (elem.ActionTag == FGameplayTag() || UACFFunctionLibrary::ShouldExecuteAction(elem, pawnOwner)) {
				executableActions.Add(elem);
				weights.Add(elem.Weight);
			}
		}
		const int32 index = UACFFunctionLibrary::ExtractIndexWithProbability(weights);
		if (executableActions.IsValidIndex(index)) {
			const auto& elem = executableActions[index];
			aiController->SetWaitDurationTimeBK(elem.BTWaitTime);
			if (elem.bRequiresTicket) {
				return EvaluateTicket(elem);

			}
			else {
				abilityComp->TriggerAction(elem.ActionTag, elem.Priority);
				return true;
			}
		}
	}
	return false;
}

void UACFCombatBehaviourComponent::SetCombatBehaviour(UACFBaseCombatBehaviorDataAsset* combatBehav)
{
	CombatBehaviour = combatBehav;
	InternalCombatBehaviour = Cast<UACFCombatBehaviorDataAsset>(CombatBehaviour);
}

bool UACFCombatBehaviourComponent::EvaluateTicket(const FActionChances& elem)
{
	// Verify if we have a ticket or if we can request one
	TObjectPtr<AGameStateBase> gameState = UGameplayStatics::GetGameState(this);
	if (!gameState) {
		return false;
	}

	TObjectPtr<UACFAIManagerComponent> aiManager = gameState->FindComponentByClass<UACFAIManagerComponent>();
	if (!aiManager) {
		UE_LOG(ACFAILog, Error, TEXT("No AI Manager found! - UACFCombatBehaviourComponent::EvaluateTicket"));
		return false;
	}
	if (aiManager->HasTicket(aiController) || aiManager->RequestTicket(UATSTargetingFunctionLibrary::GetTargetedActor(aiController->GetPawn()), aiController, elem.TicketDuration)) {
		abilityComp->TriggerAction(elem.ActionTag, elem.Priority);
		return true;
	}

	return false;
}


bool UACFCombatBehaviourComponent::TryExecuteConditionAction()
{
	if (CheckEquipment()) {
		TryEquipWeapon();
		return false;
	}

	FActionChances elem;
	if (TryGetBestConditionalAction(elem)) {
		if (aiController) {
			aiController->SetWaitDurationTimeBK(elem.BTWaitTime);
		}
		if (elem.bRequiresTicket) {
			return EvaluateTicket(elem);
		}
		else {
			abilityComp->TriggerAction(elem.ActionTag, elem.Priority);
			return true;
		}
	}
	return false;
}

bool UACFCombatBehaviourComponent::VerifyCondition(const FConditions& condition)
{
	return condition.Condition && condition.Condition->IsConditionMet(pawnOwner);
}

bool UACFCombatBehaviourComponent::IsTargetInMeleeRange(AActor* target)
{
	if (!InternalCombatBehaviour) {
		//UE_LOG(ACFAILog, Error, TEXT("No Combat Behavior found! - UACFCombatBehaviourComponent"));
		return false;
	}

	const FAICombatStateConfig* meleeDist = InternalCombatBehaviour->CombatStatesConfig.FindByKey(EAICombatState::EMeleeCombat);

	const ACharacter* targetChar = Cast<ACharacter>(target);
	const float meleeDistance = GetIdealDistanceByCombatState(EAICombatState::EMeleeCombat);
	if (meleeDist) {
		if (targetChar) {
			const float dist = UACFFunctionLibrary::CalculateDistanceBetweenCharactersExtents(pawnOwner, targetChar);
			return meleeDistance >= dist;
		}
		else if (target) {
			return pawnOwner->GetDistanceTo(target) <= meleeDistance;
		}
	}
	return false;
}

EAICombatState UACFCombatBehaviourComponent::GetBestCombatStateByTargetDistance(float targetDistance)
{
	if (!InternalCombatBehaviour) {
		return EAICombatState::EMeleeCombat;
	}
	for (const FAICombatStateConfig& state : InternalCombatBehaviour->CombatStatesConfig) {
		if (EvaluateCombatState(state.CombatState)) {
			return state.CombatState;
		}
	}

	return InternalCombatBehaviour->DefaultCombatState;
}

float UACFCombatBehaviourComponent::GetIdealDistanceByCombatState(EAICombatState combatState) const
{
	const FAICombatStateConfig* aiState = InternalCombatBehaviour->CombatStatesConfig.FindByKey(combatState);
	if (aiState) {
		const UACFDistanceActionCondition* distanceCond = aiState->GetDistanceBasedCondition();
		if (distanceCond) {
			return distanceCond->GetDistance();
		}
	}

	UE_LOG(ACFAILog, Warning, TEXT("Unallowed Combat State! - UACFCombatBehaviourComponent::GetIdealDistanceByCombatState"));
	return -1.f;
}



void UACFCombatBehaviourComponent::TryEquipWeapon()
{
	const UACFEquipmentComponent* equipComp = pawnOwner->GetEquipmentComponent();

	ensure(equipComp);

	if (!InternalCombatBehaviour) {
		return;
	}


	if (InternalCombatBehaviour->DefaultCombatBehaviorType == ECombatBehaviorType::EMelee) {
		abilityComp->TriggerAction(EquipMeleeAction, EActionPriority::EMedium);
		aiController->SetCombatStateBK(EAICombatState::EMeleeCombat);
	}
	else if (InternalCombatBehaviour->DefaultCombatBehaviorType == ECombatBehaviorType::ERanged) {
		abilityComp->TriggerAction(EquipRangedAction, EActionPriority::EMedium);
		aiController->SetCombatStateBK(EAICombatState::ERangedCombat);
	}
}

void UACFCombatBehaviourComponent::UninitBehavior()
{
	if (!InternalCombatBehaviour) {
		return;
	}
	if (InternalCombatBehaviour->bNeedsWeapon && pawnOwner && InternalCombatBehaviour && pawnOwner->GetCombatType() != ECombatType::EUnarmed) {
		const FGameplayTag unequipAction = InternalCombatBehaviour->DefaultCombatBehaviorType == ECombatBehaviorType::EMelee ? EquipMeleeAction : EquipRangedAction;
		abilityComp->TriggerAction(unequipAction, EActionPriority::EHigh);
	}


	if (UACFAIManagerSubsystem* Subsystem = GetWorld()->GetSubsystem<UACFAIManagerSubsystem>())
	{
		Subsystem->RemoveAIFromBattle(aiController);
	}
}

bool UACFCombatBehaviourComponent::CheckEquipment()
{
	if (!pawnOwner || !InternalCombatBehaviour) {
		return false;
	}
	return (pawnOwner->GetCombatType() != ECombatType::EMelee && InternalCombatBehaviour->bNeedsWeapon && InternalCombatBehaviour->DefaultCombatBehaviorType == ECombatBehaviorType::EMelee) ||
		(pawnOwner->GetCombatType() != ECombatType::ERanged && InternalCombatBehaviour->bNeedsWeapon && InternalCombatBehaviour->DefaultCombatBehaviorType == ECombatBehaviorType::ERanged);
}

void UACFCombatBehaviourComponent::UpdateCombatLocomotion(EAICombatState combatState)
{
	if (!InternalCombatBehaviour) {
		return;
	}
	const FAICombatStateConfig* locstate = InternalCombatBehaviour->CombatStatesConfig.FindByKey(combatState);
	if (locstate && moventComp) {
		moventComp->SetLocomotionState(locstate->LocomotionState);
	}
}

bool UACFCombatBehaviourComponent::EvaluateCombatState(EAICombatState combatState)
{
	if (!InternalCombatBehaviour) {
		return false;
	}
	if (!InternalCombatBehaviour->CombatStatesConfig.Contains(combatState)) {
		return false;
	}

	const FAICombatStateConfig* chance = InternalCombatBehaviour->CombatStatesConfig.FindByKey(combatState);

	if (chance) {
		for (auto condition : chance->Conditions) {
			if (!condition) {
				UE_LOG(ACFAILog, Error, TEXT("INVALID ACTION CONDITION IN COMBAT CONFIG! - UACFCombatBehaviourComponent"));
				continue;
			}
			if (condition && !condition->IsConditionMet(pawnOwner)) {
				return false;
			}
		}
		return FMath::RandRange(0.f, 100.f) <= chance->TriggerChancePercentage;
	}
	return false;
}

// void UACFCombatBehaviourComponent::UpdateBehaviorType()
// {
// 	if (IdealDistanceByCombatState.Contains(ECombatBehaviorType::ERanged))
// 	{
// 		float* randegdist = IdealDistanceByCombatState.Find(ECombatBehaviorType::ERanged);
// 		if (randegdist &&  aiController->GetTargetActorDistanceBK() > *randegdist)
// 		{
// 			CurrentCombatBehaviorType = ECombatBehaviorType::ERanged;
// 			return;
// 		}
// 	}
// 	CurrentCombatBehaviorType = ECombatBehaviorType::EMelee;
// }
