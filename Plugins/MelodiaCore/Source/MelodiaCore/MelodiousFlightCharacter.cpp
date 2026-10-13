#include "MelodiousFlightCharacter.h"

#include "Camera/CameraComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
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

	LookAction = NewObject<UInputAction>(this, TEXT("IA_Flight_Look"));
	LookAction->ValueType = EInputActionValueType::Axis2D;
	FlightMappingContext->MapKey(LookAction, EKeys::Mouse2D);

	AscendAction = NewObject<UInputAction>(this, TEXT("IA_Flight_Ascend"));
	AscendAction->ValueType = EInputActionValueType::Boolean;
	FlightMappingContext->MapKey(AscendAction, EKeys::SpaceBar);
	FlightMappingContext->MapKey(AscendAction, EKeys::Gamepad_RightTrigger);

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
	EIC->BindAction(DescendAction, ETriggerEvent::Triggered, this, &AMelodiousFlightCharacter::OnDescendTriggered);
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
	// The Completed callback can be lost when party switching removes the mapping
	// context while Shift is held. Never carry boost into a later possession.
	OnBoostCompleted();
	RemoveMappingContextOnUnpossess(FlightMappingContext);
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
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	AddMovementInput(FVector::UpVector, 1.0f);
}

void AMelodiousFlightCharacter::OnDescendTriggered(const FInputActionValue& Value)
{
	LeavePerch();
	SecondsSinceSteering = 0.0f;
	AddMovementInput(FVector::DownVector, 1.0f);
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

void AMelodiousFlightCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bIsPerched)
	{
		// Perched birds stay perched until the player steers; the takeoff is
		// driven from the input handlers so it happens on the same frame the
		// stick moves, not one tick later.
		return;
	}

	SecondsSinceSteering += DeltaSeconds;
	if (!bIsBoosting && SecondsSinceSteering >= PerchIdleDelay)
	{
		TryLandOnNearestPerch();
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

	// Teleport onto the spot so he settles instead of overshooting it, and
	// keep MOVE_Flying so there is no gravity/falling transition to tune.
	SetActorLocation(Perch->GetLandingLocation(), false, nullptr, ETeleportType::TeleportPhysics);
	SetActorRotation(Perch->GetLandingRotation());

	if (UCharacterMovementComponent* Movement = GetCharacterMovement())
	{
		Movement->SetMovementMode(MOVE_Flying);
		Movement->StopMovementImmediately();
		Movement->Velocity = FVector::ZeroVector;
	}

	CurrentPerch = Perch;
	bIsPerched = true;
	SecondsSinceSteering = 0.0f;

	UE_LOG(LogTemp, Verbose, TEXT("Melodia: Sir perched on %s at %s (%.0f units)."),
		*GetNameSafe(Perch), *Perch->GetLandingLocation().ToCompactString(), Distance);
	return true;
}

void AMelodiousFlightCharacter::LeavePerch()
{
	if (!bIsPerched)
	{
		return;
	}
	UE_LOG(LogTemp, Verbose, TEXT("Melodia: Sir left perch %s."), *GetNameSafe(CurrentPerch));
	CurrentPerch = nullptr;
	bIsPerched = false;
}

