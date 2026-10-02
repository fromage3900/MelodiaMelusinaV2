// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFFlyComponent.h"

#include "CollisionQueryParams.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/HitResult.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/Pawn.h"
#include "Logging.h"
#include "Net/UnrealNetwork.h"

UACFFlyComponent::UACFFlyComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PrePhysics;

    SetIsReplicatedByDefault(true);

    bAutoActivate = true;
    bAutoRegisterUpdatedComponent = true;
    bAutoRegisterPhysicsVolumeUpdates = false;
}

void UACFFlyComponent::BeginPlay()
{
    Super::BeginPlay();
}

void UACFFlyComponent::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);

    DOREPLIFETIME(UACFFlyComponent, bFlyEnabled);
    DOREPLIFETIME(UACFFlyComponent, CurrentPhase);
}

// =====================================================================
//  Lookup of the pawn's FloatingPawnMovement
// =====================================================================

UFloatingPawnMovement* UACFFlyComponent::GetFloatingMovement() const
{
    if (CachedFloatingMovement.IsValid()) {
        return CachedFloatingMovement.Get();
    }

    if (PawnOwner) {
        UFloatingPawnMovement* Found = PawnOwner->FindComponentByClass<UFloatingPawnMovement>();
        CachedFloatingMovement = Found;
        return Found;
    }
    return nullptr;
}

// =====================================================================
//  Input collection (called by Blueprint / input bindings)
// =====================================================================

void UACFFlyComponent::ClearPendingInput()
{
    PendingLinearInput = FVector::ZeroVector;
    PendingAngularInput = FVector::ZeroVector;
}

void UACFFlyComponent::AddForwardInput(float Scale)
{
    PendingLinearInput.X = FMath::Clamp(PendingLinearInput.X + Scale, -1.f, 1.f);
}

void UACFFlyComponent::AddStrafeInput(float Scale)
{
    PendingLinearInput.Y = FMath::Clamp(PendingLinearInput.Y + Scale, -1.f, 1.f);
}

void UACFFlyComponent::AddVerticalInput(float Scale)
{
    PendingLinearInput.Z = FMath::Clamp(PendingLinearInput.Z + Scale, -1.f, 1.f);
}

void UACFFlyComponent::AddYawInput(float Scale)
{
    PendingAngularInput.X = FMath::Clamp(PendingAngularInput.X + Scale, -1.f, 1.f);
}

void UACFFlyComponent::AddPitchInput(float Scale)
{
    PendingAngularInput.Y = FMath::Clamp(PendingAngularInput.Y + Scale, -1.f, 1.f);
}

void UACFFlyComponent::AddRollInput(float Scale)
{
    PendingAngularInput.Z = FMath::Clamp(PendingAngularInput.Z + Scale, -1.f, 1.f);
}

void UACFFlyComponent::Accelerate(float Amount)
{
    AddForwardInput(Amount);
}

void UACFFlyComponent::Decelerate(float Amount)
{
    AddForwardInput(-Amount);
}

void UACFFlyComponent::Brake()
{
    // We no longer own velocity. "Brake" just means: stop pushing.
    // The FloatingPawnMovement will decelerate through its own Deceleration.
    ClearPendingInput();
    SmoothedLinearInput = FVector::ZeroVector;
    SmoothedAngularInput = FVector::ZeroVector;
}

void UACFFlyComponent::Stop()
{
    ClearPendingInput();
    SmoothedLinearInput = FVector::ZeroVector;
    SmoothedAngularInput = FVector::ZeroVector;

    if (UFloatingPawnMovement* Move = GetFloatingMovement()) {
        Move->Velocity = FVector::ZeroVector;
        Move->StopMovementImmediately();
    }
}

// =====================================================================
//  Phase control (server authoritative)
// =====================================================================

void UACFFlyComponent::EnableFly_Implementation(bool bEnabled)
{
    SetPhase(bEnabled ? EACFFlyPhase::Flying : EACFFlyPhase::Grounded);
}

