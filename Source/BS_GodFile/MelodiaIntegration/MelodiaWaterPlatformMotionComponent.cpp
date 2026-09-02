#include "MelodiaWaterPlatformMotionComponent.h"

#include "GameFramework/Actor.h"
#include "MelodiaWaterGameplaySubsystem.h"
#include "MelodiaWaterPlatform.h"

UMelodiaWaterPlatformMotionComponent::UMelodiaWaterPlatformMotionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PrePhysics;
}

void UMelodiaWaterPlatformMotionComponent::BeginPlay()
{
	Super::BeginPlay();
	InitializePlatformState();
}

void UMelodiaWaterPlatformMotionComponent::InitializePlatformState()
{
	if (const AMelodiaWaterPlatform* Platform = Cast<AMelodiaWaterPlatform>(GetOwner()))
	{
		bActive = bStartsActive || Platform->MotionMode == EMelodiaWaterPlatformMotionMode::PhysicsBuoyant;
		if (UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this))
		{
			FMelodiaWaterPlatformState State;
			State.PlatformId = Platform->PlatformId;
			State.NetworkId = Platform->WaterNetworkId;
			State.RouteId = RouteId;
			State.MotionMode = Platform->MotionMode;
			State.RouteProgress = RouteProgress;
			State.bActive = bActive;
			State.bDocked = bDocked;
			WaterGameplay->RegisterPlatform(State);
		}
	}
}

void UMelodiaWaterPlatformMotionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	const AMelodiaWaterPlatform* Platform = Cast<AMelodiaWaterPlatform>(GetOwner());
	if (!Platform || Platform->MotionMode != EMelodiaWaterPlatformMotionMode::KinematicRoute || RoutePoints.Num() < 2)
	{
		return;
	}

	UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this);
	if (WaterGameplay)
	{
		FMelodiaWaterPlatformState State;
		if (WaterGameplay->GetPlatformMotionState(Platform->PlatformId, State))
		{
			RouteProgress = State.RouteProgress;
			bActive = State.bActive;
			bDocked = State.bDocked;
		}
	}
	if (!bActive || !IsGateOpen())
	{
		return;
	}
	if (DockPauseRemaining > 0.0f)
	{
		DockPauseRemaining = FMath::Max(0.0f, DockPauseRemaining - DeltaTime);
		return;
	}

	const float ProgressDelta = DeltaTime * FMath::Max(0.0f, Speed) * GetRouteResponseScale() * (Direction < 0 ? -1.0f : 1.0f);
	RouteProgress += ProgressDelta;
	if (RouteProgress >= 1.0f || RouteProgress <= 0.0f)
	{
		RouteProgress = FMath::Clamp(RouteProgress, 0.0f, 1.0f);
		bDocked = true;
		DockPauseRemaining = DockPauseSeconds;
		if (bReverseOnEnd)
		{
			Direction = -FMath::Sign(Direction == 0 ? 1 : Direction);
		}
		else
		{
			bActive = false;
		}
	}
	else
	{
		bDocked = false;
	}
	ApplyRouteTransform();

	if (WaterGameplay)
	{
		FMelodiaWaterPlatformState State;
		State.PlatformId = Platform->PlatformId;
		State.NetworkId = Platform->WaterNetworkId;
		State.RouteId = RouteId;
		State.MotionMode = Platform->MotionMode;
		State.RouteProgress = RouteProgress;
		State.bActive = bActive;
		State.bDocked = bDocked;
		WaterGameplay->UpdatePlatformState(State);
	}
}

void UMelodiaWaterPlatformMotionComponent::ResetDeterministicProgress()
{
	RouteProgress = Direction < 0 ? 1.0f : 0.0f;
	bDocked = false;
	bActive = bStartsActive;
	DockPauseRemaining = 0.0f;
	ApplyRouteTransform();
}

void UMelodiaWaterPlatformMotionComponent::ApplyRouteTransform()
{
	AActor* Owner = GetOwner();
	if (!Owner || RoutePoints.Num() < 2)
	{
		return;
	}
	const float SegmentPosition = RouteProgress * static_cast<float>(RoutePoints.Num() - 1);
	const int32 SegmentIndex = FMath::Clamp(FMath::FloorToInt(SegmentPosition), 0, RoutePoints.Num() - 2);
	const float Alpha = FMath::Clamp(SegmentPosition - static_cast<float>(SegmentIndex), 0.0f, 1.0f);
	FTransform Transform;
	Transform.Blend(RoutePoints[SegmentIndex], RoutePoints[SegmentIndex + 1], Alpha);
	Owner->SetActorTransform(Transform);
}

bool UMelodiaWaterPlatformMotionComponent::IsGateOpen() const
{
	if (!GateActivationRequirement.IsValid())
	{
		return true;
	}
	const AMelodiaWaterPlatform* Platform = Cast<AMelodiaWaterPlatform>(GetOwner());
	const UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this);
	return Platform && WaterGameplay && WaterGameplay->IsWaterRouteOpen(Platform->WaterNetworkId, GateActivationRequirement);
}

float UMelodiaWaterPlatformMotionComponent::GetRouteResponseScale() const
{
	const AMelodiaWaterPlatform* Platform = Cast<AMelodiaWaterPlatform>(GetOwner());
	const UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this);
	if (!Platform || !WaterGameplay)
	{
		return 1.0f;
	}
	FMelodiaWaterNodeState NodeState;
	if (!WaterGameplay->GetNodeState(Platform->WaterNetworkId, GateActivationRequirement, NodeState))
	{
		return 1.0f;
	}
	return FMath::Max(0.0f, 1.0f + NodeState.Pressure * PressureResponse + NodeState.Level * WaterLevelResponse + NodeState.FlowVelocity.Size() * FlowResponse * 0.01f);
}

