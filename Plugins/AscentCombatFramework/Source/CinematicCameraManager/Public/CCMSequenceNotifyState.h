// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Animation/AnimNotifies/AnimNotifyState.h"
#include "CCMTypes.h"
#include "CCMSequenceNotifyState.generated.h"

/**
 * 
 */
UCLASS()
class CINEMATICCAMERAMANAGER_API UCCMSequenceNotifyState : public UAnimNotifyState
{
	GENERATED_BODY()


public:


	virtual void NotifyBegin(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, float TotalDuration, const FAnimNotifyEventReference& EventReference) override;
	virtual void NotifyEnd(USkeletalMeshComponent* MeshComp, UAnimSequenceBase* Animation, const FAnimNotifyEventReference& EventReference) override;
protected: 

	UPROPERTY(EditAnywhere, Category = CCM)
	bool bActivateOnlyIfOwningPlayer = true;

	UPROPERTY(EditAnywhere, Category = CCM)
	FCCMSequenceEvent SequenceModifier;
	
};
