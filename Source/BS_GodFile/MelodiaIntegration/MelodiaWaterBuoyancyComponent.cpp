#include "MelodiaWaterBuoyancyComponent.h"

#include "Components/PrimitiveComponent.h"
#include "GameFramework/Actor.h"
#include "MelodiaWaterGameplaySubsystem.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterInteractionTypes.h"
#include "MelodiaWaterPlatform.h"

UMelodiaWaterBuoyancyComponent::UMelodiaWaterBuoyancyComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
	ProbeOffsets = {
		FVector(80.0f, 60.0f, 0.0f),
		FVector(80.0f, -60.0f, 0.0f),
		FVector(-80.0f, 60.0f, 0.0f),
		FVector(-80.0f, -60.0f, 0.0f),
	};
}

void UMelodiaWaterBuoyancyComponent::BeginPlay()
{
	Super::BeginPlay();
	InitializePlatformState();
}

void UMelodiaWaterBuoyancyComponent::InitializePlatformState()
{
	if (const AMelodiaWaterPlatform* Platform = Cast<AMelodiaWaterPlatform>(GetOwner()))
	{
		if (!WaterNetworkId.IsValid())
		{
			WaterNetworkId = Platform->WaterNetworkId;
		}
	}
}

void UMelodiaWaterBuoyancyComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	AMelodiaWaterPlatform* Platform = Cast<AMelodiaWaterPlatform>(GetOwner());
	if (!Platform || Platform->MotionMode != EMelodiaWaterPlatformMotionMode::PhysicsBuoyant)
	{
		return;
	}
	UPrimitiveComponent* Primitive = Platform->GetPhysicsPrimitive();
	if (!Primitive || !Primitive->IsSimulatingPhysics() || ProbeOffsets.Num() == 0)
	{
		return;
	}

	UMelodiaWaterInteractionSubsystem* WaterInteraction = UMelodiaWaterInteractionSubsystem::Get(this);
	if (!WaterInteraction)
	{
		bHasAuthoritativeSample = false;
		return;
	}

	const FTransform ComponentTransform = Primitive->GetComponentTransform();
	const float Mass = FMath::Max(0.01f, Primitive->GetMass());
	const float Gravity = FMath::Abs(GetWorld() ? GetWorld()->GetGravityZ() : -980.0f);
	float TotalImmersion = 0.0f;
	int32 ValidSamples = 0;
	FVector ForceSum = FVector::ZeroVector;
	FVector TorqueSum = FVector::ZeroVector;

	for (const FVector& LocalProbe : ProbeOffsets)
	{
		const FVector ProbeWorld = ComponentTransform.TransformPosition(LocalProbe);
		FMelodiaWaterSample Sample;
		if (!WaterInteraction->QueryWaterAtLocationForActor(Platform, ProbeWorld, Sample) ||
			!Sample.bValid || !Sample.bSurfaceValid || Sample.QueryProvider != EMelodiaWaterQueryProvider::NativeWaterBody)
		{
			continue;
		}

		const float Immersion = FMath::Clamp((Sample.SurfaceLocation.Z - ProbeWorld.Z + ProbeRadius) / (2.0f * ProbeRadius), 0.0f, 1.0f);
		if (Immersion <= 0.0f)
		{
			continue;
		}
		++ValidSamples;
		TotalImmersion += Immersion;
		const FVector BuoyantForce = FVector::UpVector * Mass * Gravity * BuoyancyScale * Immersion;
		ForceSum += BuoyantForce;
		TorqueSum += FVector::CrossProduct(ProbeWorld - Primitive->GetComponentLocation(), BuoyantForce) * TorqueScale;
	}

	bHasAuthoritativeSample = ValidSamples > 0;
	LastImmersion = ValidSamples > 0 ? TotalImmersion / static_cast<float>(ValidSamples) : 0.0f;
	const bool bImmersed = LastImmersion >= MinimumImmersionThreshold;
	if (!bHasAuthoritativeSample)
	{
		// No native sample means no fabricated buoyancy. Preserve the physics body
		// in its current safe state and wait for the authoritative query path.
		bWasImmersed = false;
		return;
	}

	ForceSum /= static_cast<float>(ValidSamples);
	ForceSum = ForceSum.GetClampedToMaxSize(FMath::Max(0.0f, MaximumForce));
	Primitive->AddForce(ForceSum);
	const FVector Velocity = Primitive->GetPhysicsLinearVelocity();
	Primitive->AddForce(-Velocity * LinearDrag * Mass);
	Primitive->AddTorqueInRadians(-Primitive->GetPhysicsAngularVelocityInRadians() * AngularDrag * Mass);

	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this))
	{
		FVector Flow = FVector::ZeroVector;
		if (WaterGameplay->GetResolvedWaterFlow(WaterBodyId, Flow))
		{
			Primitive->AddForce(Flow.GetClampedToMaxSize(FMath::Max(0.0f, MaximumForce)) * FlowForceScale);
		}
	}
	Primitive->AddTorqueInRadians(TorqueSum.GetClampedToMaxSize(FMath::Max(0.0f, MaximumForce)));

	if (bPublishImpactEvents && bImmersed != bWasImmersed)
	{
		FMelodiaWaterContactEvent Event;
		Event.EventType = bImmersed ? EMelodiaWaterContactType::WaterImpact : EMelodiaWaterContactType::Ripple;
		Event.SourceActor = Platform;
		Event.ContactLocation = Primitive->GetComponentLocation();
		Event.ImpulseVector = bImmersed ? ForceSum : -ForceSum;
		Event.Intensity = FMath::Clamp(LastImmersion, 0.0f, 1.0f);
		Event.Radius = ProbeRadius;
		WaterInteraction->PublishContact(Event);
	}
	bWasImmersed = bImmersed;
}

