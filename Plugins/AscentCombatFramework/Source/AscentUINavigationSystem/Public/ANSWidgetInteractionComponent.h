// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/WidgetInteractionComponent.h"
#include "ANSWidgetInteractionComponent.generated.h"

class UCommonInputSubsystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnInteractionStateChanged, bool, bEnabled);

/**
 * Component that manages widget interaction for UI elements (gamepad or cursor).
 * Allows enabling or disabling interaction at runtime and broadcasts when the state changes.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTUINAVIGATIONSYSTEM_API UANSWidgetInteractionComponent : public UWidgetInteractionComponent
{
	GENERATED_BODY()

public:
	/** Default constructor */
	UANSWidgetInteractionComponent(const FObjectInitializer& ObjectInitializer);

	/**
	 * Enables or disables widget interaction.
	 * Also toggles ticking accordingly.
	 *
	 * @param bEnabled Whether to enable or disable the component.
	 */
	UFUNCTION(BlueprintCallable, Category = "ANS")
	void SetInteractionEnabled(bool bEnabled);

	/**
	 * Returns whether widget interaction is currently enabled.
	 *
	 * @return True if interaction is enabled, false otherwise.
	 */
	UFUNCTION(BlueprintPure, Category = "ANS")
	bool IsInteractionEnabled() const { return bIsInteractionEnabled; }

	/** Called whenever the interaction state changes. */
	UPROPERTY(BlueprintAssignable, Category = "ANS")
	FOnInteractionStateChanged OnInteractionStateChanged;




protected:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	virtual void BeginPlay() override;

private:


	/** Whether the component is currently active for interaction. */
	UPROPERTY()
	bool bIsInteractionEnabled = false;

	bool bIsUsingGamepad = false;

	UPROPERTY()
	TObjectPtr<APlayerController> PlayerController;

	UFUNCTION()
	void HandleInputChanged(ECommonInputType inputType);
	UCommonInputSubsystem* GetInputSubsystem() const;
};
