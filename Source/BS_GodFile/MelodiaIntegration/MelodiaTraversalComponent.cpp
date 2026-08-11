#include "MelodiaTraversalComponent.h"

#include "Components/InputComponent.h"
#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "MelodiaInputContextSubsystem.h"
#include "MelodiaWaterAudioBridgeComponent.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterNiagaraBridgeComponent.h"
#include "MelodiaWaterUnderwaterPostProcessComponent.h"
#include "TimerManager.h"

namespace
{
	bool IsTraversalMovementAllowed(const UObject* WorldContextObject)
	{
		const UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(WorldContextObject);
		return !Input || Input->IsMovementAllowed();
	}
}

UMelodiaTraversalComponent::UMelodiaTraversalComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UMelodiaTraversalComponent::BeginPlay()
{
	Super::BeginPlay();
	OwnerCharacter = Cast<ACharacter>(GetOwner());
	if (OwnerCharacter.IsValid())
	{
		Movement = OwnerCharacter->GetCharacterMovement();
	}

	if (Movement.IsValid() && OwnerCharacter.IsValid())
	{
		SavedMaxWalkSpeed = Movement->MaxWalkSpeed;
		SavedRotationRate = Movement->RotationRate;
		bSavedOrientRotationToMovement = Movement->bOrientRotationToMovement;
		bSavedUseControllerRotationYaw = OwnerCharacter->bUseControllerRotationYaw;
		bMovementDefaultsCaptured = true;

		Movement->MaxWalkSpeed = NormalWalkSpeed;
		if (bApplyExplorationRotationTuning)
		{
			Movement->bOrientRotationToMovement = true;
			Movement->RotationRate.Yaw = ExplorationRotationRateYaw;
			OwnerCharacter->bUseControllerRotationYaw = false;
		}
	}

	GlideStamina = MaxGlideStamina;
	TimeSinceGlideStopped = GlideStaminaRegenDelay;
	SwimStamina = MaxSwimStamina;
	Breath = MaxBreath;
	TimeSinceSwimStopped = SwimStaminaRegenDelay;

	// Resolve water proximity MPC
	WaterProximityMPC = Cast<UMaterialParameterCollection>(StaticLoadObject(UMaterialParameterCollection::StaticClass(), nullptr, TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette")));
	if (!WaterProximityMPC)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaTraversalComponent: MPC_Melodia_Palette not found at /Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"));
	}

	ResolveWingPresentation();
	if (bAutoCreateWaterNiagaraBridge && OwnerCharacter.IsValid())
	{
		WaterNiagaraBridge = NewObject<UMelodiaWaterNiagaraBridgeComponent>(OwnerCharacter.Get(), TEXT("MelodiaWaterNiagaraBridge"));
		if (WaterNiagaraBridge)
		{
			OwnerCharacter->AddInstanceComponent(WaterNiagaraBridge);
			WaterNiagaraBridge->RegisterComponent();
		}
	}
	if (bAutoCreateWaterAudioBridge && OwnerCharacter.IsValid())
	{
		WaterAudioBridge = NewObject<UMelodiaWaterAudioBridgeComponent>(OwnerCharacter.Get(), TEXT("MelodiaWaterAudioBridge"));
		if (WaterAudioBridge)
		{
			OwnerCharacter->AddInstanceComponent(WaterAudioBridge);
			WaterAudioBridge->RegisterComponent();
		}
	}
	if (bAutoCreateWaterUnderwaterPostProcess && OwnerCharacter.IsValid())
	{
		WaterUnderwaterPostProcess = NewObject<UMelodiaWaterUnderwaterPostProcessComponent>(OwnerCharacter.Get(), TEXT("MelodiaWaterUnderwaterPostProcess"));
		if (WaterUnderwaterPostProcess)
		{
			OwnerCharacter->AddInstanceComponent(WaterUnderwaterPostProcess);
			WaterUnderwaterPostProcess->RegisterComponent();
		}
	}
	SetWingPresentation(false);
}

float UMelodiaTraversalComponent::GetJumpWindupNormalized() const
{
	if (!bJumpWindingUp || JumpWindupStartedAt < 0.0 || JumpWindupVisualDuration <= UE_SMALL_NUMBER)
	{
		return 0.0f;
	}

	const double CurrentTime = GetWorld() ? GetWorld()->GetTimeSeconds() : JumpWindupStartedAt;
	return FMath::Clamp(static_cast<float>((CurrentTime - JumpWindupStartedAt) / JumpWindupVisualDuration), 0.0f, 1.0f);
}

float UMelodiaTraversalComponent::GetGlideStaminaNormalized() const
{
	return MaxGlideStamina > UE_SMALL_NUMBER
		? FMath::Clamp(GlideStamina / MaxGlideStamina, 0.0f, 1.0f)
		: 0.0f;
}

float UMelodiaTraversalComponent::GetBreathNormalized() const
{
	return MaxBreath > UE_SMALL_NUMBER
		? FMath::Clamp(Breath / MaxBreath, 0.0f, 1.0f)
		: 0.0f;
}

void UMelodiaTraversalComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	bSuppressWaterPresentation = true;
	CancelTraversalState();
	StopSwim();
	StopDive();
	if (OwnerCharacter.IsValid())
	{
		if (UWorld* World = GetWorld())
		{
			if (UMelodiaWaterInteractionSubsystem* WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>())
			{
				WaterSubsystem->ClearActor(OwnerCharacter.Get());
			}
		}
	}
	RestoreMovementDefaults();
	OwnerCharacter.Reset();
	Movement.Reset();
	WingMesh = nullptr;
	WingMaterials.Reset();
	if (WaterNiagaraBridge)
	{
		WaterNiagaraBridge->DestroyComponent();
		WaterNiagaraBridge = nullptr;
	}
	if (WaterAudioBridge)
	{
		WaterAudioBridge->DestroyComponent();
		WaterAudioBridge = nullptr;
	}
	if (WaterUnderwaterPostProcess)
	{
		WaterUnderwaterPostProcess->DestroyComponent();
		WaterUnderwaterPostProcess = nullptr;
	}
	WaterProximityMPC = nullptr;
	bHasAuthoritativeWaterSurface = false;
	bWaterProximityActive = false;
	bInputBound = false;
	Super::EndPlay(EndPlayReason);
}

void UMelodiaTraversalComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	if (!OwnerCharacter.IsValid() || !Movement.IsValid())
	{
		return;
	}

	if (!IsTraversalMovementAllowed(this))
	{
		CancelTraversalState();
		return;
	}

	if (!bInputBound)
	{
		BindTraversalInput();
	}

	UpdateWaterState(DeltaTime);

	if (bAwaitingGlideTap)
	{
		if (!Movement->IsMovingOnGround())
		{
			bJumpHasLeftGround = true;
		}
		else if (bJumpHasLeftGround)
		{
			bAwaitingGlideTap = false;
			bJumpHasLeftGround = false;
		}
	}

	// Glide logic
	if (bIsGliding)
	{
		if (Movement->IsMovingOnGround())
		{
			StopGlide();
			bAwaitingGlideTap = false;
			bJumpHasLeftGround = false;
			return;
		}

		GlideStamina = FMath::Max(0.0f, GlideStamina - GlideStaminaDrainPerSecond * DeltaTime);
		if (GlideStamina <= UE_SMALL_NUMBER)
		{
			StopGlide();
			return;
		}

		FVector Velocity = Movement->Velocity;
		Velocity.Z = FMath::Max(Velocity.Z, -GlideTerminalFallSpeed);
		Movement->Velocity = Velocity;
		return;
	}

	// Not gliding - handle glide stamina regen
	if (!bIsGliding)
	{
		TimeSinceGlideStopped += DeltaTime;
		if (Movement->IsMovingOnGround() || TimeSinceGlideStopped >= GlideStaminaRegenDelay)
		{
			GlideStamina = FMath::Min(MaxGlideStamina, GlideStamina + GlideStaminaRegenPerSecond * DeltaTime);
		}
	}

	// Swimming logic
	if (bIsSwimming)
	{
		if (!Movement->IsSwimming())
		{
			StopSwim();
			return;
		}

		// Drain swim stamina
		SwimStamina = FMath::Max(0.0f, SwimStamina - SwimStaminaDrainPerSecond * DeltaTime);
		if (SwimStamina <= UE_SMALL_NUMBER)
		{
			StopSwim();
			return;
		}

		// Diving preserves swimming movement mode, so process breath inside this
		// block instead of returning before a separate dive branch.
		if (bIsDiving)
		{
			Breath = FMath::Max(0.0f, Breath - BreathDrainPerSecond * DeltaTime);
			if (Breath <= UE_SMALL_NUMBER)
			{
				StopDive(); // Auto-surface when out of breath
				return;
			}
		}
		else
		{
			Breath = FMath::Min(MaxBreath, Breath + BreathRegenPerSecond * DeltaTime);
		}

		// Cap swim speed
		FVector Velocity = Movement->Velocity;
		const float HorizontalSpeed = FMath::Sqrt(Velocity.X * Velocity.X + Velocity.Y * Velocity.Y);
		if (HorizontalSpeed > SwimSpeed)
		{
			const float Scale = SwimSpeed / HorizontalSpeed;
			Velocity.X *= Scale;
			Velocity.Y *= Scale;
			Movement->Velocity = Velocity;
		}

		const float MotionFactor = FMath::Clamp(HorizontalSpeed / FMath::Max(1.0f, SwimSpeed), 0.0f, 1.0f);
		if (MotionFactor > 0.05f)
		{
			WaterMotionEventAccumulator += DeltaTime;
			if (WaterMotionEventAccumulator >= WaterMotionEventInterval)
			{
				WaterMotionEventAccumulator = 0.0f;
				PublishWaterContact(
					EMelodiaWaterContactType::Ripple,
					FMath::Clamp(0.22f + MotionFactor * 0.58f, 0.0f, 1.0f),
					Velocity);
			}
		}
		else
		{
			WaterMotionEventAccumulator = 0.0f;
		}
		return;
	}

	// Not swimming - handle swim stamina regen
	if (!bIsSwimming)
	{
		TimeSinceSwimStopped += DeltaTime;
		if (Movement->IsMovingOnGround() || TimeSinceSwimStopped >= SwimStaminaRegenDelay)
		{
			SwimStamina = FMath::Min(MaxSwimStamina, SwimStamina + SwimStaminaRegenPerSecond * DeltaTime);
		}
	}

}

