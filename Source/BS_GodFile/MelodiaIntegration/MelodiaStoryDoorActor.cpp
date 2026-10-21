#include "MelodiaStoryDoorActor.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UObject/ConstructorHelpers.h"

AMelodiaStoryDoorActor::AMelodiaStoryDoorActor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Leaf = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Leaf"));
	Leaf->SetupAttachment(Root);
	Leaf->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube.Succeeded())
	{
		Leaf->SetStaticMesh(Cube.Object);
	}

	Blocker = CreateDefaultSubobject<UBoxComponent>(TEXT("Blocker"));
	Blocker->SetupAttachment(Root);
	Blocker->SetCollisionProfileName(TEXT("BlockAllDynamic"));

	StoryDoor = CreateDefaultSubobject<UMelodiaStoryDoorComponent>(TEXT("StoryDoor"));
}

void AMelodiaStoryDoorActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	// The engine cube is 100 cm per side and centred; the doorway sits on the floor, so lift by half the height.
	Blocker->SetBoxExtent(OpeningSizeCm * 0.5);
	Blocker->SetRelativeLocation(FVector(0.0, 0.0, OpeningSizeCm.Z * 0.5));
	ApplyLeaf(1.0f);
}

void AMelodiaStoryDoorActor::BeginPlay()
{
	Super::BeginPlay();
	StoryDoor->OnStageChanged.AddUniqueDynamic(this, &AMelodiaStoryDoorActor::HandleStage);
	// The component already ran RefreshFromFlag in its BeginPlay; apply that stage now in case it broadcast before we bound.
	HandleStage(StoryDoor->GetStage(), true);
}

void AMelodiaStoryDoorActor::ApplyLeaf(const float Fraction)
{
	const float F = FMath::Clamp(Fraction, 0.0f, 1.0f);
	const double H = OpeningSizeCm.Z * F;
	Leaf->SetRelativeScale3D(FVector(OpeningSizeCm.X / 100.0, OpeningSizeCm.Y / 100.0, FMath::Max(H, 0.01) / 100.0));
	// Hang from the lintel: the leaf rises toward the top of the opening as F falls, like a drawn curtain.
	Leaf->SetRelativeLocation(FVector(0.0, 0.0, OpeningSizeCm.Z - H * 0.5));
}

void AMelodiaStoryDoorActor::HandleStage(const EMelodiaStoryDoorStage Stage, const bool bFromLoad)
{
	switch (Stage)
	{
	case EMelodiaStoryDoorStage::Sealed:
		bAssembling = false;
		SetActorTickEnabled(false);
		Leaf->SetVisibility(true);
		ApplyLeaf(1.0f);
		Blocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		break;
	case EMelodiaStoryDoorStage::Assembling:
		AssemblyElapsed = 0.0f;
		bAssembling = true;
		SetActorTickEnabled(true);
		Leaf->SetVisibility(true);
		Blocker->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		break;
	case EMelodiaStoryDoorStage::Open:
		bAssembling = false;
		SetActorTickEnabled(false);
		Leaf->SetVisibility(false);
		Blocker->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		break;
	}
}

void AMelodiaStoryDoorActor::Tick(const float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bAssembling)
	{
		return;
	}
	AssemblyElapsed += DeltaSeconds;
	const float Duration = FMath::Max(StoryDoor->AssemblySeconds, KINDA_SMALL_NUMBER);
	const float T = FMath::Clamp(AssemblyElapsed / Duration, 0.0f, 1.0f);
	ApplyLeaf(1.0f - FMath::InterpEaseInOut(0.0f, 1.0f, T, 2.0f));
}
