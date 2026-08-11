#include "PCGHeroMusic.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInterface.h"
#include "MelodiaAudioComponent.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "../MelodiaIntegration/MelodiaMusicClockSubsystem.h"
#include "PCGComponent.h"
#include "PCGGraph.h"
#include "ProceduralMeshComponent.h"
#include "KismetProceduralMeshLibrary.h"

// Live Coding marker: keep the reflected hero overlap contract synchronized.

namespace PCGHeroMusicPrivate
{
	constexpr int32 MidiMask = 0xFF;
	constexpr int32 LaneMask = 0xFF;

	int32 DecodeNodeIndex(const int32 Seed)
	{
		return (Seed >> 16) & 0xFFFF;
	}

	int32 DecodeLane(const int32 Seed)
	{
		return (Seed >> 8) & LaneMask;
	}

	int32 DecodeMidi(const int32 Seed)
	{
		return Seed & MidiMask;
	}
}

APCGHeroMusicNode::APCGHeroMusicNode()
{
	PrimaryActorTick.bCanEverTick = (true && !false);

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	NodeMeshComponent = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("NodeMesh"));
	NodeMeshComponent->SetupAttachment(Root);
	NodeMeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	NodeMeshComponent->SetGenerateOverlapEvents(false);
	NodeMeshComponent->SetVisibility(false);

	BeveledKeyMeshComponent = CreateDefaultSubobject<UProceduralMeshComponent>(TEXT("BeveledKeyMesh"));
	BeveledKeyMeshComponent->SetupAttachment(Root);
	BeveledKeyMeshComponent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	BeveledKeyMeshComponent->SetGenerateOverlapEvents(false);

	NodeBlocker = CreateDefaultSubobject<UBoxComponent>(TEXT("NodeBlocker"));
	NodeBlocker->SetupAttachment(Root);
	NodeBlocker->SetBoxExtent(FVector(55.0f, 55.0f, 8.0f));
	NodeBlocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	NodeBlocker->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	NodeBlocker->SetGenerateOverlapEvents(false);

	StepTrigger = CreateDefaultSubobject<UBoxComponent>(TEXT("StepTrigger"));
	StepTrigger->SetupAttachment(Root);
	StepTrigger->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	StepTrigger->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	StepTrigger->SetGenerateOverlapEvents(true);
	StepTrigger->SetCollisionResponseToAllChannels(ECR_Ignore);
	StepTrigger->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
}

void APCGHeroMusicNode::BeginPlay()
{
	Super::BeginPlay();
	// Bind only on live instances. Constructor-time dynamic binding also runs
	// for the class default object during module load and can race reflected
	// UFUNCTION registration.
	if (StepTrigger)
	{
		StepTrigger->OnComponentBeginOverlap.AddUniqueDynamic(this, &APCGHeroMusicNode::HandleStepBegin);
		StepTrigger->OnComponentEndOverlap.AddUniqueDynamic(this, &APCGHeroMusicNode::HandleStepEnd);
	}
	ResolveHost();
	ApplyProfileGeometry();

	if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		Reactivity->RegisterReactiveMeshComponent(BeveledKeyMeshComponent);
	}
}

void APCGHeroMusicNode::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (HostOwner.IsValid())
	{
		HostOwner->UnregisterNode(this);
	}
	PressingActors.Reset();
	Super::EndPlay(EndPlayReason);
}

void APCGHeroMusicNode::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const UPCGHeroMusicProfile* HeroProfile = HostOwner.IsValid() ? HostOwner->Profile : nullptr;
	const FPCGHeroMusicNodeDimensions Dimensions = HeroProfile ? HeroProfile->NodeDimensions : FPCGHeroMusicNodeDimensions();
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

	if (NodeMeshComponent)
	{
		NodeMeshComponent->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentPressOffset));
	}
	if (BeveledKeyMeshComponent)
	{
		BeveledKeyMeshComponent->SetRelativeLocation(FVector(0.0f, 0.0f, CurrentPressOffset));
	}
}

