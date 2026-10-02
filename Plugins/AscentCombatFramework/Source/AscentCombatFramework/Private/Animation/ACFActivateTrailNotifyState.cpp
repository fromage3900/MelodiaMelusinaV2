// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Animation/ACFActivateTrailNotifyState.h"
#include "ACMCollisionManagerComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Game/ACFFunctionLibrary.h"

void UACFActivateTrailNotifyState::NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference)
{
	Super::NotifyBegin(MeshComp, Animation, TotalDuration, EventReference);
	if (!MeshComp || !MeshComp->GetOwner())
	{
		return;
	}

	const TArray<UACMCollisionManagerComponent*> Components = UACFFunctionLibrary::GetCollisionManagersFromActor(MeshComp->GetOwner(), TrailTarget);

	const TArray<FName> NamesToPlay = TrailNames;
	for (UACMCollisionManagerComponent* Comp : Components)
	{
		if (!Comp)
		{
			continue;
		}
		if (NamesToPlay.Num() == 0)
		{
			for (const auto& Pair : Comp->GetDamageTraces())
			{
				Comp->PlayTrails(Pair.Key);
				Comp->OnTrailActivated.Broadcast(Pair.Key);
			}
		}
		else
		{
			for (const FName& Name : NamesToPlay)
			{
				Comp->PlayTrails(Name);
				Comp->OnTrailActivated.Broadcast(Name);
			}
		}
	}
}

void UACFActivateTrailNotifyState::NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	Super::NotifyEnd(MeshComp, Animation, EventReference);
	if (!MeshComp || !MeshComp->GetOwner())
	{
		return;
	}

	const TArray<UACMCollisionManagerComponent*> Components = UACFFunctionLibrary::GetCollisionManagersFromActor(MeshComp->GetOwner(), TrailTarget);

	const TArray<FName> NamesToStop = TrailNames;
	for (UACMCollisionManagerComponent* Comp : Components)
	{
		if (!Comp)
		{
			continue;
		}
		if (NamesToStop.Num() == 0)
		{
			for (const auto& Pair : Comp->GetDamageTraces())
			{
				Comp->StopTrails(Pair.Key);
				Comp->OnTrailDeactivated.Broadcast(Pair.Key);
			}
		}
		else
		{
			for (const FName& Name : NamesToStop)
			{
				Comp->StopTrails(Name);
				Comp->OnTrailDeactivated.Broadcast(Name);
			}
		}
	}
}
