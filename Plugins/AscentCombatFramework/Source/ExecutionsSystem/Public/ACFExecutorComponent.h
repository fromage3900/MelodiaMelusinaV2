// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include <GameplayTagContainer.h>
#include "Game/ACFTypes.h"
#include "CASAnimMasterComponent.h"
#include "Game/ACFDamageType.h"
#include "ACFExecutorComponent.generated.h"




USTRUCT(BlueprintType)
struct FExecution
{
	GENERATED_BODY()

public:

	/*The animation COmbined To Be Played*/
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
	FGameplayTag AnimationTag;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
	FName CameraEvent;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
	bool bIsFatal = true;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
	bool bCanBeHitDuringAnim = false;

	/*the chance this animation will be triggered in the array*/
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
	float Weight = 1.f;
};

USTRUCT(BlueprintType)
struct FExecutionArray
{
	GENERATED_BODY()

public:

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly,meta = (TitleProperty = "AnimationTag"), Category = "ACF")
	TArray< FExecution> ExecutionTag;

};


USTRUCT(BlueprintType)
struct FExecutions
{
	GENERATED_BODY()

public:

	/*The executable animations categorized by moveset action*/
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF")
	TMap<FGameplayTag, FExecutionArray> ExecutionsByMovesetAction;

};


UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class EXECUTIONSSYSTEM_API UACFExecutorComponent : public UCASAnimMasterComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UACFExecutorComponent();

protected:
	// Called when the game starts
	virtual void BeginPlay() override;


	UPROPERTY(EditDefaultsOnly, BlueprintReadWrite, Category = ACF)
 	TMap<ERelativeDirection, FExecutions> ExecutionsByDirectionAndMovesetAction;

	virtual void OnCombinedAnimStarted(const FGameplayTag& animTag) override;
	virtual void OnCombinedAnimEnded(const FGameplayTag& animTag) override;

public:	


	UFUNCTION(BlueprintCallable, Category = ACF)
	bool TryExecuteCharacter(class ACharacter* target);

	UFUNCTION(BlueprintCallable, Category = ACF)
	bool TryExecuteCurrentTarget();

private:

	bool TryGetBestExecutionTag(const FGameplayTag& actualTag, const TMap<ERelativeDirection, FExecutions>& execMap, ERelativeDirection dir, FExecution& outExec);

	void SetCharacterActionsLock(ACharacter* target, bool lockstatus, bool canBeHit);

	FGameplayTag GetBestExecutionTagForCharacter(const TMap<ERelativeDirection, FExecutions>& execMap, class ACharacter* target);

	UPROPERTY(Replicated)
	FExecution currentBestExec;

};
