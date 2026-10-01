// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFActivateDamageNotifyState.h"
#include "ACMCollisionManagerComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Game/ACFFunctionLibrary.h"

UACFActivateDamageNotifyState::UACFActivateDamageNotifyState()
{
}

void UACFActivateDamageNotifyState::NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference)
{
	Super::NotifyBegin(MeshComp, Animation, TotalDuration, EventReference);
	if (!MeshComp || !MeshComp->GetOwner())
	{
		return;
	}

	const TArray<UACMCollisionManagerComponent*> Components = UACFFunctionLibrary::GetCollisionManagersFromActor(MeshComp->GetOwner(), DamageToActivate);

	for (UACMCollisionManagerComponent* Comp : Components)
	{
		if (!Comp)
		{
			continue;
		}
		if (!Comp->IsRegistered())
		{
			Comp->RegisterComponent();
		}
		if (TraceChannels.Num() == 0)
		{
			Comp->StartAllTraces();
		}
		else
		{
			for (const FName& Channel : TraceChannels)
			{
				Comp->StartSingleTrace(Channel);
			}
		}
	}
}

void UACFActivateDamageNotifyState::NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	Super::NotifyEnd(MeshComp, Animation, EventReference);
	if (!MeshComp || !MeshComp->GetOwner())
	{
		return;
	}

	const TArray<UACMCollisionManagerComponent*> Components = UACFFunctionLibrary::GetCollisionManagersFromActor(MeshComp->GetOwner(), DamageToActivate);

	for (UACMCollisionManagerComponent* Comp : Components)
	{
		if (!Comp)
		{
			continue;
		}
		if (TraceChannels.Num() == 0)
		{
			Comp->StopAllTraces();
		}
		else
		{
			for (const FName& Channel : TraceChannels)
			{
				Comp->StopSingleTrace(Channel);
			}
		}
	}
}
