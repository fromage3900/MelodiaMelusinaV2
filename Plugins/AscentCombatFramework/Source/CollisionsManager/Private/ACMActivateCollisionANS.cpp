// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "ACMActivateCollisionANS.h"
#include "ACMCollisionManagerComponent.h"
#include <Components/SkeletalMeshComponent.h>
#include <Animation/AnimSequenceBase.h>
#include <GameFramework/Actor.h>

void UACMActivateCollisionANS::NotifyBegin(USkeletalMeshComponent * MeshComp, UAnimSequenceBase * Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference)
{
	if (!MeshComp)
		return;

	AActor* owner = MeshComp->GetOwner();

	if (!owner)
		return;

	UACMCollisionManagerComponent* collisionComp = owner->FindComponentByClass<UACMCollisionManagerComponent>();

	if (collisionComp)
	{
		for (const auto& trace : TracesToStart)
			collisionComp->StartSingleTrace(trace);
	}

}

void UACMActivateCollisionANS::NotifyEnd(USkeletalMeshComponent * MeshComp, UAnimSequenceBase * Animation, const FAnimNotifyEventReference& EventReference)
{
	if (!MeshComp)
		return;

	AActor* owner = MeshComp->GetOwner();

	if (!owner)
		return;

	UACMCollisionManagerComponent* collisionComp = owner->FindComponentByClass<UACMCollisionManagerComponent>();

	if (collisionComp)
	{
		for (const auto& trace : TracesToStart)
			collisionComp->StopSingleTrace(trace);
	}

}
