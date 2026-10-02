// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CASTypes.h"
#include "CASAnimSlaveComponent.generated.h"


UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class COMBINEDANIMATIONSSYSTEM_API UCASAnimSlaveComponent : public UActorComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UCASAnimSlaveComponent();

	/*Returns True if an animation with the provided tags exists in the DB*/
	UFUNCTION(BlueprintCallable, Category = CAS)
	bool SupportsAnimation(const FGameplayTag& animTag) const;

	/*Returns True if the owner supports the animTag provided and
	all conditions are verified*/
	UFUNCTION(BlueprintCallable, Category = CAS)
	bool CanStartCombinedAnimation(const FGameplayTag& animTag, const class ACharacter* animMaster);

	/*Returns as outParam the quested animation*/
	UFUNCTION(BlueprintCallable, Category = CAS)
	bool TryGetSlaveAnim(const FGameplayTag& animTag, FCombinedAnimsSlave& outSlave) const;

	UFUNCTION(BlueprintPure, Category = CAS)
	FORCEINLINE class ACharacter* GetCharacterOwner() const {
		return characterOwner;
	}

	UPROPERTY(BlueprintAssignable, Category = CAS)
	FOnCombinedAnimationStarted OnCombinedAnimationStarted;

	UPROPERTY(BlueprintAssignable, Category = CAS)
	FOnCombinedAnimationEnded OnCombinedAnimationEnded;

protected:
	// Called when the game starts
	virtual void BeginPlay() override;


	UPROPERTY(EditDefaultsOnly, Category = CAS)
	class UDataTable* SlaveAnimations;


	UPROPERTY(EditDefaultsOnly, Instanced, Category = CAS)
	TArray<class UCASAnimCondition*> AnimStartingConditions;

private: 

	bool VerifyConditions(const FGameplayTag& animTag, const class ACharacter* animMaster) ;

	class ACharacter* characterOwner;
		
  };
