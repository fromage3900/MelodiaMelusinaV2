// Battle arena actor implementation.

#include "MelodiaBattleArena.h"
#include "Camera/CameraComponent.h"
#include "Camera/CameraShakeBase.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "MelodiaBattleSession.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "MelodiaPacingSubsystem.h"

AMelodiaBattleArena::AMelodiaBattleArena()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	ArenaRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ArenaRoot"));
	RootComponent = ArenaRoot;

	EnemyMeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("EnemyMesh"));
	EnemyMeshComponent->SetupAttachment(ArenaRoot);
	EnemyMeshComponent->SetVisibility(false);
	EnemyMeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	CombatState = CreateDefaultSubobject<UMelodiaCombatStateComponent>(TEXT("CombatState"));
	RhythmExecution = CreateDefaultSubobject<UMelodiaRhythmExecutionComponent>(TEXT("RhythmExecution"));

	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(ArenaRoot);
	CameraBoom->bDoCollisionTest = false;

	BattleCamera = CreateDefaultSubobject<UCameraComponent>(TEXT("BattleCamera"));
	BattleCamera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);

	// Default framings: legacy offset/rotation fields remain the Command baseline.
	FMelodiaCameraFraming Command;
	Command.Offset = BattleCameraOffset;     Command.Rotation = BattleCameraRotation;
	Command.ArmLength = 450.0f;              Command.FOV = 32.0f;
	FMelodiaCameraFraming Execution;
	Execution.Offset = FVector(-300.0f, 60.0f, 140.0f);  Execution.Rotation = FRotator(-8.0f, -12.0f, 0.0f);
	Execution.ArmLength = 380.0f;            Execution.FOV = 40.0f;
	FMelodiaCameraFraming EnemyTurn;
	EnemyTurn.Offset = FVector(-380.0f, -160.0f, 170.0f); EnemyTurn.Rotation = FRotator(-12.0f, 18.0f, 0.0f);
	EnemyTurn.ArmLength = 430.0f;            EnemyTurn.FOV = 36.0f;
	FMelodiaCameraFraming Ult;
	Ult.Offset = FVector(-220.0f, 0.0f, 120.0f);          Ult.Rotation = FRotator(-5.0f, 0.0f, 0.0f);
	Ult.ArmLength = 300.0f;                  Ult.FOV = 27.0f;
	FMelodiaCameraFraming Break;
	Break.Offset = FVector(-280.0f, 90.0f, 150.0f);       Break.Rotation = FRotator(-10.0f, -18.0f, 0.0f);
	Break.ArmLength = 280.0f;                Break.FOV = 34.0f;
	CameraFramings.Add(EMelodiaArenaCameraPhase::Command, Command);
	CameraFramings.Add(EMelodiaArenaCameraPhase::Execution, Execution);
	CameraFramings.Add(EMelodiaArenaCameraPhase::EnemyTurn, EnemyTurn);
	CameraFramings.Add(EMelodiaArenaCameraPhase::Ult, Ult);
	CameraFramings.Add(EMelodiaArenaCameraPhase::Break, Break);
	CurrentFraming = Command;
	TargetFraming = Command;
}

void AMelodiaBattleArena::BeginPlay()
{
	Super::BeginPlay();

	if (UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this))
	{
		Session->OnBattlePhaseChanged.AddDynamic(this, &AMelodiaBattleArena::HandleBattlePhaseChanged);
	}
}

void AMelodiaBattleArena::HandleBattlePhaseChanged(const EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase)
{
	if (!bArenaActive)
	{
		return;
	}
	switch (NewPhase)
	{
	case EMelodiaBattlePhase::AwaitingPlayerCommand: SetCameraPhase(EMelodiaArenaCameraPhase::Command); break;
	case EMelodiaBattlePhase::RhythmExecution:       SetCameraPhase(EMelodiaArenaCameraPhase::Execution); break;
	case EMelodiaBattlePhase::EnemyTurn:             SetCameraPhase(EMelodiaArenaCameraPhase::EnemyTurn); break;
	case EMelodiaBattlePhase::Victory:               SetCameraPhase(EMelodiaArenaCameraPhase::Break, 0.4f); break;
	default: break;
	}
}

FMelodiaCameraFraming AMelodiaBattleArena::FramingFor(const EMelodiaArenaCameraPhase Phase) const
{
	if (const FMelodiaCameraFraming* Found = CameraFramings.Find(Phase))
	{
		return *Found;
	}
	return CameraFramings.FindRef(EMelodiaArenaCameraPhase::Command);
}

void AMelodiaBattleArena::ApplyFraming(const FMelodiaCameraFraming& Framing)
{
	if (CameraBoom)
	{
		CameraBoom->SetRelativeLocation(Framing.Offset);
		CameraBoom->SetRelativeRotation(Framing.Rotation);
		CameraBoom->TargetArmLength = Framing.ArmLength;
	}
	if (BattleCamera)
	{
		BattleCamera->SetFieldOfView(Framing.FOV);
	}
}

