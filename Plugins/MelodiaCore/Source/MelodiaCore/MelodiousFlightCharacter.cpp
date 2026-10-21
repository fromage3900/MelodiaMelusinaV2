#include "MelodiousFlightCharacter.h"

#include "Camera/CameraComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/SkeletalMesh.h"
#include "InputModifiers.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "EngineUtils.h"
#include "MelodiaPartySubsystem.h"
#include "SirPerchPoint.h"

AMelodiousFlightCharacter::AMelodiousFlightCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	UCharacterMovementComponent* CMC = GetCharacterMovement();
	CMC->DefaultLandMovementMode = MOVE_Flying;
	CMC->MaxFlySpeed = CruiseSpeed;
	CMC->BrakingDecelerationFlying = 1200.0f;
	CMC->bOrientRotationToMovement = true;
	CMC->RotationRate = FRotator(0.0f, 360.0f, 0.0f);
	bUseControllerRotationYaw = false;

	// Mesh + AnimBP are assigned in the BP child (BP_SirMelodious_Flight)
	// so his import/retarget work can iterate without touching C++.

	// CameraBoom/FollowCamera are created by AMelodiaCharacterBase; tune the
	// flight framing here. H-4: a 520-unit arm made the cockatoo read as a
	// speck, so the arm is pulled in and the pitch flattened.
	CameraBoom->TargetArmLength = 300.0f;
	CameraBoom->SetRelativeRotation(FRotator(-8.0f, 0.0f, 0.0f));
}

void AMelodiousFlightCharacter::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->SetMovementMode(MOVE_Flying);

	// CruiseSpeed is authored on the BP child, so the fly speed has to be
	// applied here rather than in the constructor, which runs before the
	// Blueprint defaults are applied.
	GetCharacterMovement()->MaxFlySpeed = CruiseSpeed;

	if (UMelodiaPartySubsystem* Party = UMelodiaPartySubsystem::Get(this))
	{
		Party->RegisterPawn(this, 1);
	}
}

void AMelodiousFlightCharacter::CreateInputMappingContext()
{
	if (FlightMappingContext)
	{
		return;
	}

	FlightMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_MelodiaFlight"));

	MoveAction = NewObject<UInputAction>(this, TEXT("IA_Flight_MoveForward"));
	MoveAction->ValueType = EInputActionValueType::Axis1D;
	FlightMappingContext->MapKey(MoveAction, EKeys::W);
	FEnhancedActionKeyMapping& BackMapping = FlightMappingContext->MapKey(MoveAction, EKeys::S);
	BackMapping.Modifiers.Add(NewObject<UInputModifierNegate>(FlightMappingContext));

	MoveRightAction = NewObject<UInputAction>(this, TEXT("IA_Flight_MoveRight"));
	MoveRightAction->ValueType = EInputActionValueType::Axis1D;
	FEnhancedActionKeyMapping& LeftMapping = FlightMappingContext->MapKey(MoveRightAction, EKeys::A);
	LeftMapping.Modifiers.Add(NewObject<UInputModifierNegate>(FlightMappingContext));
	FlightMappingContext->MapKey(MoveRightAction, EKeys::D);

	// Gamepad: left stick steers exactly like WASD. The stick reports -Y when
	// pushed up, so it needs the same negation as the S key.
	FEnhancedActionKeyMapping& StickForward = FlightMappingContext->MapKey(MoveAction, EKeys::Gamepad_LeftY);
	StickForward.Modifiers.Add(NewObject<UInputModifierNegate>(FlightMappingContext));
	FlightMappingContext->MapKey(MoveRightAction, EKeys::Gamepad_LeftX);

	LookAction = NewObject<UInputAction>(this, TEXT("IA_Flight_Look"));
	LookAction->ValueType = EInputActionValueType::Axis2D;
	FlightMappingContext->MapKey(LookAction, EKeys::Mouse2D);
	FlightMappingContext->MapKey(LookAction, EKeys::Gamepad_Right2D);

	AscendAction = NewObject<UInputAction>(this, TEXT("IA_Flight_Ascend"));
	AscendAction->ValueType = EInputActionValueType::Boolean;
	FlightMappingContext->MapKey(AscendAction, EKeys::SpaceBar);
	FlightMappingContext->MapKey(AscendAction, EKeys::Gamepad_RightTrigger);

	// Descend is its own action, not the inverse of ascend: the pair has to
	// be separately bindable so a gamepad trigger and a keyboard key can sit
	// on them independently, and so the axis can report which way it is held.
	DescendAction = NewObject<UInputAction>(this, TEXT("IA_Flight_Descend"));
	DescendAction->ValueType = EInputActionValueType::Boolean;
	FlightMappingContext->MapKey(DescendAction, EKeys::LeftAlt);
	FlightMappingContext->MapKey(DescendAction, EKeys::Gamepad_LeftTrigger);

	BoostAction = NewObject<UInputAction>(this, TEXT("IA_Flight_Boost"));
	BoostAction->ValueType = EInputActionValueType::Boolean;
	FlightMappingContext->MapKey(BoostAction, EKeys::LeftShift);

	PartySwitchAction = NewObject<UInputAction>(this, TEXT("IA_Flight_PartySwitch"));
	PartySwitchAction->ValueType = EInputActionValueType::Boolean;
	FlightMappingContext->MapKey(PartySwitchAction, EKeys::LeftControl);
}

void AMelodiousFlightCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EIC)
	{
		return;
	}

	CreateInputMappingContext();

	EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMelodiousFlightCharacter::OnMoveTriggered);
	EIC->BindAction(MoveRightAction, ETriggerEvent::Triggered, this, &AMelodiousFlightCharacter::OnMoveRightTriggered);
	EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMelodiousFlightCharacter::OnLookTriggered);
	EIC->BindAction(AscendAction, ETriggerEvent::Triggered, this, &AMelodiousFlightCharacter::OnAscendTriggered);
	EIC->BindAction(AscendAction, ETriggerEvent::Completed, this, &AMelodiousFlightCharacter::OnAscendTriggered);
	EIC->BindAction(AscendAction, ETriggerEvent::Canceled, this, &AMelodiousFlightCharacter::OnAscendTriggered);
	EIC->BindAction(DescendAction, ETriggerEvent::Triggered, this, &AMelodiousFlightCharacter::OnDescendTriggered);
	EIC->BindAction(DescendAction, ETriggerEvent::Completed, this, &AMelodiousFlightCharacter::OnDescendTriggered);
	EIC->BindAction(DescendAction, ETriggerEvent::Canceled, this, &AMelodiousFlightCharacter::OnDescendTriggered);
	EIC->BindAction(BoostAction, ETriggerEvent::Started, this, &AMelodiousFlightCharacter::OnBoostStarted);
	EIC->BindAction(BoostAction, ETriggerEvent::Completed, this, &AMelodiousFlightCharacter::OnBoostCompleted);
	EIC->BindAction(BoostAction, ETriggerEvent::Canceled, this, &AMelodiousFlightCharacter::OnBoostCompleted);
	EIC->BindAction(PartySwitchAction, ETriggerEvent::Started, this, &AMelodiousFlightCharacter::OnPartySwitch);

	if (const APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (ULocalPlayer* LocalPlayer = PC->GetLocalPlayer())
		{
			if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
			{
				Subsystem->AddMappingContext(FlightMappingContext, 0);
			}
		}
	}
}

void AMelodiousFlightCharacter::UnPossessed()
{
	RemoveMappingContextOnUnpossess(FlightMappingContext);

	// A boost that is interrupted by handing control back to the party must
	// not leave his cruise speed doubled for the next time he is possessed.
	bIsAscending = false;
	bIsDescending = false;
	bIsBoosting = false;
	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->MaxFlySpeed = CruiseSpeed;
	}

	Super::UnPossessed();
}

void AMelodiousFlightCharacter::OnMoveTriggered(const FInputActionValue& Value)
{
	const float MoveValue = Value.Get<float>();
	if (FMath::IsNearlyZero(MoveValue) || !Controller)
	{
		return;
	}
	// Any steering input is a takeoff: leave the perch, then fly along the
	// full camera direction, pitch included.
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	const FVector Forward = Controller->GetControlRotation().Vector();
	AddMovementInput(Forward, MoveValue);
}