bool UACFFlyComponent::EnableFly_Validate(bool /*bEnabled*/)
{
    return true;
}

void UACFFlyComponent::OnRep_FlyEnabled()
{
    OnFlyStateChanged.Broadcast(bFlyEnabled);
}

void UACFFlyComponent::TakeOff_Implementation(float TargetAltitudeOverride)
{
    if (CurrentPhase != EACFFlyPhase::Grounded) {
        return;
    }

    if (UpdatedComponent) {
        TakeOffStartLocation = UpdatedComponent->GetComponentLocation();
    } else if (PawnOwner) {
        TakeOffStartLocation = PawnOwner->GetActorLocation();
    }

    const float Altitude = (TargetAltitudeOverride > 0.f) ? TargetAltitudeOverride : TakeOffAltitude;
    TargetTakeOffZ = TakeOffStartLocation.Z + Altitude;

    SetPhase(EACFFlyPhase::TakingOff);
}

bool UACFFlyComponent::TakeOff_Validate(float /*TargetAltitudeOverride*/)
{
    return true;
}

void UACFFlyComponent::Land_Implementation()
{
    if (CurrentPhase != EACFFlyPhase::Flying) {
        return;
    }

    SetPhase(EACFFlyPhase::Landing);
}

bool UACFFlyComponent::Land_Validate()
{
    return true;
}

void UACFFlyComponent::CancelPhaseTransition_Implementation()
{
    switch (CurrentPhase) {
    case EACFFlyPhase::TakingOff:
        SetPhase(EACFFlyPhase::Grounded);
        break;
    case EACFFlyPhase::Landing:
        SetPhase(EACFFlyPhase::Flying);
        break;
    default:
        break;
    }
}

bool UACFFlyComponent::CancelPhaseTransition_Validate()
{
    return true;
}

void UACFFlyComponent::OnRep_FlyPhase(EACFFlyPhase OldPhase)
{
    OnFlyPhaseChanged.Broadcast(CurrentPhase);

    if (OldPhase == EACFFlyPhase::TakingOff && CurrentPhase == EACFFlyPhase::Flying) {
        OnTakeOffCompleted.Broadcast();
    } else if (OldPhase == EACFFlyPhase::Landing && CurrentPhase == EACFFlyPhase::Grounded) {
        OnLandingCompleted.Broadcast();
    }
}

bool UACFFlyComponent::IsInputLocked() const
{
    switch (CurrentPhase) {
    case EACFFlyPhase::Grounded:
        return true;
    case EACFFlyPhase::TakingOff:
        return bLockInputDuringTakeOff;
    case EACFFlyPhase::Landing:
        return bLockInputDuringLanding;
    case EACFFlyPhase::Flying:
    default:
        return false;
    }
}

void UACFFlyComponent::SetPhase(EACFFlyPhase NewPhase)
{
    if (CurrentPhase == NewPhase) {
        return;
    }

    CurrentPhase = NewPhase;

    const bool bNewEnabled = (NewPhase != EACFFlyPhase::Grounded);
    if (bFlyEnabled != bNewEnabled) {
        bFlyEnabled = bNewEnabled;
        OnFlyStateChanged.Broadcast(bFlyEnabled);
    }

    // On any non-Flying phase we want a clean slate: no carried input,
    // no carried velocity. Velocity now lives on the FloatingPawnMovement.
    switch (NewPhase) {
    case EACFFlyPhase::Grounded:
    case EACFFlyPhase::TakingOff:
    case EACFFlyPhase::Landing:
        ClearPendingInput();
        SmoothedLinearInput = FVector::ZeroVector;
        SmoothedAngularInput = FVector::ZeroVector;
        if (UFloatingPawnMovement* Move = GetFloatingMovement()) {
            Move->Velocity = FVector::ZeroVector;
        }
        break;
    case EACFFlyPhase::Flying:
    default:
        break;
    }

    OnFlyPhaseChanged.Broadcast(CurrentPhase);
}

// =====================================================================
//  Queries
// =====================================================================

