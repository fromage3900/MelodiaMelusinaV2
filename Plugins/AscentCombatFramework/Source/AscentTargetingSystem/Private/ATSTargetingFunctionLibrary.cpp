// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ATSTargetingFunctionLibrary.h"
#include "ATSBaseTargetComponent.h"  
#include "ATSTargetPointComponent.h"  
#include "GameFramework/Controller.h" 
#include "GameFramework/Pawn.h" 

AActor* UATSTargetingFunctionLibrary::GetTargetedActor(const APawn* pawn)
{
	if (pawn) {
		const TObjectPtr<AController> controller = pawn->GetController();
		if (controller) {
			const TObjectPtr<UATSBaseTargetComponent> target = controller->FindComponentByClass<UATSBaseTargetComponent>();
			if (target) {
				return target->GetCurrentTarget();
			}
		}
	}
	return nullptr;
}

UATSTargetPointComponent* UATSTargetingFunctionLibrary::GetCurrentTargetPoint(const APawn* pawn)
{
	if (pawn) {
		const TObjectPtr<AController> controller = pawn->GetController();
		if (controller) {
			const TObjectPtr<UATSBaseTargetComponent> target = controller->FindComponentByClass<UATSBaseTargetComponent>();
			if (target) {
				if (target->GetCurrentTargetPoint())
				{
					return target->GetCurrentTargetPoint();
				}
				else if(AActor* targetActor = target->GetCurrentTarget())
				{
					return targetActor->FindComponentByClass<UATSTargetPointComponent>();
				}
			}
		}
	}
	return nullptr;
}
