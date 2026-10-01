// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "ATSTargetableInterface.generated.h"

// This class does not need to be modified.
UINTERFACE(Blueprintable)
class ASCENTTARGETINGSYSTEM_API UATSTargetableInterface : public UInterface {
	GENERATED_BODY()
};

/**
 * 
 */
class ASCENTTARGETINGSYSTEM_API IATSTargetableInterface
{
	GENERATED_BODY()

	// Add interface functions to this class. This is the class that will be inherited to implement this interface.
public:

	IATSTargetableInterface() {};

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ATS)
	void OnTargetAcquired(class UATSTargetPointComponent* point);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ATS)
	void OnTargetLosed();
};