FVector UACFFlyComponent::GetCurrentVelocity() const
{
    if (UFloatingPawnMovement* Move = GetFloatingMovement()) {
        return Move->Velocity;
    }
    return FVector::ZeroVector;
}

float UACFFlyComponent::GetCurrentSpeed() const
{
    return GetCurrentVelocity().Size();
}

// =====================================================================
//  Tick: smooth input -> AddInputVector + controller rotation inputs
// =====================================================================

void UACFFlyComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    if (!PawnOwner || !UpdatedComponent) {
        return;
    }

    // The phases drive themselves; they may also want to consume / ignore input.
    switch (CurrentPhase) {
    case EACFFlyPhase::TakingOff:
        TickTakeOff(DeltaTime);
        break;
    case EACFFlyPhase::Landing:
        TickLanding(DeltaTime);
        break;
    case EACFFlyPhase::Flying:
        ApplySmoothedInput(DeltaTime);
        break;
    case EACFFlyPhase::Grounded:
    default:
        // While grounded we still bleed the smoothed values toward zero so the
        // ship doesn't keep yawing when re-enabled.
        SmoothedLinearInput = FMath::VInterpTo(SmoothedLinearInput, FVector::ZeroVector, DeltaTime, LinearInputSmoothing);
        SmoothedAngularInput = FMath::VInterpTo(SmoothedAngularInput, FVector::ZeroVector, DeltaTime, AngularInputSmoothing);
        break;
    }

    // Pending input is consumed once per tick regardless of phase.
    ClearPendingInput();
}

void UACFFlyComponent::ApplySmoothedInput(float DeltaTime)
{
    // While input is locked (e.g. during take-off if bLockInputDuringTakeOff),
    // we let smoothed values fall to zero rather than honor pending input.
    const bool bLocked = IsInputLocked();
    const FVector LinearTarget = bLocked ? FVector::ZeroVector : PendingLinearInput;
    const FVector AngularTarget = bLocked ? FVector::ZeroVector : PendingAngularInput;

    SmoothedLinearInput = FMath::VInterpTo(SmoothedLinearInput, LinearTarget, DeltaTime, LinearInputSmoothing);
    SmoothedAngularInput = FMath::VInterpTo(SmoothedAngularInput, AngularTarget, DeltaTime, AngularInputSmoothing);

    // ---- Linear: forward to FloatingPawnMovement via AddInputVector --------
    // Standard Unreal axis convention: Forward = +X (ActorForwardVector),
    // Right = +Y (ActorRightVector), Up = +Z (world up to keep vertical input
    // independent of pitch/roll). If the mesh visually points sideways, fix
    // it by rotating the mesh under the root, not by swapping axes here.
    if (!SmoothedLinearInput.IsNearlyZero()) {
        const FVector Forward = PawnOwner->GetActorForwardVector();
        const FVector Right = PawnOwner->GetActorRightVector();
        const FVector Up = FVector::UpVector;

        FVector World = Forward * SmoothedLinearInput.X
                      + Right * SmoothedLinearInput.Y
                      + Up * SmoothedLinearInput.Z;

        // Force=true: feed each frame even if magnitude < 1, so smoothing is preserved.
        AddInputVector(World, /*bForce=*/true);
    }

    // ---- Angular: forward to controller -----------------------------------
    // AddControllerYawInput / AddControllerPitchInput already accumulate into
    // ControlRotation. With bUseControllerRotationYaw/Pitch=true on the pawn,
    // the mesh follows automatically.
    if (!FMath::IsNearlyZero(SmoothedAngularInput.X)) {
        PawnOwner->AddControllerYawInput(SmoothedAngularInput.X * AngularSensitivity);
    }
    if (!FMath::IsNearlyZero(SmoothedAngularInput.Y)) {
        PawnOwner->AddControllerPitchInput(SmoothedAngularInput.Y * AngularSensitivity);
    }

    // Roll: APawn has no AddControllerRollInput. We write straight into the
    // controller's ControlRotation.Roll. For this to actually rotate the mesh,
    // the pawn must have bUseControllerRotationRoll = true.
    ApplyRollToControlRotation(DeltaTime);
}