void APCGHeroMusicNode::InitializeFromPCGPoint(const FPCGPoint Point, const UPCGMetadata* Metadata)
{
	SeedIdentity = Point.Seed;
	NodeIndex = PCGHeroMusicPrivate::DecodeNodeIndex(Point.Seed);
	Lane = PCGHeroMusicPrivate::DecodeLane(Point.Seed);
	MidiNote = FMath::Clamp(PCGHeroMusicPrivate::DecodeMidi(Point.Seed), 0, 127);
	ResolveHost();
	ApplyProfileGeometry();
}

void APCGHeroMusicNode::ResolveHost()
{
	if (HostOwner.IsValid())
	{
		return;
	}

	if (APCGHeroMusicGraphHost* ParentHost = Cast<APCGHeroMusicGraphHost>(GetAttachParentActor()))
	{
		ParentHost->RegisterNode(this);
		return;
	}

	if (UWorld* World = GetWorld())
	{
		float BestDistanceSquared = TNumericLimits<float>::Max();
		APCGHeroMusicGraphHost* BestHost = nullptr;
		for (TActorIterator<APCGHeroMusicGraphHost> It(World); It; ++It)
		{
			const float DistanceSquared = FVector::DistSquared(GetActorLocation(), It->GetActorLocation());
			if (DistanceSquared < BestDistanceSquared && DistanceSquared <= FMath::Square(5000.0f))
			{
				BestDistanceSquared = DistanceSquared;
				BestHost = *It;
			}
		}
		if (BestHost)
		{
			BestHost->RegisterNode(this);
		}
	}
}

void APCGHeroMusicNode::ApplyProfileGeometry()
{
	const UPCGHeroMusicProfile* HeroProfile = HostOwner.IsValid() ? HostOwner->Profile : nullptr;
	const FPCGHeroMusicNodeDimensions Dimensions = HeroProfile ? HeroProfile->NodeDimensions : FPCGHeroMusicNodeDimensions();
	const bool bBlackPitch = (MidiNote % 12 == 1 || MidiNote % 12 == 3 || MidiNote % 12 == 6 || MidiNote % 12 == 8 || MidiNote % 12 == 10);
	const float KeyWidth = Dimensions.Width * (bBlackPitch ? 0.62f : 1.0f);
	const float KeyDepth = Dimensions.Depth * (bBlackPitch ? 0.76f : 1.0f);
	const float KeyHeight = Dimensions.Height * (bBlackPitch ? 1.18f : 1.0f);
	UMaterialInterface* Material = nullptr;

	if (HeroProfile)
	{
		UStaticMesh* Mesh = bBlackPitch ? HeroProfile->BlackNodeMesh.LoadSynchronous() : HeroProfile->WhiteNodeMesh.LoadSynchronous();
		if (!Mesh)
		{
			Mesh = HeroProfile->NodeMesh.LoadSynchronous();
		}
		if (Mesh)
		{
			NodeMeshComponent->SetStaticMesh(Mesh);
		}
		Material = bBlackPitch ? HeroProfile->BlackNodeMaterial.LoadSynchronous() : HeroProfile->WhiteNodeMaterial.LoadSynchronous();
		if (!Material)
		{
			Material = HeroProfile->NodeMaterial.LoadSynchronous();
		}
		if (Material)
		{
			NodeMeshComponent->SetMaterial(0, Material);
		}
		NodeMeshComponent->SetRenderCustomDepth(HeroProfile->bWriteCustomDepth);
		NodeMeshComponent->SetCustomDepthStencilValue(HeroProfile->CustomDepthStencilValue);
		NodeMeshComponent->SetCullDistance(FMath::Max(0.0f, HeroProfile->InstanceEndCullDistance));
	}
	// Never fall back to an engine cube for hero nodes.  The procedural beveled
	// key below is the visible interaction surface, and authored hero profiles
	// must provide any optional static mesh/material explicitly.

	RebuildBeveledKeyGeometry(KeyWidth, KeyDepth, KeyHeight, Material);
	if (BeveledKeyMeshComponent && HeroProfile)
	{
		BeveledKeyMeshComponent->SetRenderCustomDepth(HeroProfile->bWriteCustomDepth);
		BeveledKeyMeshComponent->SetCustomDepthStencilValue(HeroProfile->CustomDepthStencilValue);
		BeveledKeyMeshComponent->SetCullDistance(FMath::Max(0.0f, HeroProfile->InstanceEndCullDistance));
	}
	NodeMeshComponent->SetRelativeScale3D(FVector(1.0f, 1.0f, 1.0f));
	NodeBlocker->SetBoxExtent(FVector(Dimensions.Width * 0.5f, Dimensions.Depth * 0.5f, FMath::Max(2.0f, Dimensions.Height * 0.5f)));
	StepTrigger->SetBoxExtent(FVector(Dimensions.Width * 0.5f, Dimensions.Depth * 0.5f, FMath::Max(2.0f, Dimensions.PressTriggerHeight * 0.5f)));
	StepTrigger->SetRelativeLocation(FVector(0.0f, 0.0f, Dimensions.Height * 0.5f + FMath::Max(2.0f, Dimensions.PressTriggerHeight * 0.5f)));
}

