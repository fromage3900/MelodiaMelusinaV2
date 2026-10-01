// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "ACFNotifyExitAction.generated.h"

/**
 * 
 */
UCLASS()
class ACTIONSSYSTEM_API UACFNotifyExitAction : public UAnimNotify
{
	GENERATED_BODY()
	
protected:
	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
	
	
};