void AMelodiousFlightCharacter::OnMoveRightTriggered(const FInputActionValue& Value)
{
	const float MoveValue = Value.Get<float>();
	if (FMath::IsNearlyZero(MoveValue) || !Controller)
	{
		return;
	}
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	const FRotator YawOnly(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
	AddMovementInput(FRotationMatrix(YawOnly).GetUnitAxis(EAxis::Y), MoveValue);
}

void AMelodiousFlightCharacter::OnLookTriggered(const FInputActionValue& Value)
{
	const FVector2D LookVector = Value.Get<FVector2D>();
	AddControllerYawInput(LookVector.X * MouseLookSensitivity);
	AddControllerPitchInput(LookVector.Y * MouseLookSensitivity * (bInvertMouseY ? -1.0f : 1.0f));
}

void AMelodiousFlightCharacter::OnAscendTriggered(const FInputActionValue& Value)
{
	// Boolean action: a non-zero value means the key is held, a zero value
	// means it was released. Both directions of the same binding are handled
	// here so the flag always matches the key.
	bIsAscending = Value.Get<bool>();
	if (!bIsAscending)
	{
		return;
	}
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	AddMovementInput(FVector::UpVector, 1.0f);
}

void AMelodiousFlightCharacter::OnDescendTriggered(const FInputActionValue& Value)
{
	bIsDescending = Value.Get<bool>();
	if (!bIsDescending)
	{
		return;
	}
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	AddMovementInput(FVector::UpVector, -1.0f);
}

void AMelodiousFlightCharacter::OnBoostStarted()
{
	bIsBoosting = true;
	// A boost is a deliberate departure, not a rest state.
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	GetCharacterMovement()->MaxFlySpeed = BoostSpeed;
}

void AMelodiousFlightCharacter::OnBoostCompleted()
{
	bIsBoosting = false;
	GetCharacterMovement()->MaxFlySpeed = CruiseSpeed;
}

void AMelodiousFlightCharacter::ApplyHeightAxis()
{
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	if (!Movement)
	{
		return;
	}

	// The climb rate is capped independently of MaxFlySpeed. Without this the
	// horizontal speed cap doubles the climb rate while boosting, and holding
	// the key puts him out of the playable volume in two seconds.
	const float Cap = GetVerticalSpeedCap();
	if (Movement->Velocity.Z > Cap)
	{
		Movement->Velocity.Z = Cap;
	}
	else if (Movement->Velocity.Z < -Cap)
	{
		Movement->Velocity.Z = -Cap;
	}
}

void AMelodiousFlightCharacter::UpdateCrestRaise(float DeltaSeconds)
{
	USkeletalMeshComponent* Mesh = GetMesh();
	if (!Mesh)
	{
		return;
	}

	if (!bWarnedMissingCrestMorph)
	{
		// A morph that is not on the mesh is a silent no-op, so say so once
		// instead of leaving a crest that never moves.
		bWarnedMissingCrestMorph = true;
		const USkeletalMesh* Asset = Mesh->GetSkeletalMeshAsset();
		bool bFound = false;
		if (Asset)
		{
			for (const FMorphTarget& MorphTarget : Asset->GetMorphTargets())
			{
				if (MorphTarget.GetFName() == CrestMorphName)
				{
					bFound = true;
					break;
				}
			}
		}
		if (!bFound)
		{
			UE_LOG(LogTemp, Warning, TEXT("Melodia: crest morph '%s' is not on %s; the crest raise will not show."),
				*CrestMorphName.ToString(), *GetNameSafe(Asset));
		}
	}

	const float Yaw = GetActorRotation().Yaw;
	if (!bHasPreviousYaw)
	{
		PreviousActorYaw = Yaw;
		bHasPreviousYaw = true;
	}

	const float DeltaYaw = FMath::FindDeltaAngleDegrees(PreviousActorYaw, Yaw);
	PreviousActorYaw = Yaw;

	const float TurnRate = FMath::Abs(DeltaYaw) / FMath::Max(DeltaSeconds, KINDA_SMALL_NUMBER);
	const float Target = FMath::Clamp(TurnRate / FMath::Max(CrestRaiseTurnRate, 1.0f), 0.0f, 1.0f);
	CurrentCrestRaise = FMath::FInterpTo(CurrentCrestRaise, Target, DeltaSeconds, CrestRaiseRiseSpeed);

	Mesh->SetMorphTarget(CrestMorphName, CurrentCrestRaise);
}

void AMelodiousFlightCharacter::UpdatePerchApproach(float DeltaSeconds)
{
	if (!bIsPerchApproaching || !CurrentPerch)
	{
		return;
	}

	PerchApproachRemaining = FMath::Max(0.0f, PerchApproachRemaining - DeltaSeconds);
	const float Alpha = (PerchApproachDuration <= 0.0f)
		? 1.0f
		: FMath::Clamp(1.0f - (PerchApproachRemaining / PerchApproachDuration), 0.0f, 1.0f);

	const FVector Target = CurrentPerch->GetLandingLocation();
	const FRotator TargetRot = CurrentPerch->GetLandingRotation();
	const FVector Location = FMath::Lerp(PerchApproachStartLoc, Target, Alpha);
	const FRotator Rotation = FMath::Lerp(PerchApproachStartRot, TargetRot, Alpha);

	SetActorLocationAndRotation(Location, Rotation, false, nullptr, ETeleportType::TeleportPhysics);

	if (PerchApproachRemaining <= 0.0f)
	{
		SettleOnPerch(CurrentPerch);
	}
}

void AMelodiousFlightCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UpdateCrestRaise(DeltaSeconds);

	if (bIsPerchApproaching)
	{
		// A glide-in in progress owns him: no idle-perch re-trigger, and the
		// steering inputs still cancel it through LeavePerch().
		UpdatePerchApproach(DeltaSeconds);
		return;
	}

	if (bIsPerched)
	{
		// Perched birds stay perched until the player steers; the takeoff is
		// driven from the input handlers so it happens on the same frame the
		// stick moves, not one tick later.
		return;
	}

	ApplyHeightAxis();

	SecondsSinceSteering += DeltaSeconds;
	if (!bIsBoosting && SecondsSinceSteering >= PerchIdleDelay)
	{
		BeginPerchApproach();
	}
}

