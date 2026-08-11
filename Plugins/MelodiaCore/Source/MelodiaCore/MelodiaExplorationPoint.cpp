#include "MelodiaExplorationPoint.h"

#include "Components/SphereComponent.h"
#include "GameFramework/Pawn.h"
#include "MelodiaOpeningFlowSubsystem.h"

AMelodiaExplorationPoint::AMelodiaExplorationPoint()
{
	PrimaryActorTick.bCanEverTick = false;

	Trigger = CreateDefaultSubobject<USphereComponent>(TEXT("Trigger"));
	SetRootComponent(Trigger);
	Trigger->SetSphereRadius(120.0f);
	Trigger->SetCollisionProfileName(TEXT("Trigger"));
	Trigger->SetGenerateOverlapEvents(true);
}

void AMelodiaExplorationPoint::BeginPlay()
{
	Super::BeginPlay();
	Trigger->OnComponentBeginOverlap.AddDynamic(this, &AMelodiaExplorationPoint::HandleOverlap);

	if (PointId.IsNone())
	{
		UE_LOG(LogTemp, Warning,
			TEXT("MELUSINA_EXPLORE: %s has no PointId set -- it will never register as visited."),
			*GetNameSafe(this));
	}
}

void AMelodiaExplorationPoint::HandleOverlap(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor,
	UPrimitiveComponent* OtherComp, int32 OtherBodyIndex, bool bFromSweep, const FHitResult& SweepResult)
{
	if (bVisited)
	{
		return;
	}

	const APawn* Pawn = Cast<APawn>(OtherActor);
	if (!Pawn || !Pawn->IsPlayerControlled())
	{
		return;
	}

	UMelodiaOpeningFlowSubsystem* Flow = UMelodiaOpeningFlowSubsystem::Get(this);
	if (!Flow)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELUSINA_EXPLORE point=%s: no opening-flow subsystem found."), *PointId.ToString());
		return;
	}

	if (Flow->NotifyExplorationPointVisited(PointId))
	{
		bVisited = true;
		UE_LOG(LogTemp, Log, TEXT("MELUSINA_EXPLORE point=%s visited=%d"),
			*PointId.ToString(), Flow->GetExplorationPointsVisited());
	}
	// A false return means either the phase wasn't Morning (log would be noise on
	// replay/other levels reusing this actor) or this PointId was already recorded
	// by another placed instance sharing the same Id -- also not worth logging.
}
