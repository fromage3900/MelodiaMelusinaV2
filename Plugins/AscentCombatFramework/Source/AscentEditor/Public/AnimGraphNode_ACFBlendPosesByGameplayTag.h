// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "AnimGraphNode_BlendListBase.h"
#include "Animation/AnimNode_ACFBlendPosesByGameplayTag.h"
#include "AnimGraphNode_ACFBlendPosesByGameplayTag.generated.h"

UCLASS(MinimalAPI, meta = (Keywords = "ACF Blend Poses Gameplay Tag"))
class UAnimGraphNode_ACFBlendPosesByGameplayTag : public UAnimGraphNode_BlendListBase
{
	GENERATED_UCLASS_BODY()

	UPROPERTY(EditAnywhere, Category = Settings)
	FAnimNode_ACFBlendPosesByGameplayTag Node;

protected:
	UPROPERTY(EditAnywhere, EditFixedSize, Category = GameplayTags)
	TArray<FGameplayTag> TagEntries;

public:
	// UEdGraphNode interface
	virtual FText GetNodeTitle(ENodeTitleType::Type TitleType) const override;
	virtual FText GetTooltipText() const override;
	virtual void GetNodeContextMenuActions(class UToolMenu* Menu, class UGraphNodeContextMenuContext* Context) const override;
	// End of UEdGraphNode interface

	// UAnimGraphNode_Base interface
	virtual void CustomizePinData(UEdGraphPin* Pin, FName SourcePropertyName, int32 ArrayIndex) const override;
	virtual void BakeDataDuringCompilation(class FCompilerResultsLog& MessageLog) override;
	virtual void PostEditChangeProperty(struct FPropertyChangedEvent& PropertyChangedEvent) override;
	// End of UAnimGraphNode_Base interface

private:
	void AddPosePin();
	void RemovePosePin(UEdGraphPin* Pin);

	static void GetPinInformation(const FString& InPinName, int32& Out_PinIndex, bool& Out_bIsPosePin, bool& Out_bIsTimePin);
};