void UMelodiaTraversalComponent::BindTraversalInput()
{
	if (!OwnerCharacter.IsValid() || !OwnerCharacter->InputComponent)
	{
		return;
	}

	OwnerCharacter->InputComponent->BindAction(TEXT("MelodiaTraversalJump"), IE_Pressed, this, &UMelodiaTraversalComponent::HandleJumpPressed);
	OwnerCharacter->InputComponent->BindAction(TEXT("MelodiaTraversalJump"), IE_Released, this, &UMelodiaTraversalComponent::HandleJumpReleased);
	OwnerCharacter->InputComponent->BindAction(TEXT("MelodiaTraversalSprint"), IE_Pressed, this, &UMelodiaTraversalComponent::HandleSprintPressed);
	OwnerCharacter->InputComponent->BindAction(TEXT("MelodiaTraversalSprint"), IE_Released, this, &UMelodiaTraversalComponent::HandleSprintReleased);
	OwnerCharacter->InputComponent->BindAction(TEXT("MelodiaTraversalStrafe"), IE_Pressed, this, &UMelodiaTraversalComponent::HandleStrafePressed);
	OwnerCharacter->InputComponent->BindAction(TEXT("MelodiaTraversalDive"), IE_Pressed, this, &UMelodiaTraversalComponent::HandleDivePressed);
	bInputBound = true;
}

