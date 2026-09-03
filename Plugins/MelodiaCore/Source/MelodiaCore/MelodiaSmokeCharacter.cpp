#include "MelodiaSmokeCharacter.h"

#include "Camera/CameraComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputModifiers.h"
#include "InputMappingContext.h"
#include "InputAction.h"
#include "Components/SkeletalMeshComponent.h"
#include "Animation/AnimMontage.h"
#include "Animation/AnimInstance.h"
#include "Blueprint/UserWidget.h"
#include "UObject/UnrealType.h"
#include "Materials/MaterialInterface.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/PlayerController.h"
#include "MelodiaExplorationHUDWidget.h"
#include "MelodiaPartySubsystem.h"
#include "UObject/ConstructorHelpers.h"

AMelodiaSmokeCharacter::AMelodiaSmokeCharacter()
{
	PrimaryActorTick.bCanEverTick = true;
	OrreryWidgetClass = TSoftClassPtr<UUserWidget>(
		FSoftObjectPath(TEXT("/Game/Melodia/UI/WBP_ComicOrrery.WBP_ComicOrrery_C")));

	// GameMode's default-pawn spawn silently no-ops if the PlayerStart is blocked
	// (e.g. set-dressing furniture placed over it) and this is left at the engine
	// default. Always spawn the player, nudged out of any overlap, rather than fail.
	SpawnCollisionHandlingMethod = ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButAlwaysSpawn;

	GetCharacterMovement()->MaxWalkSpeed = BaseWalkSpeed;
	GetCharacterMovement()->bOrientRotationToMovement = true;
	GetCharacterMovement()->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
	bUseControllerRotationYaw = false;
	JumpMaxCount = 1;

	// Nikki-style arc: quick liftoff, floaty apex, heavy fall (fall/apex scales in Tick).
	JumpMaxHoldTime = 0.25f;
	GetCharacterMovement()->JumpZVelocity = 620.0f;
	GetCharacterMovement()->GravityScale = 1.6f;
	GetCharacterMovement()->AirControl = 0.55f;
	GetCharacterMovement()->AirControlBoostMultiplier = 2.0f;
	GetCharacterMovement()->AirControlBoostVelocityThreshold = 25.0f;
	GetCharacterMovement()->BrakingDecelerationFalling = 300.0f;
	GetCharacterMovement()->FallingLateralFriction = 0.4f;

	// CameraBoom/FollowCamera are created by AMelodiaCharacterBase; tune the
	// ground-exploration framing here.
	CameraBoom->TargetArmLength = 420.0f;
	CameraBoom->SetRelativeRotation(FRotator(-18.0f, 0.0f, 0.0f));

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> MelusinaMesh(TEXT("/Game/Melodia/Characters/Melusina/SK_Melusina.SK_Melusina"));
	if (MelusinaMesh.Succeeded())
	{
		GetMesh()->SetSkeletalMesh(MelusinaMesh.Object);
		GetMesh()->SetRelativeLocation(FVector(0.0f, 0.0f, -88.0f));
		// The authored character faces +Y; ACharacter locomotion faces +X.
		GetMesh()->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
	}

	WaterHairMesh = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("WaterHairMesh"));
	WaterHairMesh->SetupAttachment(GetMesh());
	WaterHairMesh->SetRelativeTransform(FTransform::Identity);
	WaterHairMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	WaterHairMesh->SetGenerateOverlapEvents(false);

	static ConstructorHelpers::FObjectFinder<USkeletalMesh> MelusinaHair(
		TEXT("/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair.SK_MelusinaHair"));
	if (MelusinaHair.Succeeded())
	{
		WaterHairMesh->SetSkeletalMesh(MelusinaHair.Object);
	}

	static ConstructorHelpers::FObjectFinder<UMaterialInterface> WaterHairMaterial(
		TEXT("/Game/EnvSandbox/Materials/Instances/Melusina/MI_Melusina_WaterHair.MI_Melusina_WaterHair"));
	if (WaterHairMaterial.Succeeded())
	{
		for (int32 MaterialIndex = 0; MaterialIndex < WaterHairMesh->GetNumMaterials(); ++MaterialIndex)
		{
			WaterHairMesh->SetMaterial(MaterialIndex, WaterHairMaterial.Object);
		}
	}

	static ConstructorHelpers::FClassFinder<UAnimInstance> WaterHairAnim(
		TEXT("/Game/Melodia/Characters/Melusina/Hair/ABP_Melusina_WaterHair"));
	if (WaterHairAnim.Succeeded())
	{
		WaterHairMesh->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		WaterHairMesh->SetAnimInstanceClass(WaterHairAnim.Class);
	}

	static ConstructorHelpers::FClassFinder<UAnimInstance> MelusinaAnim(TEXT("/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"));
	if (MelusinaAnim.Succeeded())
	{
		GetMesh()->SetAnimationMode(EAnimationMode::AnimationBlueprint);
		GetMesh()->SetAnimInstanceClass(MelusinaAnim.Class);
	}

	static ConstructorHelpers::FObjectFinder<UAnimMontage> MelusinaLanding(TEXT("/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_JumpEnd.AM_Mocap_JumpEnd"));
	if (MelusinaLanding.Succeeded())
	{
		LandingMontage = MelusinaLanding.Object;
	}
}