void UACFFlyComponent::ApplyRollToControlRotation(float DeltaTime)
{
    if (FMath::IsNearlyZero(SmoothedAngularInput.Z)) {
        return;
    }
    AController* C = PawnOwner ? PawnOwner->GetController() : nullptr;
    if (!C) {
        return;
    }

    // AddControllerYaw/PitchInput are scaled by InputYawScale_DEPRECATED /
    // InputPitchScale_DEPRECATED and by frame time inside PlayerInput. Here we
    // just apply a degree delta per second so the feel is predictable and not
    // tied to the deprecated input scales. AngularSensitivity remains the
    // single knob the user can tune.
    constexpr float RollDegPerSecAtFullStick = 90.f;

    FRotator Ctrl = C->GetControlRotation();
    Ctrl.Roll += SmoothedAngularInput.Z * AngularSensitivity * RollDegPerSecAtFullStick * DeltaTime;
    Ctrl.Roll = FRotator::NormalizeAxis(Ctrl.Roll);
    C->SetControlRotation(Ctrl);
}

// =====================================================================
//  TakeOff / Landing
// =====================================================================

void UACFFlyComponent::TickTakeOff(float DeltaTime)
{
    if (!UpdatedComponent) {
        return;
    }

    const float CurrentZ = UpdatedComponent->GetComponentLocation().Z;
    const float DistRemaining = TargetTakeOffZ - CurrentZ;

    if (DistRemaining <= KINDA_SMALL_NUMBER) {
        if (PawnOwner && PawnOwner->HasAuthority()) {
            SetPhase(EACFFlyPhase::Flying);
        }
        return;
    }

    // Push upward through the FloatingPawnMovement. The amount of upward input
    // is capped so we don't overshoot in a single frame.
    const float MaxStep = TakeOffVerticalSpeed * DeltaTime;
    const float StepRatio = (MaxStep > KINDA_SMALL_NUMBER)
        ? FMath::Clamp(DistRemaining / FMath::Max(MaxStep, 1.f), 0.f, 1.f)
        : 1.f;

    AddInputVector(FVector::UpVector * StepRatio, /*bForce=*/true);

    // While taking off we explicitly clamp the FloatingPawnMovement's max
    // speed contribution by also caching the smoothed input at zero, so any
    // residual horizontal drift dies off quickly.
    SmoothedLinearInput = FMath::VInterpTo(SmoothedLinearInput, FVector::ZeroVector, DeltaTime, LinearInputSmoothing);
    SmoothedAngularInput = FMath::VInterpTo(SmoothedAngularInput, FVector::ZeroVector, DeltaTime, AngularInputSmoothing);
}

