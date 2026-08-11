#include "MelodiaWaterGameplayControllerComponent.h"

#include "MelodiaWaterGameplaySubsystem.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterInteractionTypes.h"

UMelodiaWaterGameplayControllerComponent::UMelodiaWaterGameplayControllerComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaWaterGameplayControllerComponent::BeginPlay()
{
	Super::BeginPlay();
	RegisteredSubsystem = UMelodiaWaterGameplaySubsystem::Get(this);
	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = RegisteredSubsystem.Get())
	{
		WaterGameplay->OnStateChanged.AddUniqueDynamic(this, &ThisClass::HandleWaterStateChanged);
		if (bAutoRegister)
		{
			RegisterConfiguredNode();
		}
	}
}

void UMelodiaWaterGameplayControllerComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = RegisteredSubsystem.Get())
	{
		WaterGameplay->OnStateChanged.RemoveDynamic(this, &ThisClass::HandleWaterStateChanged);
	}
	RegisteredSubsystem.Reset();
	Super::EndPlay(EndPlayReason);
}

bool UMelodiaWaterGameplayControllerComponent::RegisterConfiguredNode()
{
	UMelodiaWaterGameplaySubsystem* WaterGameplay = RegisteredSubsystem.Get();
	if (!WaterGameplay)
	{
		WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this);
		RegisteredSubsystem = WaterGameplay;
	}
	if (!WaterGameplay || !WaterGameplay->RegisterNode(NodeConfig))
	{
		return false;
	}
	return WaterGameplay->GetNodeState(NodeConfig.NetworkId, NodeConfig.NodeId, CurrentState);
}

bool UMelodiaWaterGameplayControllerComponent::InteractWithDevice(AActor* Instigator)
{
	UMelodiaWaterGameplaySubsystem* WaterGameplay = RegisteredSubsystem.Get();
	if (!WaterGameplay)
	{
		return false;
	}
	FMelodiaWaterOperationRequest Request;
	Request.Operation = InteractionOperation;
	Request.NetworkId = NodeConfig.NetworkId;
	Request.TargetWaterNodeId = NodeConfig.NodeId;
	Request.DeviceId = DeviceId;
	Request.RouteId = InteractionRouteId;
	Request.Strength = FMath::Clamp(InteractionStrength, 0.0f, 1.0f);
	Request.PuzzleId = CompletionPuzzleId;
	Request.SourceActor = Instigator ? Instigator : GetOwner();
	return WaterGameplay->ApplyOperation(Request);
}

bool UMelodiaWaterGameplayControllerComponent::SetRouteOpen(bool bOpen, FName InRouteId)
{
	UMelodiaWaterGameplaySubsystem* WaterGameplay = RegisteredSubsystem.Get();
	if (!WaterGameplay)
	{
		return false;
	}
	FMelodiaWaterOperationRequest Request;
	Request.Operation = bOpen ? EMelodiaWaterGameplayOperation::OpenValve : EMelodiaWaterGameplayOperation::CloseValve;
	Request.NetworkId = NodeConfig.NetworkId;
	Request.TargetWaterNodeId = NodeConfig.NodeId;
	Request.DeviceId = DeviceId;
	Request.RouteId = InRouteId;
	Request.SourceActor = GetOwner();
	return WaterGameplay->ApplyOperation(Request);
}

void UMelodiaWaterGameplayControllerComponent::HandleWaterStateChanged(FMelodiaWaterStateChange Change)
{
	if (Change.NetworkId != NodeConfig.NetworkId || Change.NodeId != NodeConfig.NodeId)
	{
		return;
	}
	CurrentState = Change.CurrentState;
	OnControllerStateChanged.Broadcast(Change);

	// Fan out bounded telemetry through the existing interaction bus. This
	// component never writes MPC state directly and never creates a second
	// material/reactivity authority.
	if (UMelodiaWaterInteractionSubsystem* WaterInteraction = UMelodiaWaterInteractionSubsystem::Get(this))
	{
		FMelodiaWaterFluidImpulse Impulse;
		Impulse.WaterBodyId = NodeConfig.WaterBodyId;
		Impulse.Location = GetOwner() ? GetOwner()->GetActorLocation() : FVector::ZeroVector;
		Impulse.Impulse = Change.CurrentState.FlowVelocity.GetClampedToMaxSize(NodeConfig.MaxFlowStrength);
		Impulse.Strength = FMath::Clamp(Change.CurrentState.Pressure, 0.0f, 1.0f);
		Impulse.Radius = 100.0f;
		Impulse.bRouteToNativeWater = false;
		WaterInteraction->PublishFluidImpulse(Impulse);
	}
}

