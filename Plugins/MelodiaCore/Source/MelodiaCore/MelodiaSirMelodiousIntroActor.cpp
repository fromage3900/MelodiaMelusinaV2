#include "MelodiaSirMelodiousIntroActor.h"

#include "Components/SkeletalMeshComponent.h"
#include "Components/SphereComponent.h"
#include "Components/PointLightComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "MelodiaAuthorityLocator.h"
#include "MelodiaOpeningStateAnchor.h"
#include "MelodiaOpeningStateComponent.h"
#include "MelodiaOpeningFlowSubsystem.h"
#include "MelodiaPacingSubsystem.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

AMelodiaSirMelodiousIntroActor::AMelodiaSirMelodiousIntroActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;
	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	ReunionTrigger = CreateDefaultSubobject<USphereComponent>(TEXT("ReunionTrigger"));
	ReunionTrigger->SetupAttachment(Root);
	ReunionTrigger->SetSphereRadius(165.0f);
	ReunionTrigger->SetCollisionProfileName(TEXT("Trigger"));
	ReunionTrigger->SetGenerateOverlapEvents(true);
	ReunionLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("ReunionLight"));
	ReunionLight->SetupAttachment(Root);
	ReunionLight->SetRelativeLocation(FVector(0.0f, 0.0f, 65.0f));
	ReunionLight->SetLightColor(FLinearColor(0.35f, 0.86f, 1.0f));
	ReunionLight->SetIntensity(1150.0f);
	ReunionLight->SetAttenuationRadius(380.0f);
	ReunionLight->SetCastShadows(false);
	ReunionLight->SetVisibility(false);

	// The armature-bearing delivery is authoritative. Keep the earlier component
	// assembly below solely as a recovery fallback for an incomplete checkout.
	ConstructorHelpers::FObjectFinder<USkeletalMesh> RiggedMeshFinder(
		TEXT("/Game/Melodia/Characters/SirMelodious/Rigged/SK_SirMelodious_Rigged.SK_SirMelodious_Rigged"));
	if (RiggedMeshFinder.Succeeded())
	{
		USkeletalMeshComponent* RiggedComponent = CreateDefaultSubobject<USkeletalMeshComponent>(TEXT("SirMelodiousRigged"));
		RiggedComponent->SetupAttachment(Root);
		RiggedComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		RiggedComponent->SetCastShadow(true);
		RiggedComponent->SetSkeletalMesh(RiggedMeshFinder.Object);
		PresentationMeshes.Add(RiggedComponent);
		return;
	}

	const TArray<FString> MeshPaths = {
		TEXT("/Game/Melodia/Characters/SirMelodious/B├⌐zierCurve_001.B├⌐zierCurve_001"),
		TEXT("/Game/Melodia/Characters/SirMelodious/Retopo_Cube_001.Retopo_Cube_001"),
		TEXT("/Game/Melodia/Characters/SirMelodious/Retopo_PM3D_Cube3D1_011.Retopo_PM3D_Cube3D1_011"),
		TEXT("/Game/Melodia/Characters/SirMelodious/Retopo_PM3D_Cube3D25.Retopo_PM3D_Cube3D25"),
		TEXT("/Game/Melodia/Characters/SirMelodious/Retopo_PM3D_Cube3D27.Retopo_PM3D_Cube3D27"),
		TEXT("/Game/Melodia/Characters/SirMelodious/Retopo_PM3D_Ring3D2_001.Retopo_PM3D_Ring3D2_001"),
		TEXT("/Game/Melodia/Characters/SirMelodious/Retopo_PM3D_Ring3D2_1_001.Retopo_PM3D_Ring3D2_1_001")
	};

	for (int32 Index = 0; Index < MeshPaths.Num(); ++Index)
	{
		USkeletalMeshComponent* MeshComponent = CreateDefaultSubobject<USkeletalMeshComponent>(*FString::Printf(TEXT("SirMelodiousPart_%02d"), Index));
		MeshComponent->SetupAttachment(Root);
		MeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		MeshComponent->SetCastShadow(true);

		ConstructorHelpers::FObjectFinder<USkeletalMesh> MeshFinder(*MeshPaths[Index]);
		if (MeshFinder.Succeeded())
		{
			MeshComponent->SetSkeletalMesh(MeshFinder.Object);
		}

		PresentationMeshes.Add(MeshComponent);
	}
}

