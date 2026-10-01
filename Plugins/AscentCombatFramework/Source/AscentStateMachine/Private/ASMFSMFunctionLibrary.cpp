// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ASMFSMFunctionLibrary.h"
#include "ASMFSMComponent.h"
#include <GameFramework/Actor.h>

void UASMFSMFunctionLibrary::TriggerTransition(const  AActor* fsmOwner, const FGameplayTag& transition)
{
	if (!fsmOwner) {
		return ;
	}

	UASMFSMComponent* fsmComponent = Cast< UASMFSMComponent>(fsmOwner->FindComponentByClass(UASMFSMComponent::StaticClass()));

	if (fsmComponent) {
		 fsmComponent->TriggerTransition(transition);
	}
}

void UASMFSMFunctionLibrary::ClientTriggerTransition(const class AActor* fsmOwner, const FGameplayTag& transition)
{
	if (!fsmOwner) {
		return;
	}

	UASMFSMComponent* fsmComponent = Cast< UASMFSMComponent>(fsmOwner->FindComponentByClass(UASMFSMComponent::StaticClass()));

	if (fsmComponent) {
		fsmComponent->ClientTriggerTransition(transition);
	}
}

