// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "CineCameraComponent.h"
#include "GameplayTagContainer.h"
#include "Camera/CameraComponent.h"
#include "Components/SceneComponent.h"
#include "CCMTypes.h"
#include "ACFCameraPointComponent.generated.h"



/**
 * Lightweight camera point marker with optional automated movement presets.
 * Inherits from UCineCameraComponent for full cinematic camera features.
 * Tick is automatically enabled when activated and disabled when deactivated.
 */
UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CINEMATICCAMERAMANAGER_API UACFCameraPointComponent : public UCineCameraComponent
{
	GENERATED_BODY()

public:
	UACFCameraPointComponent();
	//~ Begin UActorComponent Interface
	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
	//~ End UActorComponent Interface


protected:

	/** GameplayTag used to resolve this point (e.g., Camera.Battle.Attack1) */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF", meta = (Categories = "Camera"))
	FGameplayTag CameraTag;

	/** Configuration for automated camera movement when activated */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FACFCameraMovementConfig MovementConfig;

	/** Delay before restoring initial transform on deactivation (allows blend to start first) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera Point|Movement", meta = (ClampMin = "0.0"))
	float RestoreDelay = 0.1f;
public:


	/**
	 * Gets the camera tag used to resolve this point.
	 * @return The camera gameplay tag
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FGameplayTag GetCameraTag() const { return CameraTag; }


	/**
	 * Gets the movement configuration.
	 * @return The movement config struct
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE FACFCameraMovementConfig GetMovementConfig() const { return MovementConfig; }
	/**
	 * Checks if this camera point is currently active.
	 * @return True if the camera is active
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool IsActivated() const { return bIsActivated; }

	/**
	 * Checks if movement is currently running.
	 * @return True if movement is active
	 */
	UFUNCTION(BlueprintPure, Category = ACF)
	FORCEINLINE bool IsMovementRunning() const { return bIsMovementRunning; }

	// ========================================================================
	// Movement Control
	// ========================================================================

	/**
	 * Stops the current movement. Camera stays at current position.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void StopMovement();

	/**
	 * Resumes movement from current position.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void ResumeMovement();

	/**
	 * Stops movement and resets camera to initial position.
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void ResetMovement();

	// ========================================================================
	// Setters
	// ========================================================================

	/**
	 * Sets the movement preset at runtime.
	 * @param NewPreset - The new movement preset to use
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void SetMovementPreset(EACFCameraMovementPreset NewPreset);

	/**
	 * Sets the movement speed.
	 * @param NewSpeed - Speed in degrees/sec for orbit, units/sec for crane
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void SetMovementSpeed(float NewSpeed);

	/**
	 * Sets the look-at height offset from owner.
	 * @param NewOffset - Height offset in units
	 */
	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void SetLookAtHeightOffset(float NewOffset);

	UFUNCTION(BlueprintCallable, Category = "ACF|Movement")
	void SetCameraTag(const FGameplayTag& inTag) {
		CameraTag = inTag;
	}


	virtual void OnCameraActivated();
	virtual void OnCameraDeactivated();
protected:


	/*
	*Blueprint event for custom movement logic.
	* Called every tick when MovementPreset is set to Custom.
	* @param DeltaTime - Time elapsed since last tick
	*/
	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnCustomMovementTick(float DeltaTime);

	/**
	 * Processes the configured movement preset.
	 * @param DeltaTime - Time elapsed since last tick
	 */
	virtual void ProcessMovementPreset(float DeltaTime);

	/**
	 * Executes rotate around owner movement. Always looks at owner.
	 * @param DeltaTime - Time elapsed since last tick
	 */
	virtual void ProcessRotateAroundOwner(float DeltaTime);

	/**
	 * Executes crane movement. Always looks at owner.
	 * @param DeltaTime - Time elapsed since last tick
	 */
	virtual void ProcessCrane(float DeltaTime);

	/**
	* Executes lateral pan movement. Always looks at owner.
	* @param DeltaTime - Time elapsed since last tick
	*/
	virtual void ProcessPanLateral(float DeltaTime);

	/**
	 * Updates camera rotation to look at owner.
	 */
	void UpdateLookAtOwner();

	/**
	 * Gets the look-at target position (owner location + height offset).
	 * @return Target position to look at
	 */
	FVector GetLookAtTarget() const;

	/**
	 * Restores the camera to its initial transform immediately.
	 */
	void RestoreInitialTransform();

	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnActivated();

	UFUNCTION(BlueprintNativeEvent, Category = ACF)
	void OnDeactivated();

#if WITH_EDITORONLY_DATA
	/** Editor-only: draw a small frustum gizmo to preview orientation/FOV */
	UPROPERTY(EditAnywhere, Category = "Debug")
	bool bDrawPreviewFrustum = true;

	/** Editor-only: length of the preview frustum (cm) */
	UPROPERTY(EditAnywhere, Category = "Debug", meta = (ClampMin = "10.0", ClampMax = "100000.0"))
	float PreviewFrustumLength = 300.0f;
#endif
private:
	/** Whether this camera point is currently active */
	bool bIsActivated = false;

	/** Whether movement is currently running */
	bool bIsMovementRunning = false;

	/** Cached initial relative transform for restoration */
	FTransform InitialRelativeTransform;

	/** Current orbit angle in radians (for RotateAroundOwner) */
	float CurrentOrbitAngle = 0.0f;

	/** Cached orbit radius calculated from initial camera-owner distance */
	float CachedOrbitRadius = 0.0f;

	/** Cached orbit height offset calculated from initial camera Z relative to owner */
	float CachedOrbitHeightOffset = 0.0f;

	/** Current crane height offset (for Crane) */
	float CurrentCraneOffset = 0.0f;

	/** Current lateral offset (for PanLateral) */
	float CurrentLateralOffset = 0.0f;

	/** Timer handle for delayed restore */
	FTimerHandle RestoreTimerHandle;

};