void UMelodiaTraversalComponent::HandleJumpPressed()
{
	if (!OwnerCharacter.IsValid() || !Movement.IsValid() || !IsTraversalMovementAllowed(this))
	{
		CancelTraversalState();
		return;
	}

	// If diving, jump = surface jump
	if (bIsDiving)
	{
		StopDive();
		StartSwim(); // Surface and start swimming
		if (Movement->IsSwimming())
		{
			FVector Velocity = Movement->Velocity;
			Velocity.Z = SurfaceJumpImpulse;
			Movement->Velocity = Velocity;
		}
		return;
	}

	// If swimming, jump = exit water or surface jump
	if (bIsSwimming)
	{
		// Check if we're near water surface
		const float CharacterZ = OwnerCharacter->GetActorLocation().Z;
		if (FMath::Abs(CharacterZ - WaterLevelZ) < 100.0f)
		{
			// Surface jump
			FVector Velocity = Movement->Velocity;
			Velocity.Z = SurfaceJumpImpulse;
			Movement->Velocity = Velocity;
			Movement->SetMovementMode(MOVE_Falling);
			StopSwim();
		}
		return;
	}

	if (bIsGliding)
	{
		StopGlide();
		return;
	}

	if (Movement->IsMovingOnGround())
	{
		BeginJumpWindup();
		return;
	}

	if (bAwaitingGlideTap)
	{
		bAwaitingGlideTap = false;
		StartGlide();
	}
}

void UMelodiaTraversalComponent::HandleJumpReleased()
{
	if (!bJumpWindingUp)
	{
		return;
	}

	if (!OwnerCharacter.IsValid() || !Movement.IsValid() || !IsTraversalMovementAllowed(this) || !Movement->IsMovingOnGround())
	{
		CancelJumpWindup();
		return;
	}

	CancelJumpWindup();
	OwnerCharacter->Jump();
	bAwaitingGlideTap = true;
	bJumpHasLeftGround = false;

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimerForNextTick(
			FTimerDelegate::CreateUObject(this, &UMelodiaTraversalComponent::FinishReleasedJump));
	}
}

void UMelodiaTraversalComponent::FinishReleasedJump()
{
	if (OwnerCharacter.IsValid())
	{
		OwnerCharacter->StopJumping();
	}
}

void UMelodiaTraversalComponent::HandleSprintPressed()
{
	bSprintInputHeld = true;
	if (IsTraversalMovementAllowed(this) && !bJumpWindingUp)
	{
		SetSprinting(true);
	}
}

void UMelodiaTraversalComponent::HandleSprintReleased()
{
	bSprintInputHeld = false;
	SetSprinting(false);
}

void UMelodiaTraversalComponent::HandleStrafePressed()
{
	if (!OwnerCharacter.IsValid() || !Movement.IsValid() || !IsTraversalMovementAllowed(this))
	{
		return;
	}

	// Never dash during jump windup, nor twice within the cooldown window.
	if (bJumpWindingUp || !Movement.IsValid())
	{
		return;
	}

	const double Now = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	if (Now < DashCooldownUntilTime)
	{
		return;
	}

	// Direction: prefer the player's current intended movement; if standing still,
	// fall back to facing so a tap still gives a read.
	FVector Direction = Movement->GetLastInputVector();
	if (Direction.IsNearlyZero())
	{
		Direction = OwnerCharacter->GetActorForwardVector();
	}
	Direction.Z = 0.0f;
	Direction = Direction.GetSafeNormal();
	if (Direction.IsNearlyZero())
	{
		Direction = OwnerCharacter->GetActorForwardVector();
		Direction.Z = 0.0f;
	}

	// Apply the impulse. In air we don't stack vertical velocity so a glide-flavored
	// dash reads as a burst of horizontal speed, not a teleport upward.
	FVector NewVelocity = Movement->Velocity;
	const FVector DashDir = Direction * DashImpulse;
	NewVelocity.X = DashDir.X;
	NewVelocity.Y = DashDir.Y;
	Movement->Velocity = NewVelocity;

	bIsDashing = true;
	DashCooldownUntilTime = Now + DashCooldownSeconds;

	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(DashPersistTimer, this,
			&UMelodiaTraversalComponent::FinishDash, DashPersistSeconds, false);
	}
}

