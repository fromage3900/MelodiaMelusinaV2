// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Animation/ACFSetFeetIKEnabledNotify.h"
#include "Animation/ACFAnimInstance.h"
#include "Components/SkeletalMeshComponent.h"

void UACFSetFeetIKEnabledNotify::Notify(USkeletalMeshComponent* MeshComp, class UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	if (MeshComp) {
		UACFAnimInstance* animInst = Cast<UACFAnimInstance>(MeshComp->GetAnimInstance());
		if (animInst) {
			animInst->SetEnableFootIK(bEnabled);
		}
	}
}
