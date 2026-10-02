// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Animation/ACFGoRagdollNotify.h"
#include "Actors/ACFCharacter.h"
#include "Components/ACFRagdollComponent.h"


void UACFGoRagdollNotify::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	Super::Notify(MeshComp, Animation, EventReference);

	const AACFCharacter* acfChar = Cast<AACFCharacter>(MeshComp->GetOwner());
	if (acfChar) {
		acfChar->GetRagdollComponent()->GoRagdoll(RagdollImpulse);
	}
}