void UMelodiaTraversalComponent::HandleDivePressed()
{
	if (!OwnerCharacter.IsValid() || !Movement.IsValid() || !IsTraversalMovementAllowed(this))
	{
		return;
	}

	// If already diving, surface
	if (bIsDiving)
	{
		StopDive();
		StartSwim();
		return;
	}

	// If swimming, start dive
	if (bIsSwimming)
	{
		StartDive();
		return;
	}

	// If gliding, cancel glide and try to enter water
	if (bIsGliding)
	{
		StopGlide();
	}

	// If on ground or falling near water, try to enter water
	if (Movement->IsMovingOnGround() || Movement->IsFalling())
	{
		// The actual water entry is handled by UpdateWaterState when overlapping water volume
		// This just primes the dive if we're already in water
		if (Movement->IsSwimming())
		{
			StartDive();
		}
	}
}

void UMelodiaTraversalComponent::FinishDash()
{
	bIsDashing = false;

	// Dash closed the window; velocity on X/Y already settled by friction.
	// No restore needed because we never touched gravity or walk speed —
	// only the instantaneous velocity impulse.
}

void UMelodiaTraversalComponent::BeginJumpWindup()
{
	if (bJumpWindingUp || !Movement.IsValid())
	{
		return;
	}

	bJumpWindingUp = true;
	JumpWindupStartedAt = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0;
	SetSprinting(false);
	Movement->StopMovementImmediately();
	Movement->MaxWalkSpeed = 0.0f;
}

void UMelodiaTraversalComponent::CancelJumpWindup()
{
	if (!bJumpWindingUp)
	{
		return;
	}

	bJumpWindingUp = false;
	JumpWindupStartedAt = -1.0;
	SetSprinting(bSprintInputHeld && IsTraversalMovementAllowed(this));
	ApplyCurrentMovementSpeed();
}

void UMelodiaTraversalComponent::SetSprinting(bool bShouldSprint)
{
	const bool bNewSprinting = bShouldSprint && !bJumpWindingUp && IsTraversalMovementAllowed(this);
	if (bIsSprinting == bNewSprinting)
	{
		ApplyCurrentMovementSpeed();
		return;
	}

	bIsSprinting = bNewSprinting;
	ApplyCurrentMovementSpeed();
}

void UMelodiaTraversalComponent::ApplyCurrentMovementSpeed()
{
	if (!Movement.IsValid() || bJumpWindingUp)
	{
		return;
	}
	Movement->MaxWalkSpeed = bIsSprinting ? SprintSpeed : NormalWalkSpeed;
}

void UMelodiaTraversalComponent::CancelTraversalState()
{
	StopGlide();
	StopSwim();
	StopDive();
	bSprintInputHeld = false;
	SetSprinting(false);
	CancelJumpWindup();
	bAwaitingGlideTap = false;
	bJumpHasLeftGround = false;
	bIsDashing = false;
	DashPersistTimer.Invalidate();
	if (OwnerCharacter.IsValid())
	{
		OwnerCharacter->StopJumping();
	}
}

void UMelodiaTraversalComponent::StartGlide()
{
	if (bIsGliding || !Movement.IsValid() || !OwnerCharacter.IsValid() || GlideStamina < MinimumGlideStartStamina || Movement->IsMovingOnGround())
	{
		return;
	}

	SavedGravityScale = Movement->GravityScale;
	SavedAirControl = Movement->AirControl;
	Movement->GravityScale = GlideGravityScale;
	Movement->AirControl = GlideAirControl;

	FVector Velocity = Movement->Velocity;
	Velocity.Z = FMath::Max(Velocity.Z, GlideActivationLiftSpeed);
	const FVector FacingDirection = OwnerCharacter->GetActorForwardVector().GetSafeNormal2D();
	Velocity += FacingDirection * GlideActivationForwardBoost;
	Movement->Velocity = Velocity;

	TimeSinceGlideStopped = 0.0f;
	bIsGliding = true;
	SetWingPresentation(true);
	OnGlideStateChanged.Broadcast(true);
}