void AMelodiaSirMelodiousIntroActor::BeginPlay()
{
	Super::BeginPlay();
	ReunionTrigger->OnComponentBeginOverlap.AddDynamic(this, &AMelodiaSirMelodiousIntroActor::HandleReunionOverlap);
	if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
	{
		Flow->BeginMorning();
	}
}

void AMelodiaSirMelodiousIntroActor::HandleReunionOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (!bEnableReunionBeat || bReunionTriggered)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: HandleReunionOverlap early-out (bEnableReunionBeat=%d, bReunionTriggered=%d)"),
			bEnableReunionBeat, bReunionTriggered);
		return;
	}

	APawn* Pawn = Cast<APawn>(OtherActor);
	if (!Pawn || !Pawn->IsPlayerControlled())
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: HandleReunionOverlap ignored overlap from non-player-pawn actor '%s'"),
			*GetNameSafe(OtherActor));
		return;
	}

	if (RequiredExplorationPoints > 0)
	{
		UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this);
		const int32 Visited = Flow ? Flow->GetExplorationPointsVisited() : 0;
		if (Visited < RequiredExplorationPoints)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("MELUSINA_DEPARTURE: HandleReunionOverlap gated -- explored %d/%d required points, reunion beat withheld"),
				Visited, RequiredExplorationPoints);
			return;
		}
	}

	bool bFoundBond = false;
	for (TActorIterator<AMelodiaOpeningStateAnchor> It(GetWorld()); It; ++It)
	{
		if (UMelodiaResonanceBondComponent* Bond = It->ResonanceBond)
		{
			bFoundBond = true;
			Bond->SetBondState(EMelodiaResonanceBondState::Reunited);
			ReunionLight->SetVisibility(true);
			bReunionTriggered = true;
			UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: HandleReunionOverlap triggered reunion, bDepartAfterReunion=%d"),
				bDepartAfterReunion);
			if (bDepartAfterReunion)
			{
				// Existing Blueprint instances may retain this legacy serialized value.
				// Never let overlap bypass Quill: the final dialogue command is the sole
				// authority allowed to call BeginWindowDeparture().
				UE_LOG(LogTemp, Error,
					TEXT("MELUSINA_DEPARTURE: legacy bDepartAfterReunion=true ignored; waiting for dialogue completion"));
			}
		}
		break;
	}

	if (!bFoundBond)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: HandleReunionOverlap found no valid ResonanceBond on state anchor; reunion not triggered"));
	}
}

void AMelodiaSirMelodiousIntroActor::UpdateDissonanceFromDistance(const FVector& SirLocation) const
{
	const APawn* PlayerPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!PlayerPawn)
	{
		return;
	}

	// "Losing power because she's away from her companion": procs from actual
	// distance to Sir as he flies off, not a fixed narrative trigger volume.
	const float MaxDistance = FMath::Max(1.0f, DepartureOffset.Size());
	const float DistanceRatio = FMath::Clamp(FVector::Dist(SirLocation, PlayerPawn->GetActorLocation()) / MaxDistance, 0.0f, 1.0f);

	EMelodiaDissonanceTier Tier = EMelodiaDissonanceTier::Clear;
	if (DistanceRatio >= RuptureDistanceRatio)
	{
		Tier = EMelodiaDissonanceTier::Rupture;
	}
	else if (DistanceRatio >= StrainDistanceRatio)
	{
		Tier = EMelodiaDissonanceTier::Strain;
	}
	const float Scalar = FMath::Clamp(1.0f - DistanceRatio, MinSongcraftScalar, 1.0f);

	for (TActorIterator<AMelodiaOpeningStateAnchor> It(GetWorld()); It; ++It)
	{
		if (UMelodiaDissonanceComponent* Dissonance = It->Dissonance)
		{
			Dissonance->SetDissonanceTier(Tier, Scalar);
		}
		break;
	}
}