void APCGHeroMusicNode::RebuildBeveledKeyGeometry(const float Width, const float Depth, const float Height, UMaterialInterface* Material)
{
	if (!BeveledKeyMeshComponent)
	{
		return;
	}

	const float HalfWidth = FMath::Max(1.0f, Width * 0.5f);
	const float HalfDepth = FMath::Max(1.0f, Depth * 0.5f);
	const float Bevel = FMath::Clamp(FMath::Min3(HalfWidth, HalfDepth, Height * 0.5f) * 0.18f, 1.5f, 8.0f);
	TArray<FVector> Vertices;
	TArray<int32> Triangles;
	TArray<FVector2D> UV0;
	TArray<FLinearColor> Colors;

	auto AddRing = [&](const float Z, const float RingHalfWidth, const float RingHalfDepth)
	{
		const FVector Ring[8] = {
			FVector(-RingHalfWidth + Bevel, -RingHalfDepth, Z),
			FVector(RingHalfWidth - Bevel, -RingHalfDepth, Z),
			FVector(RingHalfWidth, -RingHalfDepth + Bevel, Z),
			FVector(RingHalfWidth, RingHalfDepth - Bevel, Z),
			FVector(RingHalfWidth - Bevel, RingHalfDepth, Z),
			FVector(-RingHalfWidth + Bevel, RingHalfDepth, Z),
			FVector(-RingHalfWidth, RingHalfDepth - Bevel, Z),
			FVector(-RingHalfWidth, -RingHalfDepth + Bevel, Z)
		};
		for (const FVector& Vertex : Ring)
		{
			Vertices.Add(Vertex);
			UV0.Add(FVector2D((Vertex.X / (HalfWidth * 2.0f)) + 0.5f, (Vertex.Y / (HalfDepth * 2.0f)) + 0.5f));
			Colors.Add(FLinearColor::White);
		}
	};

	const float HalfHeight = FMath::Max(2.0f, Height * 0.5f);
	AddRing(-HalfHeight, FMath::Max(1.0f, HalfWidth - Bevel), FMath::Max(1.0f, HalfDepth - Bevel));
	AddRing(-HalfHeight + Bevel, HalfWidth, HalfDepth);
	AddRing(HalfHeight - Bevel, HalfWidth, HalfDepth);
	AddRing(HalfHeight, FMath::Max(1.0f, HalfWidth - Bevel), FMath::Max(1.0f, HalfDepth - Bevel));

	for (int32 Ring = 0; Ring < 3; ++Ring)
	{
		for (int32 Side = 0; Side < 8; ++Side)
		{
			const int32 Next = (Side + 1) % 8;
			const int32 A = Ring * 8 + Side;
			const int32 B = Ring * 8 + Next;
			const int32 C = (Ring + 1) * 8 + Next;
			const int32 D = (Ring + 1) * 8 + Side;
			Triangles.Add(A);
			Triangles.Add(B);
			Triangles.Add(C);
			Triangles.Add(A);
			Triangles.Add(C);
			Triangles.Add(D);
		}
	}

	const int32 BottomCenter = Vertices.Add(FVector(0.0f, 0.0f, -HalfHeight));
	UV0.Add(FVector2D(0.5f, 0.5f));
	Colors.Add(FLinearColor::White);
	const int32 TopCenter = Vertices.Add(FVector(0.0f, 0.0f, HalfHeight));
	UV0.Add(FVector2D(0.5f, 0.5f));
	Colors.Add(FLinearColor::White);
	for (int32 Side = 0; Side < 8; ++Side)
	{
		const int32 Next = (Side + 1) % 8;
		Triangles.Add(BottomCenter);
		Triangles.Add(Next);
		Triangles.Add(Side);
		Triangles.Add(TopCenter);
		Triangles.Add(24 + Side);
		Triangles.Add(24 + Next);
	}

	TArray<FVector> Normals;
	TArray<FProcMeshTangent> Tangents;
	UKismetProceduralMeshLibrary::CalculateTangentsForMesh(Vertices, Triangles, UV0, Normals, Tangents);
	BeveledKeyMeshComponent->ClearAllMeshSections();
	BeveledKeyMeshComponent->CreateMeshSection_LinearColor(0, Vertices, Triangles, Normals, UV0, Colors, Tangents, true);
	BeveledKeyMeshComponent->SetMaterial(0, Material);
	BeveledKeyMeshComponent->SetVisibility(true);
	BeveledKeyMeshComponent->SetRelativeScale3D(FVector(1.0f, 1.0f, 1.0f));
}

