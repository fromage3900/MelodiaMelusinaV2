#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaWaterGameplayTypes.h"
#include "MelodiaWaterGameplayControllerComponent.generated.h"

class UMelodiaWaterGameplaySubsystem;

/** Blueprint-facing controller for devices and proof-map state fan-out. */
UCLASS(ClassGroup = (Melodia), BlueprintType, Blueprintable, meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaWaterGameplayControllerComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaWaterGameplayControllerComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Controller")
	bool RegisterConfiguredNode();

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Controller")
	bool InteractWithDevice(AActor* Instigator);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Water|Controller")
	bool SetRouteOpen(bool bOpen, FGameplayTag InRouteId);

	UFUNCTION(BlueprintPure, Category = "Melodia|Water|Controller")
	FMelodiaWaterNodeState GetCurrentState() const { return CurrentState; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller")
	FMelodiaWaterNodeConfig NodeConfig;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller")
	FName DeviceId = NAME_None;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller")
	EMelodiaWaterGameplayOperation InteractionOperation = EMelodiaWaterGameplayOperation::OpenValve;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float InteractionStrength = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller")
	FGameplayTag InteractionRouteId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller")
	FGameplayTag CompletionPuzzleId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melodia|Water|Controller")
	bool bAutoRegister = true;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Water|Controller")
	FMelodiaWaterGameplayStateChanged OnControllerStateChanged;

private:
	UFUNCTION()
	void HandleWaterStateChanged(FMelodiaWaterStateChange Change);

	UPROPERTY(Transient)
	FMelodiaWaterNodeState CurrentState;

	UPROPERTY(Transient)
	TWeakObjectPtr<UMelodiaWaterGameplaySubsystem> RegisteredSubsystem;
};