void UMelodiaTraversalComponent::StopGlide()
{
	if (!bIsGliding)
	{
		SetWingPresentation(false);
		return;
	}

	if (Movement.IsValid())
	{
		Movement->GravityScale = SavedGravityScale;
		Movement->AirControl = SavedAirControl;
	}
	TimeSinceGlideStopped = 0.0f;
	bIsGliding = false;
	SetWingPresentation(false);
	OnGlideStateChanged.Broadcast(false);
}

void UMelodiaTraversalComponent::StartDash()
{
	// Not used directly - handled in HandleStrafePressed
}

void UMelodiaTraversalComponent::StartSwim()
{
	if (bIsSwimming || !Movement.IsValid() || !OwnerCharacter.IsValid() || SwimStamina < 1.0f)
	{
		return;
	}

	if (!Movement->IsSwimming())
	{
		// Try to enter swimming mode
		Movement->SetMovementMode(MOVE_Swimming);
		if (!Movement->IsSwimming())
		{
			return; // Failed to enter swimming
		}
	}

	// Configure swimming movement
	Movement->MaxSwimSpeed = SwimSpeed;
	Movement->Buoyancy = 1.0f;

	SwimStamina = MaxSwimStamina;
	Breath = MaxBreath;
	TimeSinceSwimStopped = 0.0f;
	WaterMotionEventAccumulator = 0.0f;
	bIsSwimming = true;
	OnSwimStateChanged.Broadcast(true);

	// Update water level Z for surface detection
	if (OwnerCharacter.IsValid() && !bHasAuthoritativeWaterSurface)
	{
		WaterLevelZ = OwnerCharacter->GetActorLocation().Z;
	}

	PublishWaterContact(EMelodiaWaterContactType::SurfaceEntry, 0.8f, Movement->Velocity);
	PublishWaterContact(EMelodiaWaterContactType::SwimStarted, 0.55f, Movement->Velocity);
}

void UMelodiaTraversalComponent::StopSwim()
{
	if (!bIsSwimming)
	{
		return;
	}

	if (Movement.IsValid())
	{
		Movement->SetMovementMode(MOVE_Walking);
	}
	bIsSwimming = false;
	TimeSinceSwimStopped = 0.0f;
	WaterMotionEventAccumulator = 0.0f;
	OnSwimStateChanged.Broadcast(false);
	PublishWaterContact(EMelodiaWaterContactType::SurfaceExit, 0.65f, Movement.IsValid() ? Movement->Velocity : FVector::ZeroVector);
	PublishWaterContact(EMelodiaWaterContactType::SwimStopped, 0.35f, Movement.IsValid() ? Movement->Velocity : FVector::ZeroVector);
}

void UMelodiaTraversalComponent::StartDive()
{
	if (bIsDiving || !Movement.IsValid() || !OwnerCharacter.IsValid() || !bIsSwimming || Breath < 1.0f)
	{
		return;
	}

	// Apply dive impulse downward
	FVector Velocity = Movement->Velocity;
	Velocity.Z = -DiveImpulse;
	Movement->Velocity = Velocity;

	// Configure diving movement
	Movement->MaxSwimSpeed = SwimSpeed;
	Movement->Buoyancy = 0.1f; // Slight buoyancy to prevent sinking forever

	bIsDiving = true;
	OnDiveStateChanged.Broadcast(true);
	PublishWaterContact(EMelodiaWaterContactType::DiveStarted, 0.8f, Movement->Velocity);
}

void UMelodiaTraversalComponent::StopDive()
{
	if (!bIsDiving)
	{
		return;
	}

	if (Movement.IsValid())
	{
		Movement->Buoyancy = 1.0f;
	}
	bIsDiving = false;
	OnDiveStateChanged.Broadcast(false);
	PublishWaterContact(EMelodiaWaterContactType::DiveStopped, 0.5f, Movement.IsValid() ? Movement->Velocity : FVector::ZeroVector);

	// If still in water, return to swimming
	if (Movement.IsValid() && Movement->IsSwimming())
	{
		// Already swimming, just stay in swimming mode
	}
}

