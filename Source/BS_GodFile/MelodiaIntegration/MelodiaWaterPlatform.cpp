#include "MelodiaWaterPlatform.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "MelodiaWaterBuoyancyComponent.h"
#include "MelodiaWaterGameplaySubsystem.h"
#include "MelodiaWaterPlatformMotionComponent.h"

AMelodiaWaterPlatform::AMelodiaWaterPlatform()
{
	PrimaryActorTick.bCanEverTick = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	PlatformMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PlatformMesh"));
	PlatformMesh->SetupAttachment(Root);
	PlatformMesh->SetMobility(EComponentMobility::Movable);
	PlatformMesh->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	PlatformMesh->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	PlatformMesh->SetCanEverAffectNavigation(false);

	MotionComponent = CreateDefaultSubobject<UMelodiaWaterPlatformMotionComponent>(TEXT("MotionComponent"));
	BuoyancyComponent = CreateDefaultSubobject<UMelodiaWaterBuoyancyComponent>(TEXT("BuoyancyComponent"));

	Tags.Add(TEXT("MelodiaWaterGameplay"));
	Tags.Add(TEXT("NoMerging"));
}

void AMelodiaWaterPlatform::BeginPlay()
{
	Super::BeginPlay();
	AuthoredTransform = GetActorTransform();
	if (MotionComponent)
	{
		MotionComponent->InitializePlatformState();
	}
	if (MotionMode == EMelodiaWaterPlatformMotionMode::PhysicsBuoyant && PlatformMesh)
	{
		PlatformMesh->SetSimulatePhysics(true);
	}
	if (BuoyancyComponent)
	{
		BuoyancyComponent->InitializePlatformState();
	}
	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this))
	{
		FMelodiaWaterPlatformState State;
		State.PlatformId = PlatformId;
		State.NetworkId = WaterNetworkId;
		State.MotionMode = MotionMode;
		State.RouteId = MotionComponent ? MotionComponent->RouteId : NAME_None;
		State.bActive = MotionMode == EMelodiaWaterPlatformMotionMode::PhysicsBuoyant;
		WaterGameplay->RegisterPlatform(State);
	}
}

void AMelodiaWaterPlatform::InitializeFromPCGPoint(FPCGPoint Point, const UPCGMetadata* Metadata)
{
	PointSeed = Point.Seed;
	if (PlatformId.IsNone())
	{
		PlatformId = FName(*FString::Printf(TEXT("WaterPlatform_%08X"), static_cast<uint32>(PointSeed)));
	}
	SetActorTransform(Point.Transform);
	AuthoredTransform = Point.Transform;
	Tags.AddUnique(FName(*FString::Printf(TEXT("StableId_%s"), *PlatformId.ToString())));
	Tags.AddUnique(TEXT("GameplayDataLayer_DL_Musical_HeroGameplay"));
	if (bNoMerging)
	{
		Tags.AddUnique(TEXT("NoMerging"));
	}
	if (MotionComponent)
	{
		MotionComponent->DeterministicSeed = PointSeed;
	}
	for (const FName Tag : Tags)
	{
		const FString Value = Tag.ToString();
		if (Value.StartsWith(TEXT("WaterStableId_")))
		{
			PlatformId = FName(*Value.RightChop(14));
		}
		else if (Value.StartsWith(TEXT("WaterRole_")))
		{
			GameplayRole = FName(*Value.RightChop(10));
		}
		else if (Value.StartsWith(TEXT("WaterNetwork_")))
		{
			WaterNetworkId = FName(*Value.RightChop(13));
		}
		else if (Value.StartsWith(TEXT("WaterRoute_")) && MotionComponent)
		{
			MotionComponent->RouteId = FName(*Value.RightChop(11));
		}
		else if (Value == TEXT("WaterMotion_KinematicRoute"))
		{
			MotionMode = EMelodiaWaterPlatformMotionMode::KinematicRoute;
		}
		else if (Value == TEXT("WaterMotion_PhysicsBuoyant"))
		{
			MotionMode = EMelodiaWaterPlatformMotionMode::PhysicsBuoyant;
		}
	}
}

UPrimitiveComponent* AMelodiaWaterPlatform::GetPhysicsPrimitive() const
{
	return PlatformMesh;
}

void AMelodiaWaterPlatform::ResetPhysicsToAuthoredState()
{
	SetActorTransform(AuthoredTransform);
	if (PlatformMesh && PlatformMesh->IsSimulatingPhysics())
	{
		PlatformMesh->SetPhysicsLinearVelocity(FVector::ZeroVector);
		PlatformMesh->SetPhysicsAngularVelocityInRadians(FVector::ZeroVector);
		PlatformMesh->WakeRigidBody();
	}
	if (MotionComponent)
	{
		MotionComponent->ResetDeterministicProgress();
	}
}
