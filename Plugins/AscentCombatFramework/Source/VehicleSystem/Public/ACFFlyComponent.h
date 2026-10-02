// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PawnMovementComponent.h"
#include "Engine/EngineTypes.h"

#include "ACFFlyComponent.generated.h"

class UFloatingPawnMovement;

/**
 * High level flight state machine for the spaceship. Unlike a character flying state
 * (MOVE_Flying vs MOVE_Walking) a pawn has no built-in mode so we model the
 * takeoff/landing phases explicitly here.
 */
UENUM(BlueprintType)
enum class EACFFlyPhase : uint8 {
    Grounded    UMETA(DisplayName = "Grounded"),
    TakingOff   UMETA(DisplayName = "TakingOff"),
    Flying      UMETA(DisplayName = "Flying"),
    Landing     UMETA(DisplayName = "Landing")
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnFlyStateChanged, bool, bEnabled);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnFlyPhaseChanged, EACFFlyPhase, NewPhase);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTakeOffCompleted);
DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnLandingCompleted);

/**
 * UACFFlyComponent is a thin flight controller for spaceship-like pawns.
 *
 * Responsibilities:
 *  - Smooth player input on linear and angular axes.
 *  - Forward smoothed linear input to AddInputVector(): translation is integrated
 *    by a separate UFloatingPawnMovement living on the same pawn (auto-discovered).
 *  - Forward smoothed angular input to APawn::AddControllerYawInput / PitchInput,
 *    and write the roll directly into the controller's ControlRotation.Roll.
 *    The pawn is expected to have bUseControllerRotationPitch/Yaw/Roll = true so
 *    the mesh follows the control rotation natively.
 *  - Drive the high-level Grounded/TakingOff/Flying/Landing state machine and
 *    replicate it (server is authoritative; client RPCs ask the server to switch).
 *
 * What this component intentionally does NOT do:
 *  - It does not integrate Velocity, does not call SafeMoveUpdatedComponent, and
 *    does not compute physical roll from yaw. Those concerns belong to
 *    UFloatingPawnMovement / the pawn rotation pipeline / animation.
 */
UCLASS(ClassGroup = (ACF), Blueprintable, meta = (BlueprintSpawnableComponent))
class VEHICLESYSTEM_API UACFFlyComponent : public UPawnMovementComponent {
    GENERATED_BODY()

public:
    UACFFlyComponent();

    // --- Delegates ---------------------------------------------------------

    UPROPERTY(BlueprintAssignable, Category = "ACF|Fly")
    FOnFlyStateChanged OnFlyStateChanged;

    UPROPERTY(BlueprintAssignable, Category = "ACF|Fly|Phases")
    FOnFlyPhaseChanged OnFlyPhaseChanged;

    UPROPERTY(BlueprintAssignable, Category = "ACF|Fly|Phases")
    FOnTakeOffCompleted OnTakeOffCompleted;

    UPROPERTY(BlueprintAssignable, Category = "ACF|Fly|Phases")
    FOnLandingCompleted OnLandingCompleted;

    // --- Movement feel (intentionally minimal) -----------------------------

    /** Higher = snappier response, lower = smoother. Applied to linear axes. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Feel", meta = (ClampMin = "0.1"))
    float LinearInputSmoothing = 6.f;

    /** Higher = snappier response, lower = smoother. Applied to yaw/pitch/roll. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Feel", meta = (ClampMin = "0.1"))
    float AngularInputSmoothing = 8.f;

    /** Multiplier on yaw/pitch/roll inputs before they are forwarded to the controller. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Feel", meta = (ClampMin = "0"))
    float AngularSensitivity = 1.f;

    // --- Phase parameters (kept from previous version) ---------------------

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases", meta = (ClampMin = "0"))
    float TakeOffAltitude = 800.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases", meta = (ClampMin = "0"))
    float TakeOffVerticalSpeed = 400.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases")
    bool bLockInputDuringTakeOff = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases", meta = (ClampMin = "0"))
    float LandingVerticalSpeed = 250.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases")
    bool bLockInputDuringLanding = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases")
    bool bLevelOutBeforeLanding = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases",
        meta = (EditCondition = "bLevelOutBeforeLanding", ClampMin = "0"))
    float LandingLevelInterpSpeed = 4.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases",
        meta = (EditCondition = "bLevelOutBeforeLanding", ClampMin = "0"))
    float LandingLevelTolerance = 1.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases", meta = (ClampMin = "0"))
    float LandingGroundOffset = 50.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases", meta = (ClampMin = "0"))
    float LandingTraceDistance = 10000.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases")
    TEnumAsByte<ECollisionChannel> LandingTraceChannel = ECC_Visibility;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF|Fly|Phases", meta = (ClampMin = "0"))
    float LandingSnapDistance = 50.f;

    // --- Input API ---------------------------------------------------------
    // Each Add*Input scales by the corresponding axis input. The component
    // smooths these every tick and forwards them to AddInputVector (linear)
    // or to AddControllerXxxInput / ControlRotation.Roll (angular).

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly|Input")
    void AddForwardInput(float Scale);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly|Input")
    void AddStrafeInput(float Scale);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly|Input")
    void AddVerticalInput(float Scale);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly|Input")
    void AddYawInput(float Scale);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly|Input")
    void AddPitchInput(float Scale);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly|Input")
    void AddRollInput(float Scale);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly")
    void Accelerate(float Amount = 1.f);

    UFUNCTION(BlueprintCallable, Category = "ACF|Fly")
    void Decelerate(float Amount = 1.f);

    /** Cancels current pending input. Real braking belongs on the FloatingPawnMovement. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Fly")
    void Brake();

    /** Cancels pending input and zeroes any velocity carried by the FloatingPawnMovement. */
    UFUNCTION(BlueprintCallable, Category = "ACF|Fly")
    void Stop();