void AMelodiaSmokeCharacter::BeginPlay()
{
	Super::BeginPlay();

	GetMesh()->bDisableClothSimulation = !bEnableSkirtClothSimulation;

	// The hair owns a distinct skeleton, so LeaderPoseComponent is unsafe here.
	// Its AnimBP copies shared body bones, then evaluates Kawaii Physics on the
	// hair-only chain. Supply the body mesh to that transient AnimBP input.
	if (WaterHairMesh && GetMesh())
	{
		WaterHairMesh->SetLeaderPoseComponent(nullptr);
		WaterHairMesh->InitAnim(true);
		if (UAnimInstance* HairAnimInstance = WaterHairMesh->GetAnimInstance())
		{
			if (FObjectPropertyBase* SourceMeshProperty = FindFProperty<FObjectPropertyBase>(
				HairAnimInstance->GetClass(), TEXT("SourceMeshComponent")))
			{
				SourceMeshProperty->SetObjectPropertyValue_InContainer(HairAnimInstance, GetMesh());
			}
			else
			{
				UE_LOG(LogTemp, Warning, TEXT("MelodiaSmokeCharacter: Hair AnimBP is missing SourceMeshComponent."));
			}
		}
	}

	BaseGravityScale = GetCharacterMovement()->GravityScale;
	BaseAirControl = GetCharacterMovement()->AirControl;
	if (CameraBoom)
	{
		BaseBoomLength = CameraBoom->TargetArmLength;
	}

	if (APlayerController* PC = Cast<APlayerController>(GetController()); PC && IsLocallyControlled())
	{
		ExplorationHUDWidget = CreateWidget<UMelodiaExplorationHUDWidget>(PC, UMelodiaExplorationHUDWidget::StaticClass());
		if (ExplorationHUDWidget)
		{
			ExplorationHUDWidget->AddToViewport(5);
		}
	}

	if (UMelodiaPartySubsystem* Party = UMelodiaPartySubsystem::Get(this))
	{
		Party->RegisterPawn(this, 0);
	}
}

void AMelodiaSmokeCharacter::Landed(const FHitResult& Hit)
{
	StopGlide();

	Super::Landed(Hit);

	// Buffered jump: pressed shortly before touchdown -> jump again immediately.
	if (bJumpHeld || TimeSinceJumpPressed <= JumpBufferTime)
	{
		if (TimeSinceJumpPressed <= JumpBufferTime)
		{
			TimeSinceJumpPressed = BIG_NUMBER;
			Jump();
			return;
		}
	}

	if (LandingMontage && GetMesh() && GetMesh()->GetAnimInstance())
	{
		GetMesh()->GetAnimInstance()->Montage_Play(LandingMontage, 1.0f);
	}
}

bool AMelodiaSmokeCharacter::CanJumpInternal_Implementation() const
{
	// Coyote time: a recent walk-off still counts as grounded for jump purposes.
	if (Super::CanJumpInternal_Implementation())
	{
		return true;
	}
	return !bWasJumping && GetCharacterMovement()->IsFalling() && TimeSinceLeftGround <= CoyoteTime;
}

