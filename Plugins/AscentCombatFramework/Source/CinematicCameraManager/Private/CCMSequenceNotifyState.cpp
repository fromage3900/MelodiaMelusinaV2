// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#include "CCMSequenceNotifyState.h"
#include <Kismet/GameplayStatics.h>
#include <Components/SkeletalMeshComponent.h>
#include "CCMPlayerCameraManager.h"
#include "CCMCameraFunctionLibrary.h"

void UCCMSequenceNotifyState::NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference)
{
	Super::NotifyBegin(MeshComp, Animation, TotalDuration, EventReference);

	if (bActivateOnlyIfOwningPlayer &&
		(MeshComp->GetOwner()) != (AActor*)UGameplayStatics::GetPlayerCharacter(MeshComp, 0)){
		return;
	}

	ACCMPlayerCameraManager* cameraMan = UCCMCameraFunctionLibrary::GetLocalCinematicCameraManager(MeshComp);
	if (cameraMan) {
		cameraMan->AddSequenceEventModifier(SequenceModifier);
	}
}

void UCCMSequenceNotifyState::NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference)
{
	Super::NotifyEnd(MeshComp, Animation, EventReference);

	if (bActivateOnlyIfOwningPlayer &&
		(MeshComp->GetOwner()) != (AActor*)UGameplayStatics::GetPlayerCharacter(MeshComp, 0)) {
		return;
	}

	ACCMPlayerCameraManager* cameraMan = UCCMCameraFunctionLibrary::GetLocalCinematicCameraManager(MeshComp);
	if (cameraMan) {
		cameraMan->RemoveSequenceEventModifier(SequenceModifier);
	}
}