    // --- Phase control -----------------------------------------------------

    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "ACF|Fly")
    void EnableFly(bool bEnabled);

    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "ACF|Fly|Phases")
    void TakeOff(float TargetAltitudeOverride = -1.f);

    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "ACF|Fly|Phases")
    void Land();

    UFUNCTION(Server, Reliable, WithValidation, BlueprintCallable, Category = "ACF|Fly|Phases")
    void CancelPhaseTransition();

    // --- Queries -----------------------------------------------------------

    UFUNCTION(BlueprintPure, Category = "ACF|Fly")
    FVector GetCurrentVelocity() const;

    UFUNCTION(BlueprintPure, Category = "ACF|Fly")
    float GetCurrentSpeed() const;

    virtual bool IsFlying() const override { return CurrentPhase != EACFFlyPhase::Grounded; }

    UFUNCTION(BlueprintPure, Category = "ACF|Fly|Phases")
    FORCEINLINE EACFFlyPhase GetFlyPhase() const { return CurrentPhase; }

    UFUNCTION(BlueprintPure, Category = "ACF|Fly|Phases")
    FORCEINLINE bool IsTakingOff() const { return CurrentPhase == EACFFlyPhase::TakingOff; }

    UFUNCTION(BlueprintPure, Category = "ACF|Fly|Phases")
    FORCEINLINE bool IsLanding() const { return CurrentPhase == EACFFlyPhase::Landing; }

    UFUNCTION(BlueprintPure, Category = "ACF|Fly|Phases")
    bool IsInputLocked() const;

    // --- UActorComponent / UMovementComponent ------------------------------

    virtual void TickComponent(float DeltaTime, enum ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void BeginPlay() override;
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    UPROPERTY(ReplicatedUsing = OnRep_FlyEnabled)
    bool bFlyEnabled = false;

    UPROPERTY(ReplicatedUsing = OnRep_FlyPhase)
    EACFFlyPhase CurrentPhase = EACFFlyPhase::Grounded;

    UFUNCTION()
    void OnRep_FlyEnabled();

    UFUNCTION()
    void OnRep_FlyPhase(EACFFlyPhase OldPhase);

private:
    /** Resolves and caches the FloatingPawnMovement on the owning pawn. */
    UFloatingPawnMovement* GetFloatingMovement() const;

    /** Smooths PendingLinearInput / PendingAngularInput and dispatches them to the engine. */
    void ApplySmoothedInput(float DeltaTime);

    /** Applies the smoothed roll rate to the controller's ControlRotation.Roll. */
    void ApplyRollToControlRotation(float DeltaTime);

    void SetPhase(EACFFlyPhase NewPhase);
    void TickTakeOff(float DeltaTime);
    void TickLanding(float DeltaTime);
    bool PerformGroundTrace(FHitResult& OutHit) const;
    bool IsMeshNearLandingSurface() const;
    void ClearPendingInput();

    // Per-frame requested input from the player (overwritten each frame
    // by Add*Input calls). Linear is in pawn-local space, angular is raw.
    FVector PendingLinearInput = FVector::ZeroVector;     // X=fwd, Y=right, Z=up
    FVector PendingAngularInput = FVector::ZeroVector;    // X=yaw, Y=pitch, Z=roll

    // Smoothed values driven toward the pending input each tick.
    FVector SmoothedLinearInput = FVector::ZeroVector;
    FVector SmoothedAngularInput = FVector::ZeroVector;

    // Cached weak pointer to the pawn's FloatingPawnMovement (resolved lazily).
    mutable TWeakObjectPtr<UFloatingPawnMovement> CachedFloatingMovement;

    // TakeOff/Landing state.
    float TargetTakeOffZ = 0.f;
    FVector TakeOffStartLocation = FVector::ZeroVector;
};
