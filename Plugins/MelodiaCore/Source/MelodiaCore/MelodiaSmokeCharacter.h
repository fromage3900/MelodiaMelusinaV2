#pragma once

#include "CoreMinimal.h"
#include "MelodiaCharacterBase.h"
#include "InputActionValue.h"
#include "MelodiaSmokeCharacter.generated.h"

class UInputMappingContext;
class UInputAction;
class UAnimMontage;
class USkeletalMeshComponent;
class UUserWidget;
class UMelodiaExplorationHUDWidget;

UCLASS(Blueprintable)
class MELODIACORE_API AMelodiaSmokeCharacter : public AMelodiaCharacterBase
{
	GENERATED_BODY()

public:
	AMelodiaSmokeCharacter();

	virtual void Tick(float DeltaSeconds) override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void BeginPlay() override;
	virtual void Landed(const FHitResult& Hit) override;

	/** Hair follows the production body pose and owns the water-hair materials. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Melodia|Smoke|Presentation")
	TObjectPtr<USkeletalMeshComponent> WaterHairMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke")
	float MoveSpeedScale = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke")
	float SprintSpeedMultiplier = 1.5f;

	/** Runtime sprint state consumed by HUD and presentation code. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Sprint")
	bool bIsSprinting = false;

	/** Cloth stays disabled until the skirt collision/weighting pass is stable. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Presentation")
	bool bEnableSkirtClothSimulation = false;

	/** Movement input is resolved from controller yaw instead of actor-local axes. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Melodia|Smoke|Input")
	bool bCameraRelativeMovement = true;

	/** Runtime-created mapping context for exploration movement */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputMappingContext> MoveMappingContext;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> MoveRightAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> LookAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> SprintAction;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> JumpInputAction;

	/** Explicit exploration interaction (F/E/gamepad face button). */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> InteractAction;

	/** Opens/closes the character-owned Orrery menu (M or Tab). */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Input")
	TObjectPtr<UInputAction> OrreryMenuAction;

	/** Native fallback for canonical pawns without the legacy ToggleOrreryMenu Blueprint function. */
	UPROPERTY(EditDefaultsOnly, Category="Melodia|Smoke|UI")
	TSoftClassPtr<UUserWidget> OrreryWidgetClass;

	UPROPERTY(Transient)
	TObjectPtr<UUserWidget> ActiveNativeOrreryWidget;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaExplorationHUDWidget> ExplorationHUDWidget;

	/** One-shot recovery pose played after a jump reaches the ground. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Animation")
	TObjectPtr<UAnimMontage> LandingMontage;

	// --- Nikki-style jump feel ---

	/** Grace window after walking off a ledge during which Jump still fires. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Jump", meta=(ClampMin="0.0", ClampMax="0.5"))
	float CoyoteTime = 0.12f;

	/** Pressing Jump this long before landing still triggers the jump on touchdown. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Jump", meta=(ClampMin="0.0", ClampMax="0.5"))
	float JumpBufferTime = 0.15f;

	/** Gravity while falling (not gliding) - heavier than rise for a snappy descent. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Jump")
	float FallGravityScale = 2.4f;

	/** Gravity near the arc apex - lighter for a floaty hang. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Jump")
	float ApexGravityScale = 1.1f;

	/** |Vz| below which the apex gravity applies. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Jump")
	float ApexVelocityThreshold = 150.0f;

	// --- Glide ---

	/** True while parasol-gliding; drives the AnimBP Glide state. */
	UPROPERTY(BlueprintReadOnly, Category="Melodia|Smoke|Glide")
	bool bIsGliding = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Glide")
	float GlideGravityScale = 0.1f;

	/** Terminal descent speed while gliding (negative Z, uu/s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Glide")
	float GlideTerminalZ = -180.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Glide")
	float GlideAirControl = 0.9f;

	/** Extra camera boom length while gliding. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Smoke|Glide")
	float GlideBoomExtension = 80.0f;

	UFUNCTION(BlueprintCallable, Category="Melodia|Smoke|Glide")
	void StartGlide();

	UFUNCTION(BlueprintCallable, Category="Melodia|Smoke|Glide")
	void StopGlide();

protected:
	virtual bool CanJumpInternal_Implementation() const override;
	virtual void UnPossessed() override;

private:
	float BaseWalkSpeed = 420.0f;

	// Rise gravity captured from the CDO value at BeginPlay.
	float BaseGravityScale = 1.6f;
	float BaseAirControl = 0.55f;
	float BaseBoomLength = 420.0f;

	float TimeSinceLeftGround = 0.0f;
	float TimeSinceJumpPressed = BIG_NUMBER;
	bool bJumpHeld = false;

	void OnMoveTriggered(const FInputActionValue& Value);
	void OnMoveRightTriggered(const FInputActionValue& Value);
	void OnLookTriggered(const FInputActionValue& Value);
	void OnSprintStarted();
	void OnSprintCompleted();
	void OnJumpStarted();
	void OnJumpCompleted();
	void OnInteractRequested();
	void OnOrreryMenuRequested();
	void CreateInputMappingContext();
};
