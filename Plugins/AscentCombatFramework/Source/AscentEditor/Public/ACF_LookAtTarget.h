// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once


#include "CoreMinimal.h"
#include "AnimGraphNode_LookAt.h"
#include "EdGraph/EdGraphNodeUtils.h"
#include "BoneControllers/AnimNode_LookAt.h"
#include "AnimGraphNode_SkeletalControlBase.h"
#include "BoneControllers/AnimNode_SkeletalControlBase.h"
#include "Animation/AnimNode_ACFLookAtTarget.h"
#include "ACF_LookAtTarget.generated.h"

/**
 * 
 */
class FPrimitiveDrawInterface;
class USkeletalMeshComponent;

UCLASS(MinimalAPI, meta=(Keywords = "Look At, Follow, Trace, Track"))
class UACF_LookAtTarget : public UAnimGraphNode_SkeletalControlBase
{
	GENERATED_UCLASS_BODY()

  	UPROPERTY(EditAnywhere, Category=Settings)
  	FAnimNode_ACFLookAtTarget ACFNode;
public:

  /*  UACF_LookAtTarget(const FObjectInitializer& ObjectInitializer);*/
	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
/*	virtual FEditorModeID GetEditorMode() const override;*/


protected:
	// UAnimGraphNode_SkeletalControlBase interface
	virtual FText GetControllerDescription() const override;
	virtual const FAnimNode_SkeletalControlBase* GetNode() const override { return &ACFNode; }
	// End of UAnimGraphNode_SkeletalControlBase interface

	// UObject interface
	virtual void Serialize(FArchive& Ar) override;
	// End of UObject interface
	
};
