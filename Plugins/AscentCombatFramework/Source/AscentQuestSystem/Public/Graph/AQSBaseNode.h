// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "AGSGraphNode.h"
#include "CoreMinimal.h"

#include "AQSBaseNode.generated.h"

/**
 *
 */
UCLASS(abstract)
class ASCENTQUESTSYSTEM_API UAQSBaseNode : public UAGSGraphNode {
    GENERATED_BODY()

public:
    virtual void ActivateNode() override;

    virtual void DeactivateNode() override;

    virtual bool CanBeActivated() const;

    UAQSBaseNode();

    /*True if this objective is completed*/
    UFUNCTION(BlueprintPure, Category = AQS)
    FORCEINLINE bool IsCompleted() const
    {
        return bIsCompleted;
    }

    /*Returns all the Activation Actions for this quest nod*/
     UFUNCTION(BlueprintPure, Category = AQS)
	TArray<class UAGSAction*> GetActivationActions() const { return ActivationActions; }

    /*Returns all the Complete Actions for this quest node*/
     UFUNCTION(BlueprintPure, Category = AQS)
	TArray<class UAGSAction*> GetOnCompletionActions() const { return OnCompletionActions; }

    
protected:
    /** List of Actions to execute when the quest starts */
    UPROPERTY(EditDefaultsOnly, Instanced, Category = "AQS|Events")
    TArray<class UAGSAction*> ActivationActions;

    /** List of Actions to execute upon quest completion */
    UPROPERTY(EditDefaultsOnly, Instanced, Category = "AQS|Events")
    TArray<class UAGSAction*> OnCompletionActions;

	virtual void CompleteNode() ;
    bool bIsCompleted;
};
