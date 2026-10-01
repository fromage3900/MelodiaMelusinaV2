// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Animation/ACFSetHandsIKEnabledNotify.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimSequenceBase.h"
#include "Animation/AnimNotifyQueue.h"
#include "Animation/ACFAnimInstance.h"

void UACFSetHandsIKEnabledNotify::Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	if (MeshComp) {
		UACFAnimInstance* animInst = Cast<UACFAnimInstance>(MeshComp->GetAnimInstance());
		if (animInst) {
			animInst->SetEnableHandIK(bEnabled);
		}
	}
}