void AMelodiaBattleArena::SetCameraPhase(const EMelodiaArenaCameraPhase Phase, const float BlendTime)
{
	CameraPhase = Phase;
	bDollyActive = false;
	TargetFraming = FramingFor(Phase);
	CameraBlendSpeed = BlendTime > KINDA_SMALL_NUMBER ? 1.0f / BlendTime : 100.0f;
	SetActorTickEnabled(true);
}

void AMelodiaBattleArena::PlayBreakDollyIn(const float Duration)
{
	// Pacing subsystem is optional polish: on a false return the authored
	// duration is used unchanged (same degrade contract as the intro actor).
	float ResolvedDuration = Duration;
	if (UMelodiaPacingSubsystem* Pacing = UMelodiaPacingSubsystem::Get(this))
	{
		Pacing->ResolveDuration(TEXT("BattleArenaBreakDolly"), ResolvedDuration);
	}
	bDollyActive = true;
	DollyTimeLeft = ResolvedDuration;
	TargetFraming = FramingFor(EMelodiaArenaCameraPhase::Break);
	CameraBlendSpeed = ResolvedDuration > KINDA_SMALL_NUMBER ? 2.0f / ResolvedDuration : 100.0f;
	SetActorTickEnabled(true);
}

void AMelodiaBattleArena::Hitstop(const float TimeScale, const float DurationSec)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	const float Now = World->GetRealTimeSeconds();
	if (LastHitstopRealTime >= 0.0f && Now - LastHitstopRealTime < 0.12f)
	{
		return;
	}
	LastHitstopRealTime = Now;
	UGameplayStatics::SetGlobalTimeDilation(World, FMath::Clamp(TimeScale, 0.01f, 1.0f));
	float ResolvedDuration = DurationSec;
	if (UMelodiaPacingSubsystem* Pacing = UMelodiaPacingSubsystem::Get(this))
	{
		Pacing->ResolveDuration(TEXT("BattleArenaHitstop"), ResolvedDuration);
	}
	HitstopTimeLeft = ResolvedDuration; // duration measured in real time (Tick consumes RealDelta)
	SetActorTickEnabled(true);
}

void AMelodiaBattleArena::PlayShake(const float Scale)
{
	APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0);
	if (!PC || !PC->PlayerCameraManager)
	{
		return;
	}
	if (ShakeClass)
	{
		PC->PlayerCameraManager->StartCameraShake(ShakeClass, Scale);
	}
	else
	{
		// Improvised micro-shake: brief random rotational punch on the boom.
		if (CameraBoom)
		{
			const FRotator Punch(FMath::FRandRange(-1.2f, 1.2f) * Scale,
				FMath::FRandRange(-1.6f, 1.6f) * Scale, 0.0f);
			CameraBoom->AddRelativeRotation(Punch);
			SetActorTickEnabled(true); // interp back via framing target
		}
	}
}

void AMelodiaBattleArena::SetTimeDilation(const float Target, const float DurationSec)
{
	DilationTarget = FMath::Clamp(Target, 0.05f, 1.0f);
	DilationTimeLeft = FMath::Max(DurationSec, 0.01f);
	SetActorTickEnabled(true);
}

void AMelodiaBattleArena::PostProcessPop(const float Intensity)
{
	PopLevel = FMath::Max(PopLevel, Intensity);
	if (UMelodiaRhythmReactivitySubsystem* Reactivity = GetWorld() ? GetWorld()->GetSubsystem<UMelodiaRhythmReactivitySubsystem>() : nullptr)
	{
		Reactivity->SetScalarOverride(TEXT("PerfectPop"), PopLevel);
	}
	SetActorTickEnabled(true);
}

