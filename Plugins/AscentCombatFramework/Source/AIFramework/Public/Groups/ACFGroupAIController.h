// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include <Perception/AIPerceptionTypes.h>
#include "ACFGroupAgentInterface.h"
#include "ACFGroupAIController.generated.h"

/**
 * 
 */
UCLASS()
class AIFRAMEWORK_API AACFGroupAIController : public AAIController, public IACFGroupAgentInterface
{
	GENERATED_BODY()

protected:

	UPROPERTY(EditAnywhere, Category = ACF)
	bool bUseGroupPerception = true;

	UPROPERTY(EditAnywhere, Category = ACF)
	float UpdateControllerPositionTimeInterval = 1.0f;

	virtual void BeginPlay() override;

	virtual void EndPlay(EEndPlayReason::Type reason) override;

	virtual void OnPossess(APawn* InPawn) override;

public: 

	/// <summary>
	/// /Groupable Entity Interface
	/// </summary>
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
		class UACFGroupAIComponent* GetOwningGroup();
	virtual class UACFGroupAIComponent* GetOwningGroup_Implementation() override;

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
		bool IsPartOfGroup();
	virtual bool IsPartOfGroup_Implementation() override;
	/// <summary>
	/// /End Groupable Entity
	/// </summary>

	AACFGroupAIController();
private: 

	UFUNCTION()
	void HandlePerceptionUpdated(AActor* Actor, FAIStimulus Stimulus);

    TObjectPtr<class UACFGroupAIComponent> groupComp;
};
