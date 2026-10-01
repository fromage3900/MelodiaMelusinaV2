// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "AQSQuestFunctionLibrary.generated.h"

/**
 * 
 */



UCLASS()
class ASCENTQUESTSYSTEM_API UAQSQuestFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public: 

	/*retrieve local quest manager from PlayerController*/
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = AQS)
	static class UAQSQuestManagerComponent* GetQuestManager(const UObject* WorldContextObject);

	/*retrieve local quest manager from GameState. To be used for party quests*/
	UFUNCTION(BlueprintPure, meta = (WorldContext = "WorldContextObject"), Category = AQS)
	static class UAQSQuestManagerComponent* GetGlobalQuestManager(const UObject* WorldContextObject);
// 
// 	/*retrieve local quest manager from GameState. To be used for party quests*/
// 	UFUNCTION(BlueprintCallable, Category = AQS)
// 	static bool HasActiveObjective(const FAQSQuestRecord& quest, const FGameplayTag& objectiveTag);
// 	
};