void APCGHeroMusicNode::SetHost(APCGHeroMusicGraphHost* InHost)
{
	if (HostOwner.Get() == InHost)
	{
		return;
	}

	if (HostOwner.IsValid())
	{
		HostOwner->UnregisterNode(this);
	}
	HostOwner = InHost;
	ApplyProfileGeometry();
}

bool APCGHeroMusicNode::IsPlayerControlledPawn(AActor* OtherActor) const
{
	const APawn* Pawn = Cast<APawn>(OtherActor);
	return Pawn && Pawn->IsPlayerControlled();
}

void APCGHeroMusicNode::HandleStepBegin(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, const int32 OtherBodyIndex, const bool bFromSweep, const FHitResult& SweepResult)
{
	if (IsPlayerControlledPawn(OtherActor))
	{
		SetPressedForActor(OtherActor, true);
	}
}

void APCGHeroMusicNode::HandleStepEnd(UPrimitiveComponent* OverlappedComponent, AActor* OtherActor, UPrimitiveComponent* OtherComp, const int32 OtherBodyIndex)
{
	if (IsPlayerControlledPawn(OtherActor))
	{
		SetPressedForActor(OtherActor, false);
	}
}

void APCGHeroMusicNode::SetPressedForActor(AActor* SteppingActor, const bool bPressedForActor)
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
		BeginNodePress(SteppingActor);
	}
	else
	{
		EndNodePress(SteppingActor);
	}
}

void APCGHeroMusicNode::BeginNodePress(AActor* SteppingActor)
{
	FPCGHeroMusicNoteEvent Event;
	Event.NodeIndex = NodeIndex;
	Event.Lane = Lane;
	Event.MidiNote = MidiNote;
	Event.InteractingActor = SteppingActor;

	const UPCGHeroMusicProfile* HeroProfile = HostOwner.IsValid() ? HostOwner->Profile : nullptr;
	const FMelodiaRhythmWindows Windows = HeroProfile ? HeroProfile->RhythmWindows : FMelodiaRhythmWindows();
	if (const UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(this); Clock && Clock->HasMusicalTime())
	{
		Event.TimingErrorMs = Clock->GetTimingErrorMsToNearestBeat();
		Event.Grade = UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(Event.TimingErrorMs, Windows).Grade;
	}
	else
	{
		// A proof level remains traversable without an active clock. Good is the
		// neutral local grade; no synthetic clock or wall-clock scorer is created.
		Event.TimingErrorMs = 0.0f;
		Event.Grade = EMelodiaRhythmGrade::Good;
	}

	OnNoteActivated.Broadcast(Event);
}

void APCGHeroMusicNode::EndNodePress(AActor* SteppingActor)
{
	FPCGHeroMusicNoteEvent Event;
	Event.NodeIndex = NodeIndex;
	Event.Lane = Lane;
	Event.MidiNote = MidiNote;
	Event.Grade = EMelodiaRhythmGrade::Good;
	Event.InteractingActor = SteppingActor;
	OnNoteDeactivated.Broadcast(Event);
}

