// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "ACFGroupAgentInterface.h"
#include "Game/ACFPlayerController.h"
#include "ACFCompanionsPlayerController.generated.h"



UCLASS()
class AIFRAMEWORK_API AACFCompanionsPlayerController : public AACFPlayerController, public IACFGroupAgentInterface
{
	GENERATED_BODY()


public: 

	AACFCompanionsPlayerController();

	UFUNCTION(BlueprintCallable, Category = ACF)
	void SwitchToNearestCompanion(float blendTime = 0.5f );

	UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = ACF)
	void SwitchPossessionToCharacer(class AACFCharacter* inCharacter, float blendTime = 0.5f );

	
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

	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE class UACFCompanionGroupAIComponent* GetCompanionsComponent() const { return CompanionsComponent; }


protected:

	virtual void BeginPlay() override;


	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = ACF)
	class UACFCompanionGroupAIComponent* CompanionsComponent;

	
private: 

	UFUNCTION()
	void Internal_SwitchPossessionTo(AACFCharacter* inCharacter);

};