void UMelodiaTraversalComponent::PublishWaterContact(EMelodiaWaterContactType EventType, float Intensity, const FVector& ImpulseVelocity)
{
	if (bSuppressWaterPresentation || !OwnerCharacter.IsValid())
	{
		return;
	}

	FMelodiaWaterContactEvent Event;
	Event.EventType = EventType;
	Event.SourceActor = OwnerCharacter.Get();
	Event.ContactLocation = OwnerCharacter->GetActorLocation();
	Event.ImpactVelocity = ImpulseVelocity;
	Event.ImpulseVector = ImpulseVelocity;
	Event.Intensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
	Event.Radius = FMath::Lerp(18.0f, 90.0f, Event.Intensity);
	Event.Duration = FMath::Lerp(0.18f, 0.9f, Event.Intensity);
	Event.EffectProfileId = TEXT("Melusina_Default");
	Event.AudioProfileId = EventType == EMelodiaWaterContactType::DiveStarted
		? FName(TEXT("Water_Underwater_Bubble"))
		: FName(TEXT("Water_Surface_Movement"));

	// This fallback is intentionally marked non-authoritative. A native Water
	// Body sample, when available, replaces it without changing any consumers.
	Event.Sample.bUnderwater = bIsDiving;
	Event.Sample.SurfaceLocation = FVector(Event.ContactLocation.X, Event.ContactLocation.Y, WaterLevelZ);
	Event.Sample.SurfaceNormal = FVector::UpVector;
	Event.Sample.DistanceToSurface = Event.ContactLocation.Z - WaterLevelZ;
	Event.Sample.Immersion = bIsDiving ? 1.0f : 0.35f;

	if (UWorld* World = GetWorld())
	{
		if (UMelodiaWaterInteractionSubsystem* WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>())
		{
			FMelodiaWaterSample LatestSample;
			if (WaterSubsystem->GetLatestSample(OwnerCharacter.Get(), LatestSample))
			{
				Event.Sample = LatestSample;
			}
			WaterSubsystem->PublishContact(Event);
		}
	}

	OnWaterContactEvent.Broadcast(Event);
}

void UMelodiaTraversalComponent::UpdateWaterState(float DeltaTime)
{
	if (!OwnerCharacter.IsValid() || !Movement.IsValid())
	{
		return;
	}

	FMelodiaWaterSample WaterSample;
	bool bHasWaterSample = false;
	if (UWorld* World = GetWorld())
	{
		if (UMelodiaWaterInteractionSubsystem* WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>())
		{
			bHasWaterSample = WaterSubsystem->QueryWaterAtLocationForActor(OwnerCharacter.Get(), OwnerCharacter->GetActorLocation(), WaterSample);
			if (bHasWaterSample)
			{
				WaterSubsystem->SubmitSample(OwnerCharacter.Get(), WaterSample);
			}
		}
	}

	bHasAuthoritativeWaterSurface = bHasWaterSample && WaterSample.bSurfaceValid;
	if (bHasAuthoritativeWaterSurface)
	{
		WaterLevelZ = WaterSample.SurfaceLocation.Z;
	}

	// Prefer the native query. Movement mode remains the fallback during map
	// startup or on legacy volumes that have not yet been migrated.
	const bool bInWater = bHasWaterSample ? WaterSample.bUnderwater : Movement->IsSwimming();

	// Auto-enter swimming when falling into water
	if (!bIsSwimming && !bIsGliding && bInWater)
	{
		// Check if we have enough stamina to start swimming
		if (SwimStamina >= 1.0f)
		{
			StartSwim();
		}
		return;
	}

	// Auto-exit swimming when leaving water
	if (bIsSwimming && !bInWater)
	{
		StopSwim();
		StopDive();
		return;
	}

	// Update water proximity for event reactivity whether or not the legacy MPC
	// asset is present. The event bus is the runtime authority; the MPC is only
	// one optional presentation consumer.
	if (OwnerCharacter.IsValid())
	{
		const float CharacterZ = OwnerCharacter->GetActorLocation().Z;
		const float DistanceToWater = bHasWaterSample
			? FMath::Abs(WaterSample.DistanceToSurface)
			: FMath::Abs(CharacterZ - WaterLevelZ);
		const float ProximityRadius = 1000.0f; // 10m proximity radius
		const float Proximity = FMath::Clamp(1.0f - (DistanceToWater / ProximityRadius), 0.0f, 1.0f);

		if (WaterProximityMPC)
		{
			// Update MPC parameters for water reactivity when the legacy collection
			// is available; missing MPC content must not suppress runtime events.
			UMaterialParameterCollectionInstance* WaterProximityMPCInstance = GetWorld()->GetParameterCollectionInstance(WaterProximityMPC);
			if (WaterProximityMPCInstance)
			{
				WaterProximityMPCInstance->SetScalarParameterValue(FName("PlayerProximity"), Proximity);
				WaterProximityMPCInstance->SetScalarParameterValue(FName("ProximityGlow"), Proximity * 0.5f);
				WaterProximityMPCInstance->SetScalarParameterValue(FName("UnderwaterDepth"), bIsDiving ? 1.0f : 0.0f);
				WaterProximityMPCInstance->SetScalarParameterValue(FName("WaterLevelZ"), WaterLevelZ);
			}
		}

		OnWaterProximityChanged.Broadcast(Proximity);

		if (!bWaterProximityActive && Proximity >= WaterProximityEnterThreshold)
		{
			bWaterProximityActive = true;
			PublishWaterContact(EMelodiaWaterContactType::ProximityEntered, Proximity);
		}
		else if (bWaterProximityActive && Proximity <= WaterProximityExitThreshold)
		{
			bWaterProximityActive = false;
			PublishWaterContact(EMelodiaWaterContactType::ProximityExited, Proximity);
		}
	}
}