void AMelodiaBattleArena::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}
	const float RealDelta = FApp::GetDeltaTime(); // unscaled-ish; hitstop windows are tiny

	bool bAnythingActive = false;

	// Camera framing interp
	CurrentFraming.Offset = FMath::VInterpTo(CurrentFraming.Offset, TargetFraming.Offset, RealDelta, CameraBlendSpeed * 3.0f);
	CurrentFraming.Rotation = FMath::RInterpTo(CurrentFraming.Rotation, TargetFraming.Rotation, RealDelta, CameraBlendSpeed * 3.0f);
	CurrentFraming.ArmLength = FMath::FInterpTo(CurrentFraming.ArmLength, TargetFraming.ArmLength, RealDelta, CameraBlendSpeed * 3.0f);
	CurrentFraming.FOV = FMath::FInterpTo(CurrentFraming.FOV, TargetFraming.FOV, RealDelta, CameraBlendSpeed * 3.0f);
	ApplyFraming(CurrentFraming);
	if (!CurrentFraming.Offset.Equals(TargetFraming.Offset, 1.0f) ||
		!FMath::IsNearlyEqual(CurrentFraming.ArmLength, TargetFraming.ArmLength, 1.0f))
	{
		bAnythingActive = true;
	}

	// Break dolly auto-restore
	if (bDollyActive)
	{
		DollyTimeLeft -= RealDelta;
		bAnythingActive = true;
		if (DollyTimeLeft <= 0.0f)
		{
			bDollyActive = false;
			TargetFraming = FramingFor(CameraPhase);
		}
	}

	// Hitstop restore
	if (HitstopTimeLeft > 0.0f)
	{
		HitstopTimeLeft -= RealDelta;
		bAnythingActive = true;
		if (HitstopTimeLeft <= 0.0f)
		{
			UGameplayStatics::SetGlobalTimeDilation(World, DilationTimeLeft > 0.0f ? DilationTarget : 1.0f);
		}
	}

	// Directed dilation (ult entry etc.)
	if (DilationTimeLeft > 0.0f)
	{
		DilationTimeLeft -= RealDelta;
		bAnythingActive = true;
		const float Current = UGameplayStatics::GetGlobalTimeDilation(World);
		UGameplayStatics::SetGlobalTimeDilation(World, FMath::FInterpTo(Current, DilationTarget, RealDelta, 8.0f));
		if (DilationTimeLeft <= 0.0f)
		{
			UGameplayStatics::SetGlobalTimeDilation(World, 1.0f);
			DilationTarget = 1.0f;
		}
	}

	// PerfectPop decay
	if (PopLevel > 0.0f)
	{
		PopLevel = FMath::Max(0.0f, PopLevel - RealDelta * 5.5f);
		bAnythingActive = PopLevel > 0.0f || bAnythingActive;
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->SetScalarOverride(TEXT("PerfectPop"), PopLevel);
		}
	}

	if (!bAnythingActive)
	{
		SetActorTickEnabled(false);
	}
}

void AMelodiaBattleArena::SetupArena(const FMelodiaEnemyDef& EnemyDef)
{
	ActiveEnemy = EnemyDef;

	// Apply enemy mesh if specified
	if (EnemyMeshComponent && !EnemyDef.DisplayMesh.IsNull())
	{
		if (UStaticMesh* Mesh = EnemyDef.DisplayMesh.LoadSynchronous())
		{
			EnemyMeshComponent->SetStaticMesh(Mesh);
		}
	}

	// Apply material if specified
	if (EnemyMeshComponent && !EnemyDef.DisplayMaterial.IsNull())
	{
		if (UMaterialInterface* Mat = EnemyDef.DisplayMaterial.LoadSynchronous())
		{
			EnemyMeshComponent->SetMaterial(0, Mat);
		}
	}

	// Scale
	if (EnemyMeshComponent)
	{
		EnemyMeshComponent->SetRelativeLocation(EnemySpawnOffset);
		EnemyMeshComponent->SetRelativeScale3D(FVector(EnemyDef.MeshScale));
	}

	// Set combat state element
	if (CombatState)
	{
		CombatState->EnemyElement = EnemyDef.Element;
		CombatState->EnemyToughness = EnemyDef.MaxToughness;
		CombatState->EnemyToughnessMax = EnemyDef.MaxToughness;
	}

	// Set rhythm BPM if overridden
	if (RhythmExecution && EnemyDef.BPMOverride > 0.0f)
	{
		RhythmExecution->BPM = EnemyDef.BPMOverride;
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia Arena: Setup for %s (HP=%.0f, Tough=%.0f, Elem=%d, BPM=%.0f)"),
		*EnemyDef.DisplayName.ToString(), EnemyDef.MaxHP, EnemyDef.MaxToughness,
		static_cast<int32>(EnemyDef.Element), EnemyDef.BPMOverride);
}

void AMelodiaBattleArena::ActivateArena()
{
	bArenaActive = true;

	// Show enemy mesh
	if (EnemyMeshComponent)
	{
		EnemyMeshComponent->SetVisibility(true);
	}

	// Save and move camera
	if (APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0))
	{
		if (APawn* Pawn = PC->GetPawn())
		{
			SavedCameraLocation = Pawn->GetActorLocation();
			SavedCameraRotation = PC->GetControlRotation();
			bCameraSaved = true;
		}

		// Set battle camera
		const FVector CameraTarget = GetActorLocation() + BattleCameraOffset;
		PC->SetControlRotation(BattleCameraRotation);
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia Arena: Activated ΓÇö %s"), *ActiveEnemy.DisplayName.ToString());
}

void AMelodiaBattleArena::DeactivateArena()
{
	bArenaActive = false;

	// Hide enemy mesh
	if (EnemyMeshComponent)
	{
		EnemyMeshComponent->SetVisibility(false);
	}

	// Restore camera
	if (bCameraSaved)
	{
		if (APlayerController* PC = UGameplayStatics::GetPlayerController(GetWorld(), 0))
		{
			PC->SetControlRotation(SavedCameraRotation);
		}
		bCameraSaved = false;
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia Arena: Deactivated"));
}
