// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#pragma once

#include "CoreMinimal.h"
#include "Tasks/AITask.h"
#include "ACFTask.generated.h"

class AController;

/**
 * A generic task for AI Routines
 */
UCLASS(EditInlineNew, BlueprintType, Abstract, DefaultToInstanced, Blueprintable)
class AIFRAMEWORK_API UACFTask : public UObject
{
	GENERATED_BODY()

protected:

	/** Called when the task starts (overridable in BP) */
	UFUNCTION(BlueprintNativeEvent, Category = "ACF|Task")
	void OnTaskStarted(const APawn* ControlledPawn);
	virtual void OnTaskStarted_Implementation(const APawn* ControlledPawn);

	/** Called when the task ends (overridable in BP) */
	UFUNCTION(BlueprintNativeEvent, Category = "ACF|Task")
	void OnTaskEnded();
	virtual void OnTaskEnded_Implementation();

	void Internal_OnTaskStarted(const APawn* ControlledPawn);

	UFUNCTION(BlueprintPure, Category = ACF)
	AController* GetOwningController() const {
		return Controller;
	}

	UPROPERTY(Transient)
	AController* Controller;

	friend class UACFAIRoutineComponent;

};