void AMelodiaSmokeCharacter::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UCharacterMovementComponent* CMC = GetCharacterMovement();
	if (!CMC)
	{
		return;
	}

	TimeSinceJumpPressed += DeltaSeconds;
	if (CMC->IsMovingOnGround())
	{
		TimeSinceLeftGround = 0.0f;
	}
	else
	{
		TimeSinceLeftGround += DeltaSeconds;
	}

	if (CMC->IsFalling())
	{
		const float Vz = GetVelocity().Z;

		// Glide entry: hold Space while descending.
		if (!bIsGliding && bJumpHeld && Vz < 0.0f && !bWasJumping)
		{
			StartGlide();
		}

		if (bIsGliding)
		{
			if (CMC->Velocity.Z < GlideTerminalZ)
			{
				CMC->Velocity.Z = GlideTerminalZ;
			}
		}
		else
		{
			// Variable gravity: floaty apex, heavy fall.
			if (FMath::Abs(Vz) < ApexVelocityThreshold)
			{
				CMC->GravityScale = ApexGravityScale;
			}
			else if (Vz < 0.0f)
			{
				CMC->GravityScale = FallGravityScale;
			}
			else
			{
				CMC->GravityScale = BaseGravityScale;
			}
		}
	}
	else if (!bIsGliding)
	{
		CMC->GravityScale = BaseGravityScale;
	}

	// Camera boom ease toward glide/normal length.
	if (CameraBoom)
	{
		const float Target = bIsGliding ? BaseBoomLength + GlideBoomExtension : BaseBoomLength;
		CameraBoom->TargetArmLength = FMath::FInterpTo(CameraBoom->TargetArmLength, Target, DeltaSeconds, 4.0f);
	}
}

void AMelodiaSmokeCharacter::StartGlide()
{
	if (bIsGliding || !GetCharacterMovement()->IsFalling())
	{
		return;
	}
	bIsGliding = true;
	GetCharacterMovement()->GravityScale = GlideGravityScale;
	GetCharacterMovement()->AirControl = GlideAirControl;
}

void AMelodiaSmokeCharacter::StopGlide()
{
	if (!bIsGliding)
	{
		return;
	}
	bIsGliding = false;
	GetCharacterMovement()->GravityScale = BaseGravityScale;
	GetCharacterMovement()->AirControl = BaseAirControl;
}

void AMelodiaSmokeCharacter::OnJumpStarted()
{
	bJumpHeld = true;
	TimeSinceJumpPressed = 0.0f;
	Jump();
}

void AMelodiaSmokeCharacter::OnJumpCompleted()
{
	bJumpHeld = false;
	StopJumping();
	StopGlide();
}

void AMelodiaSmokeCharacter::UnPossessed()
{
	// Avoid stacked input contexts across pawn swaps.
	RemoveMappingContextOnUnpossess(MoveMappingContext);
	Super::UnPossessed();
}

void AMelodiaSmokeCharacter::CreateInputMappingContext()
{
	if (MoveMappingContext)
	{
		return;
	}

	MoveMappingContext = NewObject<UInputMappingContext>(this, TEXT("IMC_MelodiaMove"));

	MoveAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_MoveForward"));
	MoveAction->ValueType = EInputActionValueType::Axis1D;

	MoveRightAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_MoveRight"));
	MoveRightAction->ValueType = EInputActionValueType::Axis1D;

	LookAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_Look"));
	LookAction->ValueType = EInputActionValueType::Axis2D;

	MoveMappingContext->MapKey(MoveAction, EKeys::W);
	FEnhancedActionKeyMapping& BackMapping = MoveMappingContext->MapKey(MoveAction, EKeys::S);
	BackMapping.Modifiers.Add(NewObject<UInputModifierNegate>(MoveMappingContext));

	FEnhancedActionKeyMapping& LeftMapping = MoveMappingContext->MapKey(MoveRightAction, EKeys::A);
	LeftMapping.Modifiers.Add(NewObject<UInputModifierNegate>(MoveMappingContext));
	MoveMappingContext->MapKey(MoveRightAction, EKeys::D);

	MoveMappingContext->MapKey(LookAction, EKeys::Mouse2D);

	SprintAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_Sprint"));
	SprintAction->ValueType = EInputActionValueType::Boolean;
	MoveMappingContext->MapKey(SprintAction, EKeys::LeftShift);

	JumpInputAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_Jump"));
	JumpInputAction->ValueType = EInputActionValueType::Boolean;
	MoveMappingContext->MapKey(JumpInputAction, EKeys::SpaceBar);

	InteractAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_Interact"));
	InteractAction->ValueType = EInputActionValueType::Boolean;
	MoveMappingContext->MapKey(InteractAction, EKeys::F);
	MoveMappingContext->MapKey(InteractAction, EKeys::E);
	MoveMappingContext->MapKey(InteractAction, EKeys::Gamepad_FaceButton_Bottom);

	PartySwitchAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_PartySwitch"));
	PartySwitchAction->ValueType = EInputActionValueType::Boolean;
	MoveMappingContext->MapKey(PartySwitchAction, EKeys::LeftControl);

	OrreryMenuAction = NewObject<UInputAction>(this, TEXT("IA_Melodia_OrreryMenu"));
	OrreryMenuAction->ValueType = EInputActionValueType::Boolean;
	MoveMappingContext->MapKey(OrreryMenuAction, EKeys::M);
	MoveMappingContext->MapKey(OrreryMenuAction, EKeys::Tab);
}

void AMelodiaSmokeCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	if (!PlayerInputComponent)
	{
		return;
	}

	UEnhancedInputComponent* EIC = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!EIC)
	{
		UE_LOG(LogTemp, Warning, TEXT("MelodiaSmokeCharacter: InputComponent is not EnhancedInputComponent."));
		return;
	}

	CreateInputMappingContext();

	EIC->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AMelodiaSmokeCharacter::OnMoveTriggered);
	EIC->BindAction(MoveRightAction, ETriggerEvent::Triggered, this, &AMelodiaSmokeCharacter::OnMoveRightTriggered);
	EIC->BindAction(LookAction, ETriggerEvent::Triggered, this, &AMelodiaSmokeCharacter::OnLookTriggered);
	EIC->BindAction(SprintAction, ETriggerEvent::Started, this, &AMelodiaSmokeCharacter::OnSprintStarted);
	EIC->BindAction(SprintAction, ETriggerEvent::Completed, this, &AMelodiaSmokeCharacter::OnSprintCompleted);
	EIC->BindAction(SprintAction, ETriggerEvent::Canceled, this, &AMelodiaSmokeCharacter::OnSprintCompleted);
	EIC->BindAction(JumpInputAction, ETriggerEvent::Started, this, &AMelodiaSmokeCharacter::OnJumpStarted);
	EIC->BindAction(JumpInputAction, ETriggerEvent::Completed, this, &AMelodiaSmokeCharacter::OnJumpCompleted);
	EIC->BindAction(JumpInputAction, ETriggerEvent::Canceled, this, &AMelodiaSmokeCharacter::OnJumpCompleted);
	EIC->BindAction(InteractAction, ETriggerEvent::Started, this, &AMelodiaSmokeCharacter::OnInteractRequested);
	EIC->BindAction(PartySwitchAction, ETriggerEvent::Started, this, &AMelodiaSmokeCharacter::OnPartySwitch);
	EIC->BindAction(OrreryMenuAction, ETriggerEvent::Started, this, &AMelodiaSmokeCharacter::OnOrreryMenuRequested);

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (ULocalPlayer* LocalPlayer = PC->GetLocalPlayer())
		{
			if (UEnhancedInputLocalPlayerSubsystem* Subsystem = LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
			{
				Subsystem->AddMappingContext(MoveMappingContext, 0);
			}
		}
	}
}

void AMelodiaSmokeCharacter::OnMoveTriggered(const FInputActionValue& Value)
{
	const float MoveValue = Value.Get<float>();
	const FRotator ControlRotation = bCameraRelativeMovement && Controller
		? Controller->GetControlRotation()
		: GetActorRotation();
	const FRotator YawRotation(0.0f, ControlRotation.Yaw, 0.0f);
	const FVector ForwardDirection = FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X);
	if (!FMath::IsNearlyZero(MoveValue))
	{
		AddMovementInput(ForwardDirection, MoveValue * MoveSpeedScale);
	}
}

void AMelodiaSmokeCharacter::OnMoveRightTriggered(const FInputActionValue& Value)
{
	const float MoveValue = Value.Get<float>();
	const FRotator ControlRotation = bCameraRelativeMovement && Controller
		? Controller->GetControlRotation()
		: GetActorRotation();
	const FVector RightDirection = FRotationMatrix(FRotator(0.0f, ControlRotation.Yaw, 0.0f)).GetUnitAxis(EAxis::Y);
	if (!FMath::IsNearlyZero(MoveValue))
	{
		AddMovementInput(RightDirection, MoveValue * MoveSpeedScale);
	}
}

