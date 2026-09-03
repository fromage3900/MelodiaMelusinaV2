#include "PCGMusicSequencer.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInterface.h"
#include "PCGComponent.h"
#include "PCGGraph.h"
#include "Sound/SoundBase.h"

namespace PCGMusicSequencerPrivate
{
	constexpr int32 StepMask = 0xFF;

	int32 DecodeStep(const int32 Seed)
	{
		return Seed & StepMask;
	}

	int32 DecodeLane(const int32 Seed)
	{
		return (Seed >> 8) & StepMask;
	}
}

APCGMusicStepPad::APCGMusicStepPad()
{
	PrimaryActorTick.bCanEverTick = true;

	USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(SceneRoot);

	PadMeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PadMesh"));
	PadMeshComponent->SetupAttachment(SceneRoot);
	PadMeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PadMeshComponent->SetGenerateOverlapEvents(false);

	PadBlocker = CreateDefaultSubobject<UBoxComponent>(TEXT("PadBlocker"));
	PadBlocker->SetupAttachment(PadMeshComponent);
	PadBlocker->SetBoxExtent(FVector(50.0f, 50.0f, 50.0f));
	PadBlocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	PadBlocker->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	PadBlocker->SetGenerateOverlapEvents(false);

	StepTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("StepTrigger"));
	StepTrigger->SetupAttachment(SceneRoot);
	StepTrigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	StepTrigger->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	StepTrigger->SetGenerateOverlapEvents(true);
	StepTrigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	StepTrigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	StepTrigger->OnComponentBeginOverlap.AddDynamic(this, &APCGMusicStepPad::HandleStepBegin);
	StepTrigger->OnComponentEndOverlap.AddDynamic(this, &APCGMusicStepPad::HandleStepEnd);
}

void APCGMusicStepPad::BeginPlay()
{
	Super::BeginPlay();
	ResolveGrid();
	ApplyProfileGeometry();
}

void APCGMusicStepPad::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (GridOwner.IsValid())
	{
		GridOwner->UnregisterPad(this);
	}
	PressingActors.Reset();
	Super::EndPlay(EndPlayReason);
}

void APCGMusicStepPad::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const UPCGMusicStepGridProfile* GridProfile = GridOwner.IsValid() ? GridOwner->GetProfile() : nullptr;
	const FPCGMusicStepGridDimensions Dimensions = GridProfile ? GridProfile->Dimensions : FPCGMusicStepGridDimensions();
	const float Stiffness = FMath::Max(0.0f, Dimensions.SpringStiffness);
	const float Damping = FMath::Max(0.0f, Dimensions.SpringDamping);
	const float PressDepth = FMath::Max(0.0f, Dimensions.PressDepth);
	const float TargetOffset = bIsPressed ? -PressDepth : 0.0f;

	const float Acceleration = ((TargetOffset - CurrentPressOffset) * Stiffness) - (PressVelocity * Damping);
	PressVelocity += Acceleration * DeltaSeconds;
	CurrentPressOffset += PressVelocity * DeltaSeconds;
	if (FMath::Abs(CurrentPressOffset - TargetOffset) < 0.01f && FMath::Abs(PressVelocity) < 0.01f)
	{
		CurrentPressOffset = TargetOffset;
		PressVelocity = 0.0f;
	}

	if (PadMeshComponent)
	{
		PadMeshComponent->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentPressOffset));
	}
}

void APCGMusicStepPad::InitializeFromPCGPoint(const FPCGPoint Point, const UPCGMetadata* Metadata)
{
	StepIndex = PCGMusicSequencerPrivate::DecodeStep(Point.Seed);
	Lane = PCGMusicSequencerPrivate::DecodeLane(Point.Seed);
	ResolveGrid();
	if (GridOwner.IsValid() && GridOwner->GetProfile())
	{
		const TArray<int32>& LaneNotes = GridOwner->GetProfile()->LaneMidiNotes;
		MidiNote = LaneNotes.IsValidIndex(Lane) ? LaneNotes[Lane] : GridOwner->GetProfile()->FirstMidiNote + Lane;
	}
	else
	{
		MidiNote = 60 + Lane;
	}
	ApplyProfileGeometry();
}

void APCGMusicStepPad::ResolveGrid()
{
	if (GridOwner.IsValid())
	{
		return;
	}

	if (APCGMusicStepGrid* ParentGrid = Cast<APCGMusicStepGrid>(GetAttachParentActor()))
	{
		GridOwner = ParentGrid;
	}
	else if (UWorld* World = GetWorld())
	{
		float BestDistanceSquared = TNumericLimits<float>::Max();
		for (TActorIterator<APCGMusicStepGrid> It(World); It; ++It)
		{
			const float DistanceSquared = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
			if (DistanceSquared < BestDistanceSquared)
			{
				BestDistanceSquared = DistanceSquared;
				GridOwner = *It;
			}
		}
	}

	if (GridOwner.IsValid())
	{
		GridOwner->RegisterPad(this);
	}
}