APCGHeroMusicGraphHost::APCGHeroMusicGraphHost()
{
	PrimaryActorTick.bCanEverTick = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	PCGComponent = CreateDefaultSubobject<UPCGComponent>(TEXT("HeroMusicPCG"));
	PCGComponent->SetIsPartitioned(false);

	GenerationBounds = CreateDefaultSubobject<UBoxComponent>(TEXT("GenerationBounds"));
	GenerationBounds->SetupAttachment(Root);
	GenerationBounds->SetBoxExtent(FVector(5000.0f, 5000.0f, 5000.0f));
	GenerationBounds->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	GenerationBounds->SetGenerateOverlapEvents(false);
	GenerationBounds->SetHiddenInGame(true);
	GenerationBounds->SetVisibility(false);

	AudioComponent = CreateDefaultSubobject<UMelodiaAudioComponent>(TEXT("HeroMusicAudio"));
}

void APCGHeroMusicGraphHost::BeginPlay()
{
	Super::BeginPlay();
	ScoreState = FPCGHeroMusicScoreState();
	ScoreState.TotalNotes = Profile ? FMath::Max(0, Profile->ExpectedNoteCount) : 0;

	if (PCGComponent && MusicGraph)
	{
		PCGComponent->SetGraph(MusicGraph);
		PCGComponent->Generate(true);
	}

	if (UWorld* World = GetWorld())
	{
		for (TActorIterator<APCGHeroMusicNode> It(World); It; ++It)
		{
			APCGHeroMusicNode* Node = *It;
			if (Node && (Node->GetHost() == this || Node->GetOwner() == this || Node->GetAttachParentActor() == this))
			{
				RegisterNode(Node);
			}
		}
	}
}

void APCGHeroMusicGraphHost::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	for (const TObjectPtr<APCGHeroMusicNode> Node : RegisteredNodes)
	{
		if (Node)
		{
			Node->OnNoteActivated.RemoveDynamic(this, &APCGHeroMusicGraphHost::HandleNodeActivated);
		}
	}
	RegisteredNodes.Reset();
	Super::EndPlay(EndPlayReason);
}

void APCGHeroMusicGraphHost::RegisterNode(APCGHeroMusicNode* Node)
{
	if (!Node || RegisteredNodes.Contains(Node))
	{
		return;
	}
	if (Node->GetHost() && Node->GetHost() != this)
	{
		return;
	}

	RegisteredNodes.Add(Node);
	Node->SetHost(this);
	Node->OnNoteActivated.AddDynamic(this, &APCGHeroMusicGraphHost::HandleNodeActivated);
	if (ScoreState.TotalNotes <= 0)
	{
		ScoreState.TotalNotes = RegisteredNodes.Num();
	}
}

void APCGHeroMusicGraphHost::UnregisterNode(APCGHeroMusicNode* Node)
{
	if (!Node)
	{
		return;
	}
	Node->OnNoteActivated.RemoveDynamic(this, &APCGHeroMusicGraphHost::HandleNodeActivated);
	RegisteredNodes.Remove(Node);
}

void APCGHeroMusicGraphHost::HandleNodeActivated(const FPCGHeroMusicNoteEvent Event)
{
	if (AudioComponent)
	{
		AudioComponent->PlayMusicalNote(Event.MidiNote, 0.18f, Event.Grade == EMelodiaRhythmGrade::Perfect ? 1.0f : 0.75f);
		if (Profile && Profile->bPlayGradeFeedbackSFX)
		{
			if (Event.Grade == EMelodiaRhythmGrade::Miss)
			{
				AudioComponent->PlayMissSFX();
			}
			else
			{
				AudioComponent->PlayHitSFX(Event.Grade);
			}
		}
	}

	ApplyNoteToScore(Event);
	HandleProgressionEvent(Event);
	OnNoteJudged.Broadcast(Event);
}

