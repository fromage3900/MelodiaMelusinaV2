// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "ADSDialogueNode.h"
#include "ADSStartDialogueNode.generated.h"

/**
 * 
 */
UCLASS()
class ASCENTDIALOGUESYSTEM_API UADSStartDialogueNode : public UADSDialogueNode
{
	GENERATED_BODY()

public: 

	UADSStartDialogueNode();

	virtual bool CanBeActivated(APlayerController* controller)  override ;

	void ExecuteEndingActions();

    virtual void ActivateNode() override;
	
    UPROPERTY(EditAnywhere, Category = "ADS|Camera")
    TSoftObjectPtr<ATargetPoint> EnforcedPlayerPosition;

protected: 
	
    // These actions will be performed when the dialogue ends
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Instanced, Category = ADS)
    TArray<class UAGSAction*> DialogueEndedActions;

};
