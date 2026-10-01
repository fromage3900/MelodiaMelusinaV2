// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AGSGraphEdge.h"
#include "ADSGraphEdge.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSGraphEdge : public UAGSGraphEdge
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = ADS)
	bool CanBeActivated( APlayerController* controller) const;
	
protected:

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Instanced, Category = ADS)
	TArray<class UAGSCondition*> ActivationConditions;


};