void APCGMusicStepPad::ApplyProfileGeometry()
{
	const UPCGMusicStepGridProfile* GridProfile = GridOwner.IsValid() ? GridOwner->GetProfile() : nullptr;
	const FPCGMusicStepGridDimensions Dimensions = GridProfile ? GridProfile->Dimensions : FPCGMusicStepGridDimensions();

	if (GridProfile)
	{
		if (UStaticMesh* Mesh = GridProfile->PadMesh.LoadSynchronous())
		{
			PadMeshComponent->SetStaticMesh(Mesh);
		}
		if (UMaterialInterface* Material = GridProfile->PadMaterial.LoadSynchronous())
		{
			PadMeshComponent->SetMaterial(0, Material);
		}
	}
	else if (!PadMeshComponent->GetStaticMesh())
	{
		if (UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")))
		{
			PadMeshComponent->SetStaticMesh(Cube);
		}
	}

	PadMeshComponent->SetRelativeScale3D(FVector(Dimensions.PadWidth / 100.0f, Dimensions.PadDepth / 100.0f, Dimensions.PadHeight / 100.0f));
	StepTrigger->SetBoxExtent(FVector(Dimensions.PadWidth * 0.5f, Dimensions.PadDepth * 0.5f, FMath::Max(1.5f, Dimensions.PressTriggerHeight * 0.5f)));
	StepTrigger->SetRelativeLocation(FVector(0.0f, 0.0f, Dimensions.PadHeight * 0.5f + FMath::Max(1.5f, Dimensions.PressTriggerHeight * 0.5f)));
}

FBox APCGMusicStepPad::GetWorldFootprint() const
{
	return PadBlocker ? PadBlocker->Bounds.GetBox() : FBox(GetActorLocation(), GetActorLocation());
}

void APCGMusicStepPad::SetGrid(APCGMusicStepGrid* InGrid)
{
	GridOwner = InGrid;
}

bool APCGMusicStepPad::IsPlayerControlledPawn(AActor* OtherActor) const
{
	const APawn* Pawn = Cast<APawn>(OtherActor);
	return Pawn && Pawn->IsPlayerControlled();
}

void APCGMusicStepPad::HandleStepBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, const int32 OtherBodyIndex, const bool bFromSweep, const FHitResult& SweepResult)
{
	if (IsPlayerControlledPawn(OtherActor))
	{
		SetPressedForActor(OtherActor, true);
	}
}

void APCGMusicStepPad::HandleStepEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, const int32 OtherBodyIndex)
{
	if (IsPlayerControlledPawn(OtherActor))
	{
		SetPressedForActor(OtherActor, false);
	}
}

void APCGMusicStepPad::SetPressedForActor(AActor* SteppingActor, const bool bPressedForActor)
{
	if (!SteppingActor)
	{
		return;
	}

	const bool bWasPressed = PressingActors.Num() > 0;
	if (bPressedForActor)
	{
		PressingActors.Add(SteppingActor);
	}
	else
	{
		PressingActors.Remove(SteppingActor);
	}
	const bool bNowPressed = PressingActors.Num() > 0;
	if (bWasPressed == bNowPressed)
	{
		return;
	}

	bIsPressed = bNowPressed;
	if (bIsPressed)
	{
		BeginPadPress(SteppingActor);
	}
	else
	{
		EndPadPress(SteppingActor);
	}
}

void APCGMusicStepPad::BeginPadPress(AActor* SteppingActor)
{
	OnStepActivated.Broadcast(StepIndex, Lane, MidiNote, SteppingActor);
	if (GridOwner.IsValid())
	{
		GridOwner->NotifyPadActivated(this, SteppingActor);
	}
}

void APCGMusicStepPad::EndPadPress(AActor* SteppingActor)
{
	OnStepDeactivated.Broadcast(StepIndex, Lane, MidiNote, SteppingActor);
	if (GridOwner.IsValid())
	{
		GridOwner->NotifyPadDeactivated(this, SteppingActor);
	}
}

APCGMusicStepGrid::APCGMusicStepGrid()
{
	PrimaryActorTick.bCanEverTick = false;

	USceneComponent* SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(SceneRoot);
	PCGComponent = CreateDefaultSubobject<UPCGComponent>(TEXT("MusicGridPCG"));
	PCGComponent->SetIsPartitioned(false);
}

void APCGMusicStepGrid::BeginPlay()
{
	Super::BeginPlay();
	if (PCGComponent && MusicGraph)
	{
		PCGComponent->SetGraph(MusicGraph);
	}
}

void APCGMusicStepGrid::RegisterPad(APCGMusicStepPad* Pad)
{
	if (!Pad)
	{
		return;
	}
	RegisteredPads.Add(Pad);
	Pad->SetGrid(this);
	RegisteredPadCount = RegisteredPads.Num();
}

void APCGMusicStepGrid::UnregisterPad(APCGMusicStepPad* Pad)
{
	if (!Pad)
	{
		return;
	}
	RegisteredPads.Remove(Pad);
	RegisteredPadCount = RegisteredPads.Num();
	UpdateActivePadCount();
}

void APCGMusicStepGrid::NotifyPadActivated(APCGMusicStepPad* Pad, AActor* SteppingActor)
{
	if (Pad)
	{
		OnStepActivated.Broadcast(Pad->GetStepIndex(), Pad->GetLane(), Pad->GetMidiNote(), SteppingActor);
		UpdateActivePadCount();
	}
}

void APCGMusicStepGrid::NotifyPadDeactivated(APCGMusicStepPad* Pad, AActor* SteppingActor)
{
	if (Pad)
	{
		OnStepDeactivated.Broadcast(Pad->GetStepIndex(), Pad->GetLane(), Pad->GetMidiNote(), SteppingActor);
		UpdateActivePadCount();
	}
}

void APCGMusicStepGrid::UpdateActivePadCount()
{
	int32 Count = 0;
	for (const TObjectPtr<APCGMusicStepPad> Pad : RegisteredPads)
	{
		if (Pad && Pad->IsPressed())
		{
			++Count;
		}
	}
	ActivePadCount = Count;
}
