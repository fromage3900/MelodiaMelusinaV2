// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Graph/ADSGraphNode.h"
#include "Graph/ADSDialogueNode.h"
#include "ADSDialogueResponseNode.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSDialogueResponseNode : public UADSGraphNode
{
	GENERATED_BODY()

protected: 

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ADS)
	bool bAllowedForEveryPlayer = true;

	
#if WITH_EDITOR

	virtual void InitializeNode() override;

#endif

public: 

	UADSDialogueResponseNode();

	UFUNCTION(BlueprintCallable, Category = ADS)
	class UADSDialogueNode* ResponseSelected();

	virtual bool CanBeActivated(class APlayerController* inController) override;
};
