// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "ATSBaseTargetComponent.h"
#include "ATSAITargetComponent.generated.h"

/**
 * 
 */
UCLASS(ClassGroup = (ATS), Blueprintable, meta = (BlueprintSpawnableComponent))
class ASCENTTARGETINGSYSTEM_API UATSAITargetComponent : public UATSBaseTargetComponent
{
	GENERATED_BODY()
	
public: 


	virtual	void SetCurrentTarget(class AActor* target) override;

};