void AMelodiaSirMelodiousIntroActor::HandleDepartureDelayElapsed()
{
	BeginWindowDeparture();
}

bool AMelodiaSirMelodiousIntroActor::BeginWindowDeparture()
{
	if (!bReunionTriggered || bDepartureActive || bDepartureCompleted)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: BeginWindowDeparture early-out (bReunionTriggered=%d, bDepartureActive=%d, bDepartureCompleted=%d)"),
			bReunionTriggered, bDepartureActive, bDepartureCompleted);
		return false;
	}

	UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this);
	if (!Flow)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: BeginWindowDeparture failed - UMelodiaOpeningFlowSubsystem not found"));
		return false;
	}
	if (!Flow->NotifySirDeparted())
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: BeginWindowDeparture failed - NotifySirDeparted() returned false (opening-flow phase was not Morning)"));
		return false;
	}

	UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: BeginWindowDeparture succeeded, departure now active"));

	DepartureStartLocation = GetActorLocation();
	DepartureElapsed = 0.0f;
	bDepartureActive = true;

	// Resolved once here, not per-Tick: the duration must stay constant for the
	// whole arc. Same optional-polish/fallback contract as the delay above.
	ResolvedDepartureDurationSeconds = DepartureDurationSeconds;
	if (UMelodiaPacingSubsystem* Pacing = UMelodiaPacingSubsystem::Get(this))
	{
		Pacing->ResolveDuration(TEXT("MorningDepartureDuration"), ResolvedDepartureDurationSeconds);
	}
	ReunionTrigger->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	ReunionLight->SetVisibility(false);
	SetActorTickEnabled(true);
	return true;
}

void AMelodiaSirMelodiousIntroActor::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bDepartureActive)
	{
		return;
	}

	DepartureElapsed += DeltaSeconds;
	const float Alpha = FMath::Clamp(DepartureElapsed / FMath::Max(0.1f, ResolvedDepartureDurationSeconds), 0.0f, 1.0f);
	const float SmoothedAlpha = FMath::SmoothStep(0.0f, 1.0f, Alpha);
	FVector Location = FMath::Lerp(DepartureStartLocation, DepartureStartLocation + DepartureOffset, SmoothedAlpha);
	Location.Z += FMath::Sin(Alpha * PI) * 80.0f;
	SetActorLocation(Location);
	SetActorRotation(DepartureOffset.Rotation());
	UpdateDissonanceFromDistance(Location);

	if (Alpha >= 1.0f)
	{
		bDepartureActive = false;
		bDepartureCompleted = true;
		SetActorTickEnabled(false);
		if (UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this))
		{
			Flow->NotifyDreamstateEntered();
		}

		// Routed through the authority locator (Stage C, 2026-07-31) instead of a bare
		// OpenLevel -- this actor is MelodiaCore-native and cannot reach
		// UMelodiaTravelSubsystem directly (see MelodiaSharedAuthorityInterfaces.h for
		// why). Falls back to the old direct OpenLevel only if no travel provider has
		// registered, so a missing/misconfigured GameInstance subsystem degrades
		// instead of stranding the player mid-departure.
		bool bRoutedThroughAuthority = false;
		if (UMelodiaAuthorityLocator* Locator = UMelodiaAuthorityLocator::Get(this))
		{
			TScriptInterface<IMelodiaTravelProvider> Travel = Locator->GetTravelProvider();
			if (Travel.GetObject())
			{
				UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: Departure animation complete, routing TravelTo(%s) via authority locator"),
					*DepartureDestinationLevel.ToString());
				bRoutedThroughAuthority = Travel->TravelTo(DepartureDestinationLevel, NAME_None);
			}
		}

		if (!bRoutedThroughAuthority)
		{
			UE_LOG(LogTemp, Warning, TEXT("MELUSINA_DEPARTURE: no travel provider registered, falling back to direct OpenLevel(%s)"),
				*DepartureDestinationLevel.ToString());
			UGameplayStatics::OpenLevel(this, DepartureDestinationLevel);
		}
	}
}
