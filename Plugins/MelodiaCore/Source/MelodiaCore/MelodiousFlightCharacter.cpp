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
#include "MelodiaPartySubsystem.h"

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
	// flight framing here (wider arm, flatter pitch than ground exploration).
	CameraBoom->TargetArmLength = 520.0f;
	CameraBoom->SetRelativeRotation(FRotator(-12.0f, 0.0f, 0.0f));
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
	Super::UnPossessed();
}

void AMelodiousFlightCharacter::OnMoveTriggered(const FInputActionValue& Value)
{
	const float MoveValue = Value.Get<float>();
	if (FMath::IsNearlyZero(MoveValue) || !Controller)
	{
		return;
	}
	// Fly along the full camera direction, pitch included.
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
	AddMovementInput(FVector::UpVector, 1.0f);
}

void AMelodiousFlightCharacter::OnBoostStarted()
{
	GetCharacterMovement()->MaxFlySpeed = BoostSpeed;
}

void AMelodiousFlightCharacter::OnBoostCompleted()
{
	GetCharacterMovement()->MaxFlySpeed = CruiseSpeed;
}