ASirPerchPoint* AMelodiousFlightCharacter::FindNearestPerch(float& OutDistance) const
{
	OutDistance = -1.0f;

	const UWorld* World = GetWorld();
	if (!World)
	{
		return nullptr;
	}

	const FVector SearchOrigin = GetActorLocation();
	const float MaxDistanceSquared = FMath::Square(PerchSearchRadius);
	float BestDistanceSquared = MaxDistanceSquared;
	ASirPerchPoint* Best = nullptr;

	for (TActorIterator<ASirPerchPoint> It(World); It; ++It)
	{
		ASirPerchPoint* Candidate = *It;
		if (!IsValid(Candidate))
		{
			continue;
		}
		// Measure to the landing spot, not the actor pivot: a perch authored
		// with an offset must attract the bird to where it will actually sit.
		const float DistanceSquared = FVector::DistSquared(SearchOrigin, Candidate->GetLandingLocation());
		if (DistanceSquared <= BestDistanceSquared)
		{
			BestDistanceSquared = DistanceSquared;
			Best = Candidate;
		}
	}

	if (Best)
	{
		OutDistance = FMath::Sqrt(BestDistanceSquared);
	}
	return Best;
}

bool AMelodiousFlightCharacter::BeginPerchApproach()
{
	if (bIsPerched || bIsPerchApproaching)
	{
		return false;
	}

	float Distance = 0.0f;
	ASirPerchPoint* Perch = FindNearestPerch(Distance);
	if (!Perch)
	{
		return false;
	}

	CurrentPerch = Perch;
	PerchApproachStartLoc = GetActorLocation();
	PerchApproachStartRot = GetActorRotation();
	PerchApproachRemaining = FMath::Max(0.0f, PerchApproachDuration);
	bIsPerchApproaching = true;

	UE_LOG(LogTemp, Verbose, TEXT("Melodia: Sir gliding to perch %s at %s (%.0f units)."),
		*GetNameSafe(Perch), *Perch->GetLandingLocation().ToCompactString(), Distance);
	return true;
}

void AMelodiousFlightCharacter::SettleOnPerch(ASirPerchPoint* Perch)
{
	if (!Perch)
	{
		return;
	}

	// Land exactly on the spot so he settles instead of overshooting it, and
	// keep MOVE_Flying so there is no gravity/falling transition to tune.
	SetActorLocationAndRotation(Perch->GetLandingLocation(), Perch->GetLandingRotation(), false, nullptr, ETeleportType::TeleportPhysics);

	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->SetMovementMode(MOVE_Flying);
		Movement->StopMovementImmediately();
		Movement->Velocity = FVector::ZeroVector;
	}

	CurrentPerch = Perch;
	bIsPerched = true;
	bIsPerchApproaching = false;
	PerchApproachRemaining = 0.0f;
	SecondsSinceSteering = 0.0f;

	UE_LOG(LogTemp, Verbose, TEXT("Melodia: Sir perched on %s at %s."),
		*GetNameSafe(Perch), *Perch->GetLandingLocation().ToCompactString());
}

bool AMelodiousFlightCharacter::TryLandOnNearestPerch()
{
	if (bIsPerched)
	{
		return true;
	}

	float Distance = 0.0f;
	ASirPerchPoint* Perch = FindNearestPerch(Distance);
	if (!Perch)
	{
		return false;
	}

	SettleOnPerch(Perch);
	return true;
}

void AMelodiousFlightCharacter::LeavePerch()
{
	// Any steering input during the glide-in is a takeoff too, so the
	// approach is cancelled here as well as the settled state.
	bIsPerchApproaching = false;
	PerchApproachRemaining = 0.0f;

	if (!bIsPerched && !CurrentPerch)
	{
		return;
	}

	UE_LOG(LogTemp, Verbose, TEXT("Melodia: Sir left perch %s."), *GetNameSafe(CurrentPerch));
	CurrentPerch = nullptr;
	bIsPerched = false;
}
