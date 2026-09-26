#pragma once

#include "CoreMinimal.h"
#include "MelodiaCharacterBase.h"
#include "InputActionValue.h"
#include "MelodiousFlightCharacter.generated.h"

class UInputMappingContext;
class UInputAction;
class ASirPerchPoint;

/**
 * Sir Melodious free-flight exploration pawn. Always airborne (MOVE_Flying);
 * WASD steers along the camera (including pitch), Space ascends, Shift boosts,
 * Ctrl hands control back to the party subsystem.
 */
UCLASS(Blueprintable)
class MELODIACORE_API AMelodiousFlightCharacter : public AMelodiaCharacterBase
{
	GENERATED_BODY()

public:
	AMelodiousFlightCharacter();

	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void BeginPlay() override;
	virtual void UnPossessed() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Flight")
	float CruiseSpeed = 800.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Flight")
	float BoostSpeed = 1600.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Flight|Input")
	TObjectPtr<UInputMappingContext> FlightMappingContext;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Flight|Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Flight|Input")
	TObjectPtr<UInputAction> MoveRightAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Flight|Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Flight|Input")
	TObjectPtr<UInputAction> AscendAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Flight|Input")
	TObjectPtr<UInputAction> BoostAction;

	// ------------------------------------------------------------------
	// Perching (D1: authored perches). Sir settles onto the nearest
	// ASirPerchPoint after going idle, and takes off again the moment the
	// player gives him input. He never scans raw geometry for a landing.
	// ------------------------------------------------------------------

	/** Radius searched for a perch when idle. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Perch", meta=(ClampMin="0.0"))
	float PerchSearchRadius = 600.0f;

	/** Seconds of no steering input before Sir looks for somewhere to sit. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Perch", meta=(ClampMin="0.0"))
	float PerchIdleDelay = 1.5f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Perch")
	bool bIsPerched = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Perch")
	TObjectPtr<ASirPerchPoint> CurrentPerch = nullptr;

	UFUNCTION(BlueprintCallable, Category="Melodia|Perch")
	bool TryLandOnNearestPerch();

	UFUNCTION(BlueprintCallable, Category="Melodia|Perch")
	void LeavePerch();

	/** Nearest perch within PerchSearchRadius, or nullptr. */
	UFUNCTION(BlueprintPure, Category="Melodia|Perch")
	ASirPerchPoint* FindNearestPerch(float& OutDistance) const;

private:
	void OnMoveTriggered(const FInputActionValue& Value);
	void OnMoveRightTriggered(const FInputActionValue& Value);
	void OnLookTriggered(const FInputActionValue& Value);
	void OnAscendTriggered(const FInputActionValue& Value);
	void OnBoostStarted();
	void OnBoostCompleted();
	void CreateInputMappingContext();

	/** Seconds since the last steering input; drives the idle perch. */
	float SecondsSinceSteering = 0.0f;

	/** Boost suppresses the idle perch - a boosted bird is never at rest. */
	bool bIsBoosting = false;
};
