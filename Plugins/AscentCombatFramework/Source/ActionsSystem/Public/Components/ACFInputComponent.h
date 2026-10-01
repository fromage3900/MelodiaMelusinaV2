// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "ACFInputConfigDataAsset.h"
#include <GameplayAbilitySpecHandle.h>
#include <GameplayTagContainer.h>
#include <EnhancedInputComponent.h>

#include "ACFInputComponent.generated.h"

class UACFInputConfigDataAsset;


/**
 * Component that handles input bindings for the Ability System
 * Automatically binds Enhanced Input Actions to Gameplay Abilities using tags
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ACTIONSSYSTEM_API UACFInputComponent : public UActorComponent {
	GENERATED_BODY()

public:
	UACFInputComponent();

	// Setup the input bindings from the data asset
	UFUNCTION(BlueprintCallable, Category = "ACF Input")
	void SetupInputBindings();

	// Clean up existing bindings
	UFUNCTION(BlueprintCallable, Category = "ACF Input")
	void CleanupInputBindings();

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// Data Asset containing binding configuration
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF Input")
	TObjectPtr<UACFInputConfigDataAsset> InputConfigDataAsset;

	// Reference to the Ability System Component
	UPROPERTY(BlueprintReadOnly, Category = "ACF Input")
	TObjectPtr<UAbilitySystemComponent> AbilitySystemComponent;

	// Reference to the Enhanced Input Component
	UPROPERTY(BlueprintReadOnly, Category = "ACF Input")
	TObjectPtr<UEnhancedInputComponent> EnhancedInputComponent;

	// Handle input press events
	void OnInputPressed(FGameplayTag AbilityTag);

	// Handle input release events
	void OnInputReleased(FGameplayTag AbilityTag);

	// Called when controller changes (possess/unpossess)
	UFUNCTION()
	void OnControllerChanged(APawn* Pawn, AController* OldController, AController* NewController);

	// Helper function to find the AbilitySystemComponent
	UFUNCTION(BlueprintCallable, Category = "ACF Input")
	UAbilitySystemComponent* GetAbilitySystemComponent() const;

private:
	// Map to track active ability handles for cancellation
	TMap<FGameplayTag, FGameplayAbilitySpecHandle> ActiveAbilityHandles;

	// Timer handle for delayed setup
	FTimerHandle SetupTimerHandle;
};
