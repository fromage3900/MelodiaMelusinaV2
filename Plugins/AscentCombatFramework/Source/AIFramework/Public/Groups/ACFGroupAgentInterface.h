// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "ACFGroupAgentInterface.generated.h"

// This class does not need to be modified.
UINTERFACE(MinimalAPI)
class UACFGroupAgentInterface : public UInterface
{
	GENERATED_BODY()
};

/**
 * 
 */
class AIFRAMEWORK_API IACFGroupAgentInterface
{
	GENERATED_BODY()

	// Add interface functions to this class. This is the class that will be inherited to implement this interface.
public:

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	class UACFGroupAIComponent* GetOwningGroup();

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
	bool IsPartOfGroup();
};