void UMelodiaTraversalComponent::ResolveWingPresentation()
{
	WingMesh = nullptr;
	WingMaterials.Reset();
	if (!GetOwner() || WingComponentTag.IsNone())
	{
		return;
	}

	TArray<UMeshComponent*> MeshComponents;
	GetOwner()->GetComponents<UMeshComponent>(MeshComponents);
	for (UMeshComponent* Candidate : MeshComponents)
	{
		if (IsValid(Candidate) && Candidate->ComponentHasTag(WingComponentTag))
		{
			WingMesh = Candidate;
			break;
		}
	}

	if (!WingMesh)
	{
		return;
	}

	for (int32 MaterialIndex = 0; MaterialIndex < WingMesh->GetNumMaterials(); ++MaterialIndex)
	{
		if (UMaterialInstanceDynamic* DynamicMaterial = WingMesh->CreateAndSetMaterialInstanceDynamic(MaterialIndex))
		{
			WingMaterials.Add(DynamicMaterial);
		}
	}
}

void UMelodiaTraversalComponent::SetWingPresentation(bool bVisible)
{
	const float Opacity = bVisible ? 1.0f : 0.0f;
	for (UMaterialInstanceDynamic* WingMaterial : WingMaterials)
	{
		if (IsValid(WingMaterial) && !WingOpacityParameter.IsNone())
		{
			WingMaterial->SetScalarParameterValue(WingOpacityParameter, Opacity);
		}
	}

	if (WingMesh && bHideWingMeshWhenNotGliding)
	{
		WingMesh->SetVisibility(bVisible, true);
		WingMesh->SetHiddenInGame(!bVisible, true);
	}
}

void UMelodiaTraversalComponent::RestoreMovementDefaults()
{
	if (!bMovementDefaultsCaptured || !Movement.IsValid() || !OwnerCharacter.IsValid())
	{
		return;
	}

	Movement->MaxWalkSpeed = SavedMaxWalkSpeed;
	Movement->RotationRate = SavedRotationRate;
	Movement->bOrientRotationToMovement = bSavedOrientRotationToMovement;
	OwnerCharacter->bUseControllerRotationYaw = bSavedUseControllerRotationYaw;
	bMovementDefaultsCaptured = false;
}
