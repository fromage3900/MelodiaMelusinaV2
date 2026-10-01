// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotify.h"
#include "ACFNotifyAction.generated.h"

/**
 * 
 */
UCLASS()
class ACTIONSSYSTEM_API UACFNotifyAction : public UAnimNotify
{
	GENERATED_BODY()
	
protected: 
	virtual void Notify(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
	
public:

// 	UPROPERTY(EditAnywhere, Category = ACF)
// 	bool bActivateOnlyOnServer = true;
};