void APCGHeroMusicGraphHost::ApplyNoteToScore(const FPCGHeroMusicNoteEvent& Event)
{
	float PresentationScalar = 0.0f;
	switch (Event.Grade)
	{
	case EMelodiaRhythmGrade::Perfect:
		PresentationScalar = 1.0f;
		break;
	case EMelodiaRhythmGrade::Great:
		PresentationScalar = 0.8f;
		break;
	case EMelodiaRhythmGrade::Good:
		PresentationScalar = 0.6f;
		break;
	default:
		break;
	}

	if (Event.Grade == EMelodiaRhythmGrade::Miss)
	{
		++ScoreState.MissCount;
		ScoreState.Streak = 0;
	}
	else
	{
		++ScoreState.HitCount;
		++ScoreState.Streak;
		if (Event.Grade == EMelodiaRhythmGrade::Perfect)
		{
			++ScoreState.PerfectCount;
		}

		int32 BasePoints = 50;
		switch (Event.Grade)
		{
		case EMelodiaRhythmGrade::Perfect:
			BasePoints = 100;
			break;
		case EMelodiaRhythmGrade::Great:
			BasePoints = 75;
			break;
		default:
			break;
		}
		ScoreState.Score += BasePoints + FMath::Max(0, ScoreState.Streak - 1) * 10;
	}

	if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		const int32 JudgedNotes = ScoreState.HitCount + ScoreState.MissCount;
		const float Accuracy = JudgedNotes > 0 ? static_cast<float>(ScoreState.HitCount) / static_cast<float>(JudgedNotes) : 0.0f;
		const float ComboNormalized = FMath::Clamp(static_cast<float>(ScoreState.Streak) / 12.0f, 0.0f, 1.0f);
		Reactivity->NotifyCommandResolved(Event.Grade, PresentationScalar, ComboNormalized, Accuracy, 0);
	}
}

void APCGHeroMusicGraphHost::RecordProgressionMiss()
{
	++ScoreState.MissCount;
	ScoreState.Streak = 0;
}

bool APCGHeroMusicGraphHost::TryGetCurrentMusicBeat(double& OutBeat) const
{
	const UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(this);
	if (!Clock || !Clock->HasMusicalTime())
	{
		return false;
	}

	const FMelodiaMusicTime Time = Clock->GetMusicTime(UMelodiaMusicClockSubsystem::InputTimebase);
	if (!Time.bValid)
	{
		return false;
	}
	OutBeat = static_cast<double>(Time.TotalBeats);
	return true;
}

void APCGHeroMusicGraphHost::MarkCompleted()
{
	if (ScoreState.bCompleted)
	{
		return;
	}
	ScoreState.bCompleted = true;
	OnPatternCompleted.Broadcast();
	ApplyCrescendoResponse();
}

void APCGHeroMusicGraphHost::ApplyCrescendoResponse()
{
	if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		// Presentation-only: the existing reactivity subsystem owns the shared
		// material bus and never enters the combat or damage pipeline.
		Reactivity->NotifyVictory();
	}
}

void APCGHeroMusicGraphHost::HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event)
{
}

APCGResonanceCathedralHost::APCGResonanceCathedralHost()
{
	StationCount = 4;
}

void APCGResonanceCathedralHost::HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event)
{
	if (ScoreState.bCompleted)
	{
		return;
	}

	const int32 RequiredStations = Profile ? FMath::Max(1, Profile->ExpectedNoteCount / 3) : FMath::Max(1, StationCount);
	const int32 Station = Event.NodeIndex >= 0 ? Event.NodeIndex / 3 : INDEX_NONE;
	const int32 Degree = Event.Lane;
	if (Station != ActiveStation)
	{
		if (Event.Grade != EMelodiaRhythmGrade::Miss)
		{
			RecordProgressionMiss();
		}
		ExpectedDegree = 0;
		bHasStationStartBeat = false;
		return;
	}

	double CurrentBeat = 0.0;
	if (TryGetCurrentMusicBeat(CurrentBeat))
	{
		if (!bHasStationStartBeat)
		{
			StationStartBeat = CurrentBeat;
			bHasStationStartBeat = true;
		}
		else if (CurrentBeat - StationStartBeat > static_cast<double>(Profile ? FMath::Max(0.0f, Profile->BeatWindowBeats) : 2.0f))
		{
			if (Event.Grade != EMelodiaRhythmGrade::Miss)
			{
				RecordProgressionMiss();
			}
			ExpectedDegree = 0;
			StationStartBeat = CurrentBeat;
			return;
		}
	}

	if (Event.Grade == EMelodiaRhythmGrade::Miss)
	{
		ExpectedDegree = 0;
		bHasStationStartBeat = false;
		return;
	}

	if (Degree != ExpectedDegree)
	{
		RecordProgressionMiss();
		ExpectedDegree = 0;
		bHasStationStartBeat = false;
		return;
	}

	++ExpectedDegree;
	if (ExpectedDegree < 3)
	{
		return;
	}

	OnStationCompleted.Broadcast(ActiveStation);
	++ActiveStation;
	ExpectedDegree = 0;
	bHasStationStartBeat = false;
	if (ActiveStation >= RequiredStations)
	{
		MarkCompleted();
		OnCathedralCompleted.Broadcast();
	}
}