void UACFFlyComponent::TickLanding(float DeltaTime)
{
    if (!UpdatedComponent) {
        return;
    }

    // Optional: level out roll/pitch before descending.
    if (bLevelOutBeforeLanding) {
        const FRotator CurrentRot = UpdatedComponent->GetComponentRotation();
        const bool bAlreadyLevel =
            FMath::Abs(CurrentRot.Pitch) <= LandingLevelTolerance &&
            FMath::Abs(CurrentRot.Roll) <= LandingLevelTolerance;

        if (!bAlreadyLevel) {
            // Drive the controller's pitch/roll toward zero through the
            // control-rotation pipeline (same channel we use for normal flight).
            AController* C = PawnOwner ? PawnOwner->GetController() : nullptr;
            if (C) {
                FRotator Ctrl = C->GetControlRotation();
                const FRotator Target(0.f, Ctrl.Yaw, 0.f);
                const FRotator Next = FMath::RInterpTo(Ctrl, Target, DeltaTime, LandingLevelInterpSpeed);
                C->SetControlRotation(Next);
            }
            return; // wait until we are level before descending
        }
    }

    // Snap-to-ground when we're already very close.
    if (IsMeshNearLandingSurface()) {
        if (UFloatingPawnMovement* Move = GetFloatingMovement()) {
            Move->Velocity = FVector::ZeroVector;
        }
        if (PawnOwner && PawnOwner->HasAuthority()) {
            SetPhase(EACFFlyPhase::Grounded);
        }
        return;
    }

    // Test if we have ground at all and how far it is.
    FHitResult Hit;
    const bool bHit = PerformGroundTrace(Hit);
    if (bHit) {
        const float StopZ = Hit.ImpactPoint.Z + LandingGroundOffset;
        const float DistRemaining = UpdatedComponent->GetComponentLocation().Z - StopZ;

        if (DistRemaining <= KINDA_SMALL_NUMBER) {
            if (UFloatingPawnMovement* Move = GetFloatingMovement()) {
                Move->Velocity = FVector::ZeroVector;
            }
            if (PawnOwner && PawnOwner->HasAuthority()) {
                SetPhase(EACFFlyPhase::Grounded);
            }
            return;
        }

        // Push downward via input vector. Magnitude scales with how much
        // distance remains so we slow down naturally as we approach.
        const float MaxStep = LandingVerticalSpeed * DeltaTime;
        const float StepRatio = (MaxStep > KINDA_SMALL_NUMBER)
            ? FMath::Clamp(DistRemaining / FMath::Max(MaxStep, 1.f), 0.f, 1.f)
            : 1.f;

        AddInputVector(FVector::DownVector * StepRatio, /*bForce=*/true);
    } else {
        // No ground in range: just descend at the configured speed.
        AddInputVector(FVector::DownVector, /*bForce=*/true);
    }

    // Bleed any residual horizontal/angular input.
    SmoothedLinearInput = FMath::VInterpTo(SmoothedLinearInput, FVector::ZeroVector, DeltaTime, LinearInputSmoothing);
    SmoothedAngularInput = FMath::VInterpTo(SmoothedAngularInput, FVector::ZeroVector, DeltaTime, AngularInputSmoothing);
}

// =====================================================================
//  Ground sensing
// =====================================================================

bool UACFFlyComponent::IsMeshNearLandingSurface() const
{
    if (LandingSnapDistance <= 0.f || !UpdatedPrimitive) {
        return false;
    }

    UWorld* World = GetWorld();
    if (!World) {
        return false;
    }

    const FVector Start = UpdatedPrimitive->GetComponentLocation();
    const FVector End = Start - FVector(0.f, 0.f, LandingSnapDistance);

    FCollisionQueryParams Params(SCENE_QUERY_STAT(ACFFlyLandingProximity), false);
    if (PawnOwner) {
        Params.AddIgnoredActor(PawnOwner);
    } else if (AActor* Owner = GetOwner()) {
        Params.AddIgnoredActor(Owner);
    }

    const FCollisionShape Shape = UpdatedPrimitive->GetCollisionShape();
    const FQuat ShapeRot = UpdatedPrimitive->GetComponentQuat();

    FHitResult Hit;
    return World->SweepSingleByChannel(Hit, Start, End, ShapeRot, LandingTraceChannel, Shape, Params);
}

bool UACFFlyComponent::PerformGroundTrace(FHitResult& OutHit) const
{
    if (!UpdatedComponent) {
        return false;
    }
    UWorld* World = GetWorld();
    if (!World) {
        return false;
    }

    const FVector Start = UpdatedComponent->GetComponentLocation();
    const FVector End = Start - FVector(0.f, 0.f, FMath::Max(0.f, LandingTraceDistance));

    FCollisionQueryParams Params(SCENE_QUERY_STAT(ACFFlyLanding), false);
    if (PawnOwner) {
        Params.AddIgnoredActor(PawnOwner);
    } else if (AActor* Owner = GetOwner()) {
        Params.AddIgnoredActor(Owner);
    }

    return World->LineTraceSingleByChannel(OutHit, Start, End, LandingTraceChannel, Params);
}