// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACFActionCondition.h"
#include "Actors/ACFCharacter.h"
#include "ACFAIController.h"
#include "ARSFunctionLibrary.h"
#include "ARSStatisticsComponent.h"
#include "Game/ACFFunctionLibrary.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Controller.h"
#include "ATSBaseTargetComponent.h"
#include "Logging.h"


bool UACFDistanceActionCondition::IsConditionMet_Implementation(const APawn* character)
{
	if (!character) {
		UE_LOG(ACFAILog, Warning, TEXT("No character found - UACFDistanceActionCondition"));
		return false;
	}

	const AController* aiController = character->GetController();
	AACFCharacter* target = nullptr;
	if (aiController) {
		const UATSBaseTargetComponent* targetComp = aiController->FindComponentByClass<UATSBaseTargetComponent>();		
		if (targetComp) {
			target = Cast<AACFCharacter>(targetComp->GetCurrentTarget());
		}
	}

	if (!target) {
		return false;
	}
	switch (ConditionType)
	{
	case EConditionType::EAbove:
		return UACFFunctionLibrary::CalculateDistanceBetweenActors(character, target) > Distance;
		break;
	case EConditionType::EBelow:
		return UACFFunctionLibrary::CalculateDistanceBetweenActors(character, target) < Distance;
		break;
	case EConditionType::EEqual:
		return (UACFFunctionLibrary::CalculateDistanceBetweenActors(character, target) > Distance - NearlyEqualAcceptance &&
			UACFFunctionLibrary::CalculateDistanceBetweenActors(character, target) < Distance + NearlyEqualAcceptance);
		break;
	}

	return false;

}

bool UACFStatisticActionCondition::IsConditionMet_Implementation(const APawn* character)
{
	if (!character) {
		UE_LOG(ACFAILog, Warning, TEXT("No character found - UACFStatisticActionCondition"));

		return false;
	}

	const UARSStatisticsComponent* statComp = character->FindComponentByClass<UARSStatisticsComponent>();

	if (!statComp) {
		UE_LOG(ACFAILog, Warning, TEXT("No Statistics Component found on character %s - UACFStatisticActionCondition"), *character->GetName());
		return false;
	}

	const float statValue = statComp->GetNormalizedValueForStatitstic(StatisticTag);

	switch (ConditionType)
	{
	case EConditionType::EAbove:
		return statValue > StatisticValuePercentage / 100.f;
		break;
	case EConditionType::EBelow:
		return statValue <= StatisticValuePercentage / 100.f;
		break;
	case EConditionType::EEqual:
		return (statValue > StatisticValuePercentage / 100.f - NearlyEqualAcceptance ||
			statValue < StatisticValuePercentage / 100.f + NearlyEqualAcceptance);
		break;
	}

	return false;
}