APCGArpeggioBridgeHost::APCGArpeggioBridgeHost()
{
	NoteCount = 24;
}

void APCGArpeggioBridgeHost::HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event)
{
	if (ScoreState.bCompleted)
	{
		return;
	}

	const int32 RequiredNotes = Profile ? FMath::Max(1, Profile->ExpectedNoteCount) : FMath::Max(1, NoteCount);
	if (Event.Grade == EMelodiaRhythmGrade::Miss)
	{
		return;
	}

	if (Event.NodeIndex != ExpectedNodeIndex)
	{
		RecordProgressionMiss();
		return;
	}

	++ExpectedNodeIndex;
	if (ExpectedNodeIndex >= RequiredNotes)
	{
		MarkCompleted();
		if (CompletionGate)
		{
			CompletionGate->SetActorHiddenInGame(false);
		}
		OnBridgeCompleted.Broadcast();
	}
}

APCGBellTreeGardenNode::APCGBellTreeGardenNode()
{
	// The base actor owns the canonical overlap/press contract. This subclass
	// only replaces the visible presentation geometry with a lathed bell body.
	PrimaryActorTick.bCanEverTick = true;
}

void APCGBellTreeGardenNode::ApplyProfileGeometry()
{
	const UPCGHeroMusicProfile* HeroProfile = GetHost() ? GetHost()->Profile : nullptr;
	const FPCGHeroMusicNodeDimensions Dimensions = HeroProfile
		? HeroProfile->NodeDimensions
		: FPCGHeroMusicNodeDimensions();

	UMaterialInterface* Material = nullptr;
	if (HeroProfile)
	{
		Material = HeroProfile->NodeMaterial.LoadSynchronous();
		if (!Material)
		{
			Material = HeroProfile->WhiteNodeMaterial.LoadSynchronous();
		}
	}

	RebuildBellGeometry(Dimensions.Width, Dimensions.Depth, Dimensions.Height, Material);
	if (BeveledKeyMeshComponent && HeroProfile)
	{
		BeveledKeyMeshComponent->SetRenderCustomDepth(HeroProfile->bWriteCustomDepth);
		BeveledKeyMeshComponent->SetCustomDepthStencilValue(HeroProfile->CustomDepthStencilValue);
		BeveledKeyMeshComponent->SetCullDistance(FMath::Max(0.0f, HeroProfile->InstanceEndCullDistance));
	}
}