void AMelodiaSmokeCharacter::OnLookTriggered(const FInputActionValue& Value)
{
	const FVector2D LookVector = Value.Get<FVector2D>();
	AddControllerYawInput(LookVector.X * MouseLookSensitivity);
	AddControllerPitchInput(LookVector.Y * MouseLookSensitivity * (bInvertMouseY ? -1.0f : 1.0f));
}

void AMelodiaSmokeCharacter::OnInteractRequested()
{
	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC || PC->bShowMouseCursor)
	{
		// Dialogue/menu owns interaction while the cursor is visible.
		return;
	}

	TArray<AActor*> OverlappingActors;
	GetOverlappingActors(OverlappingActors);
	OverlappingActors.Sort([this](const AActor& Left, const AActor& Right)
	{
		return FVector::DistSquared(GetActorLocation(), Left.GetActorLocation())
			< FVector::DistSquared(GetActorLocation(), Right.GetActorLocation());
	});

	for (AActor* Candidate : OverlappingActors)
	{
		UFunction* TryInteractFunction = Candidate ? Candidate->FindFunction(TEXT("TryInteract")) : nullptr;
		if (!TryInteractFunction)
		{
			continue;
		}

		struct FTryInteractParameters
		{
			AActor* InteractingActor = nullptr;
			bool ReturnValue = false;
		};

		FTryInteractParameters Parameters;
		Parameters.InteractingActor = this;
		Candidate->ProcessEvent(TryInteractFunction, &Parameters);
		if (Parameters.ReturnValue)
		{
			UE_LOG(LogTemp, Log, TEXT("MELODIA_INTERACT actor=%s target=%s"), *GetName(), *GetNameSafe(Candidate));
			return;
		}
	}

	UE_LOG(LogTemp, Verbose, TEXT("MELODIA_INTERACT no eligible overlapping target for %s"), *GetName());
}

void AMelodiaSmokeCharacter::OnOrreryMenuRequested()
{
	UUserWidget* ActiveWidget = nullptr;
	if (UFunction* ToggleFunction = FindFunction(TEXT("ToggleOrreryMenu")))
	{
		ProcessEvent(ToggleFunction, nullptr);
		if (FObjectPropertyBase* WidgetProperty = FindFProperty<FObjectPropertyBase>(GetClass(), TEXT("ActiveOrreryWidget")))
		{
			ActiveWidget = Cast<UUserWidget>(WidgetProperty->GetObjectPropertyValue_InContainer(this));
		}
	}
	else
	{
		if (ActiveNativeOrreryWidget && ActiveNativeOrreryWidget->IsInViewport())
		{
			ActiveNativeOrreryWidget->RemoveFromParent();
			ActiveNativeOrreryWidget = nullptr;
		}
		else if (APlayerController* OwningPC = Cast<APlayerController>(GetController()))
		{
			UClass* WidgetClass = OrreryWidgetClass.LoadSynchronous();
			if (WidgetClass && WidgetClass->IsChildOf(UUserWidget::StaticClass()))
			{
				ActiveNativeOrreryWidget = CreateWidget<UUserWidget>(OwningPC, WidgetClass);
				if (ActiveNativeOrreryWidget)
				{
					ActiveNativeOrreryWidget->AddToViewport(40);
				}
			}
			else
			{
				UE_LOG(LogTemp, Error, TEXT("MelodiaSmokeCharacter: canonical WBP_ComicOrrery class is unavailable."));
			}
		}
		ActiveWidget = ActiveNativeOrreryWidget;
	}

	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC)
	{
		return;
	}

	if (ActiveWidget && ActiveWidget->IsInViewport())
	{
		FInputModeGameAndUI InputMode;
		InputMode.SetWidgetToFocus(ActiveWidget->TakeWidget());
		InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		PC->SetInputMode(InputMode);
		PC->bShowMouseCursor = true;
	}
	else
	{
		PC->SetInputMode(FInputModeGameOnly());
		PC->bShowMouseCursor = false;
	}
}
void AMelodiaSmokeCharacter::OnSprintStarted()
{
	bIsSprinting = true;
	GetCharacterMovement()->MaxWalkSpeed = BaseWalkSpeed * SprintSpeedMultiplier;
}

void AMelodiaSmokeCharacter::OnSprintCompleted()
{
	bIsSprinting = false;
	GetCharacterMovement()->MaxWalkSpeed = BaseWalkSpeed;
}
