#pragma once

#include "CoreMinimal.h"
#include "MelodiaCharacterBase.h"
#include "InputActionValue.h"
#include "MelodiousFlightCharacter.generated.h"

class UInputMappingContext;
class UInputAction;

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

private:
	void OnMoveTriggered(const FInputActionValue& Value);
	void OnMoveRightTriggered(const FInputActionValue& Value);
	void OnLookTriggered(const FInputActionValue& Value);
	void OnAscendTriggered(const FInputActionValue& Value);
	void OnBoostStarted();
	void OnBoostCompleted();
	void CreateInputMappingContext();
};