void APCGBellTreeGardenNode::RebuildBellGeometry(
	const float Width,
	const float Depth,
	const float Height,
	UMaterialInterface* Material)
{
	if (!BeveledKeyMeshComponent)
	{
		return;
	}

	// This is a real lathed bell profile rather than a scaled cube. The lower
	// lip is deliberately wider than the shoulder, and the upper rings taper
	// into a neck so the instrument reads as a suspended bell at gameplay scale.
	constexpr int32 RadialSegments = 32;
	const float BellHeight = FMath::Max(80.0f, Height * 3.4f);
	const float Radius = FMath::Max(24.0f, FMath::Min(Width, Depth) * 0.52f);
	const float Suspension = FMath::Max(80.0f, Height * 1.8f);
	const float RingZ[] = { 0.00f, 0.06f, 0.16f, 0.34f, 0.56f, 0.76f, 0.91f, 1.00f };
	const float RingRadius[] = { 0.86f, 0.96f, 0.88f, 0.73f, 0.56f, 0.40f, 0.30f, 0.22f };
	constexpr int32 RingCount = UE_ARRAY_COUNT(RingZ);

	TArray<FVector> Vertices;
	TArray<int32> Triangles;
	TArray<FVector2D> UV0;
	TArray<FLinearColor> Colors;

	for (int32 RingIndex = 0; RingIndex < RingCount; ++RingIndex)
	{
		const float Z = Suspension + RingZ[RingIndex] * BellHeight;
		const float RingRadiusValue = Radius * RingRadius[RingIndex];
		for (int32 Side = 0; Side < RadialSegments; ++Side)
		{
			const float Angle = 2.0f * PI * static_cast<float>(Side) / static_cast<float>(RadialSegments);
			const float X = FMath::Cos(Angle) * RingRadiusValue;
			const float Y = FMath::Sin(Angle) * RingRadiusValue;
			Vertices.Add(FVector(X, Y, Z));
			UV0.Add(FVector2D(static_cast<float>(Side) / static_cast<float>(RadialSegments), RingZ[RingIndex]));
			Colors.Add(FLinearColor::White);
		}
	}

	for (int32 RingIndex = 0; RingIndex < RingCount - 1; ++RingIndex)
	{
		for (int32 Side = 0; Side < RadialSegments; ++Side)
		{
			const int32 Next = (Side + 1) % RadialSegments;
			const int32 A = RingIndex * RadialSegments + Side;
			const int32 B = RingIndex * RadialSegments + Next;
			const int32 C = (RingIndex + 1) * RadialSegments + Next;
			const int32 D = (RingIndex + 1) * RadialSegments + Side;
			Triangles.Add(A);
			Triangles.Add(B);
			Triangles.Add(C);
			Triangles.Add(A);
			Triangles.Add(C);
			Triangles.Add(D);
		}
	}

	const int32 BottomCenter = Vertices.Add(FVector(0.0f, 0.0f, Suspension));
	UV0.Add(FVector2D(0.5f, 0.0f));
	Colors.Add(FLinearColor::White);
	const int32 TopCenter = Vertices.Add(FVector(0.0f, 0.0f, Suspension + BellHeight));
	UV0.Add(FVector2D(0.5f, 1.0f));
	Colors.Add(FLinearColor::White);

	for (int32 Side = 0; Side < RadialSegments; ++Side)
	{
		const int32 Next = (Side + 1) % RadialSegments;
		Triangles.Add(BottomCenter);
		Triangles.Add(Next);
		Triangles.Add(Side);
		const int32 TopStart = (RingCount - 1) * RadialSegments;
		Triangles.Add(TopCenter);
		Triangles.Add(TopStart + Side);
		Triangles.Add(TopStart + Next);
	}

	TArray<FVector> Normals;
	TArray<FProcMeshTangent> Tangents;
	UKismetProceduralMeshLibrary::CalculateTangentsForMesh(Vertices, Triangles, UV0, Normals, Tangents);
	BeveledKeyMeshComponent->ClearAllMeshSections();
	BeveledKeyMeshComponent->CreateMeshSection_LinearColor(
		0, Vertices, Triangles, Normals, UV0, Colors, Tangents, false);
	BeveledKeyMeshComponent->SetMaterial(0, Material);
	BeveledKeyMeshComponent->SetVisibility(true);
	BeveledKeyMeshComponent->SetRelativeScale3D(FVector(1.0f, 1.0f, 1.0f));
}

APCGBellTreeGardenHost::APCGBellTreeGardenHost()
{
	BellCount = 18;
	BranchCount = 3;
}

void APCGBellTreeGardenHost::HandleProgressionEvent(const FPCGHeroMusicNoteEvent& Event)
{
	if (ScoreState.bCompleted || Event.Grade == EMelodiaRhythmGrade::Miss)
	{
		return;
	}

	const int32 RequiredBells = Profile
		? FMath::Max(1, Profile->ExpectedNoteCount)
		: FMath::Max(1, BellCount);
	if (Event.NodeIndex != ExpectedBellIndex)
	{
		// The garden remains traversable after a wrong bell. The shared score
		// contract has already reset the streak; progression simply waits for
		// the next correct bell in the deterministic sequence.
		return;
	}

	++ExpectedBellIndex;
	if (ExpectedBellIndex >= RequiredBells)
	{
		MarkCompleted();
		OnGardenCompleted.Broadcast();
	}
}
