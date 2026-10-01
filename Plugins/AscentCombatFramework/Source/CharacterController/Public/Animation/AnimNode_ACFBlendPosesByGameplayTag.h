// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "AnimNodes/AnimNode_BlendListBase.h"
#include "AnimNode_ACFBlendPosesByGameplayTag.generated.h"

USTRUCT(BlueprintInternalUseOnly)
struct CHARACTERCONTROLLER_API FAnimNode_ACFBlendPosesByGameplayTag : public FAnimNode_BlendListBase
{
	GENERATED_BODY()

private:
#if WITH_EDITORONLY_DATA
	UPROPERTY(EditAnywhere, Category = BlendList, meta = (PinShownByDefault, FoldProperty))
	FGameplayTagContainer ActiveGameplayTags;

	UPROPERTY(meta = (FoldProperty))
	TArray<FGameplayTag> GameplayTags;
#endif

public:
	FAnimNode_ACFBlendPosesByGameplayTag() = default;

#if WITH_EDITORONLY_DATA
	void SetGameplayTags(const TArray<FGameplayTag>& InGameplayTags) { GameplayTags = InGameplayTags; }
#endif

	const FGameplayTagContainer& GetActiveGameplayTags() const;
	const TArray<FGameplayTag>& GetGameplayTags() const;

protected:
	virtual int32 GetActiveChildIndex() override;
	virtual FString GetNodeName(FNodeDebugData& DebugData) override { return DebugData.GetNodeName(this); }
};
