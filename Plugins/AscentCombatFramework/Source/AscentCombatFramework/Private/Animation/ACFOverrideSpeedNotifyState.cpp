// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "Animation/ACFOverrideSpeedNotifyState.h"
#include <Components/SkeletalMeshComponent.h>
#include <Animation/AnimSequenceBase.h>
#include "Components/ACFCharacterMovementComponent.h"
#include "ACFActionTypes.h"

UACFOverrideSpeedNotifyState::UACFOverrideSpeedNotifyState()
{

}

void UACFOverrideSpeedNotifyState::NotifyBegin(USkeletalMeshComponent * MeshComp, UAnimSequenceBase * Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference)
{
	
	UACFCharacterMovementComponent* LocComp = MeshComp->GetOwner()->FindComponentByClass<UACFCharacterMovementComponent>();
// 	if (LocComp) {
// 		LocComp->SetMontageReprodutionType(EMontageReproductionType::ECurveOverrideSpeed);
// 	}
}

void UACFOverrideSpeedNotifyState::NotifyEnd(USkeletalMeshComponent * MeshComp, UAnimSequenceBase * Animation, const FAnimNotifyEventReference& EventReference)
{
	UACFCharacterMovementComponent* LocComp = MeshComp->GetOwner()->FindComponentByClass<UACFCharacterMovementComponent>();
// 	if (LocComp) {
// 		LocComp->SetMontageReprodutionType(EMontageReproductionType::ERootMotion);
// 	}
}
