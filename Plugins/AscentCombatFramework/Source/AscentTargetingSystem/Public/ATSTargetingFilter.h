// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include <GameFramework/Actor.h>
#include "ATSTargetingFilter.generated.h"

/**
 * 
 */
UCLASS(Blueprintable, BlueprintType, abstract, EditInlineNew, HideCategories = ("DoNotShow"), CollapseCategories, AutoExpandCategories = ("Default"))
class ASCENTTARGETINGSYSTEM_API UATSTargetingFilter : public UObject
{
	GENERATED_BODY()

		UATSTargetingFilter();

public:


	UFUNCTION(BlueprintNativeEvent, Category = ATS)
		bool IsActorTargetable(const AActor* componentOwner, const AActor* Target);
	virtual bool IsActorTargetable_Implementation(const AActor* componentOwner, const  AActor* Target);
// 	
};
