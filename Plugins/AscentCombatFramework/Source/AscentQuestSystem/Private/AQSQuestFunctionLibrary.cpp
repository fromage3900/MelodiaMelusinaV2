// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "AQSQuestFunctionLibrary.h"
#include <GameFramework/PlayerController.h>
#include "AQSQuestManagerComponent.h"
#include <Kismet/GameplayStatics.h>
#include "GameFramework/GameState.h"
#include "GameFramework/GameStateBase.h"

class UAQSQuestManagerComponent* UAQSQuestFunctionLibrary::GetQuestManager(const UObject* WorldContextObject)
{
	const APlayerController* playerController = UGameplayStatics::GetPlayerController(WorldContextObject, 0);
	if (playerController) {
		return playerController->FindComponentByClass<UAQSQuestManagerComponent>();
	}

	return nullptr;
}

class UAQSQuestManagerComponent* UAQSQuestFunctionLibrary::GetGlobalQuestManager(const UObject* WorldContextObject)
{
	const AGameStateBase* gameState = UGameplayStatics::GetGameState(WorldContextObject);
	if (gameState) {
		return gameState->FindComponentByClass<UAQSQuestManagerComponent>();
	}

	return nullptr;
}

// bool UAQSQuestFunctionLibrary::HasActiveObjective(const FAQSQuestRecord& quest, const FGameplayTag& objectiveTag)
// {
// 	return quest.Objectives.Contains(objectiveTag);
// }
