// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include <GameplayTagContainer.h>
#include "ASMFSMFunctionLibrary.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTSTATEMACHINE_API UASMFSMFunctionLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public: 

	UFUNCTION(BlueprintCallable, Category = ASM)
	static void TriggerTransition(const class AActor* fsmOwner, const FGameplayTag& transition);

	UFUNCTION(BlueprintCallable, Category = ASM)
	static void ClientTriggerTransition(const class AActor* fsmOwner, const FGameplayTag& transition);
	
};
