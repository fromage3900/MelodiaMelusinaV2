#include "MelodiaWaterGameplaySubsystem.h"

#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "Stats/Stats.h"

void UMelodiaWaterGameplaySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
}

void UMelodiaWaterGameplaySubsystem::Deinitialize()
{
	Networks.Reset();
	PlatformStates.Reset();
	CompletedPuzzleIds.Reset();
	PendingSaveState = FMelodiaWaterGameplaySaveData();
	bHasPendingSaveState = false;
	Super::Deinitialize();
}

UMelodiaWaterGameplaySubsystem* UMelodiaWaterGameplaySubsystem::Get(const UObject* WorldContextObject)
{
	if (!WorldContextObject)
	{
		return nullptr;
	}

	if (const UGameInstance* GameInstance = Cast<UGameInstance>(WorldContextObject))
	{
		return const_cast<UGameInstance*>(GameInstance)->GetSubsystem<UMelodiaWaterGameplaySubsystem>();
	}

	if (!GEngine)
	{
		return nullptr;
	}

	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull);
	return World && World->GetGameInstance()
		? World->GetGameInstance()->GetSubsystem<UMelodiaWaterGameplaySubsystem>()
		: nullptr;
}

bool UMelodiaWaterGameplaySubsystem::RegisterNode(const FMelodiaWaterNodeConfig& Config)
{
	if (!Config.NetworkId.IsValid() || !Config.NodeId.IsValid() || Config.Capacity <= 0.0f)
	{
		return false;
	}

	const FName NetworkKey = Config.NetworkId.GetTagName();
	const FName NodeKey = Config.NodeId.GetTagName();

	FNetworkRuntime& Network = Networks.FindOrAdd(NetworkKey);
	Network.NodeConfigs.Add(NodeKey, Config);
	FMelodiaWaterNodeState& State = Network.NodeStates.FindOrAdd(NodeKey);
	if (!State.NetworkId.IsValid())
	{
		State.NetworkId = Config.NetworkId;
		State.NodeId = Config.NodeId;
		State.Level = FMath::Clamp(Config.InitialLevel, 0.0f, Config.Capacity);
		State.Pressure = FMath::Clamp(Config.InitialPressure, 0.0f, 1.0f);
		State.FlowVelocity = FVector::ZeroVector;
		State.Revision = 0;
		ApplyPendingNodeState(Config.NetworkId, Config.NodeId, State);
	}
	RecomputeFlow(Config.NetworkId);
	return true;
}

bool UMelodiaWaterGameplaySubsystem::RegisterLink(const FMelodiaWaterLinkConfig& Config)
{
	if (!Config.NetworkId.IsValid() || !Config.LinkId.IsValid() || !Config.SourceNodeId.IsValid() || !Config.DestinationNodeId.IsValid())
	{
		return false;
	}

	const FName NetworkKey = Config.NetworkId.GetTagName();

	FNetworkRuntime& Network = Networks.FindOrAdd(NetworkKey);
	Network.LinkConfigs.Add(Config.LinkId.GetTagName(), Config);
	const FName Key = RouteKey(Config);
	Network.OpenRoutes.FindOrAdd(Key) = Config.bInitiallyOpen;
	if (bHasPendingSaveState)
	{
		for (const FMelodiaWaterSavedRouteState& SavedRoute : PendingSaveState.RouteStates)
		{
			if (SavedRoute.NetworkId == Config.NetworkId && SavedRoute.RouteId == Key)
			{
				Network.OpenRoutes[Key] = SavedRoute.bOpen;
				break;
			}
		}
	}
	RecomputeFlow(Config.NetworkId);
	return true;
}

bool UMelodiaWaterGameplaySubsystem::UnregisterNetworkBindings(FGameplayTag NetworkId)
{
	FNetworkRuntime* Network = FindNetwork(NetworkId);
	if (!Network)
	{
		return false;
	}
	// Keep NodeStates so a map transition cannot erase logical progress. The
	// next map re-registers its authored configs and uses the same state.
	Network->NodeConfigs.Reset();
	Network->LinkConfigs.Reset();
	Network->OpenRoutes.Reset();
	return true;
}

bool UMelodiaWaterGameplaySubsystem::ApplyResonance(FGameplayTag NetworkId, FGameplayTag TargetWaterNodeId, FGameplayTag ResonanceChannel, float Strength, FGameplayTag PuzzleId, FGameplayTag RouteId, AActor* SourceActor)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaWaterGameplaySubsystem_ApplyResonance);
	FMelodiaWaterOperationRequest Request;
	Request.Operation = EMelodiaWaterGameplayOperation::ResonancePulse;
	Request.NetworkId = NetworkId;
	Request.TargetWaterNodeId = TargetWaterNodeId;
	Request.ResonanceChannel = ResonanceChannel;
	Request.Strength = FMath::Clamp(Strength, 0.0f, 1.0f);
	Request.PuzzleId = PuzzleId;
	Request.RouteId = RouteId;
	Request.SourceActor = SourceActor;
	return ApplyOperation(Request);
}

bool UMelodiaWaterGameplaySubsystem::ApplyOperation(const FMelodiaWaterOperationRequest& Request)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaWaterGameplaySubsystem_ApplyOperation);
	FNetworkRuntime* Network = nullptr;
	FMelodiaWaterNodeConfig* Config = nullptr;
	FMelodiaWaterNodeState* State = nullptr;
	const FGameplayTag NodeId = Request.TargetWaterNodeId.IsValid() ? Request.TargetWaterNodeId : Request.SourceNodeId;
	if (!NodeId.IsValid() || !FindNode(Request.NetworkId, NodeId, Network, Config, State))
	{
		Reject(Request, TEXT("unknown network or water node"));
		return false;
	}

	const FMelodiaWaterNodeState Previous = *State;
	const float Amount = FMath::Max(Request.Amount, Request.Strength);

	switch (Request.Operation)
	{
	case EMelodiaWaterGameplayOperation::Fill:
	case EMelodiaWaterGameplayOperation::Pump:
		State->Level += Amount;
		break;
	case EMelodiaWaterGameplayOperation::Drain:
		State->Level -= Amount;
		break;
	case EMelodiaWaterGameplayOperation::ApplyPressure:
	case EMelodiaWaterGameplayOperation::ResonancePulse:
		State->Pressure += Amount;
		if (Request.Operation == EMelodiaWaterGameplayOperation::ResonancePulse)
		{
			State->Level += Amount * 0.25f;
		}
		break;
	case EMelodiaWaterGameplayOperation::Redirect:
		if (!Request.Direction.IsNearlyZero())
		{
			Config->FlowDirection = Request.Direction.GetSafeNormal();
		}
		break;
	case EMelodiaWaterGameplayOperation::OpenValve:
	case EMelodiaWaterGameplayOperation::CloseValve:
	{
		const FGameplayTag RouteTag = Request.RouteId.IsValid() ? Request.RouteId : Request.DeviceId;
		if (!RouteTag.IsValid())
		{
			Reject(Request, TEXT("valve operation has no route or device ID"));
			return false;
		}
		Network->OpenRoutes.FindOrAdd(RouteTag.GetTagName()) = Request.Operation == EMelodiaWaterGameplayOperation::OpenValve;
		break;
	}
	case EMelodiaWaterGameplayOperation::Reset:
		State->Level = FMath::Clamp(Config->InitialLevel, 0.0f, Config->Capacity);
		State->Pressure = FMath::Clamp(Config->InitialPressure, 0.0f, 1.0f);
		State->bBlocked = false;
		State->bSolved = false;
		break;
	default:
		Reject(Request, TEXT("unsupported water operation"));
		return false;
	}

	State->Level = FMath::Clamp(State->Level, 0.0f, Config->Capacity);
	State->Pressure = FMath::Clamp(State->Pressure, 0.0f, 1.0f);
	State->Revision++;

	if (Request.Operation == EMelodiaWaterGameplayOperation::ResonancePulse)
	{
		if (Request.RouteId.IsValid())
		{
			Network->OpenRoutes.FindOrAdd(Request.RouteId.GetTagName()) = true;
		}
		if (Request.PuzzleId.IsValid() && !CompletedPuzzleIds.Contains(Request.PuzzleId))
		{
			CompletedPuzzleIds.Add(Request.PuzzleId);
			State->bSolved = true;
			++PuzzleRevision;
			OnPuzzleSolved.Broadcast(Request.PuzzleId);
		}
	}

	RecomputeFlow(Request.NetworkId);
	FMelodiaWaterStateChange Change;
	Change.NetworkId = Request.NetworkId;
	Change.NodeId = NodeId;
	Change.PreviousState = Previous;
	Change.CurrentState = *State;
	Change.Operation = Request.Operation;
	Change.DeviceId = Request.DeviceId;
	OnStateChanged.Broadcast(Change);
	return true;
}

bool UMelodiaWaterGameplaySubsystem::GetNodeState(FGameplayTag NetworkId, FGameplayTag NodeId, FMelodiaWaterNodeState& OutState) const
{
	OutState = FMelodiaWaterNodeState();
	const FNetworkRuntime* Network = FindNetwork(NetworkId);
	const FMelodiaWaterNodeState* Found = Network ? Network->NodeStates.Find(NodeId.GetTagName()) : nullptr;
	if (!Found)
	{
		return false;
	}
	OutState = *Found;
	return true;
}

float UMelodiaWaterGameplaySubsystem::GetWaterLevelForNode(FGameplayTag NetworkId, FGameplayTag NodeId) const
{
	FMelodiaWaterNodeState State;
	return GetNodeState(NetworkId, NodeId, State) ? State.Level : 0.0f;
}

float UMelodiaWaterGameplaySubsystem::GetPressureForNode(FGameplayTag NetworkId, FGameplayTag NodeId) const
{
	FMelodiaWaterNodeState State;
	return GetNodeState(NetworkId, NodeId, State) ? State.Pressure : 0.0f;
}

bool UMelodiaWaterGameplaySubsystem::GetResolvedWaterFlow(FGameplayTag WaterBodyId, FVector& OutFlow) const
{
	OutFlow = FVector::ZeroVector;
	if (!WaterBodyId.IsValid())
	{
		return false;
	}

	bool bFound = false;
	for (const TPair<FName, FNetworkRuntime>& Pair : Networks)
	{
		for (const TPair<FName, FMelodiaWaterNodeConfig>& NodePair : Pair.Value.NodeConfigs)
		{
			if (NodePair.Value.WaterBodyId == WaterBodyId)
			{
				if (const FMelodiaWaterNodeState* State = Pair.Value.NodeStates.Find(NodePair.Key))
				{
					OutFlow += State->FlowVelocity;
					bFound = true;
				}
			}
		}
	}
	return bFound;
}

bool UMelodiaWaterGameplaySubsystem::IsWaterRouteOpen(FGameplayTag NetworkId, FGameplayTag RouteId) const
{
	const FNetworkRuntime* Network = FindNetwork(NetworkId);
	return Network && IsRouteOpen(*Network, RouteId);
}

bool UMelodiaWaterGameplaySubsystem::GetPlatformMotionState(FGameplayTag PlatformId, FMelodiaWaterPlatformState& OutState) const
{
	OutState = FMelodiaWaterPlatformState();
	const FMelodiaWaterPlatformState* Found = PlatformStates.Find(PlatformId.GetTagName());
	if (!Found)
	{
		return false;
	}
	OutState = *Found;
	return true;
}

bool UMelodiaWaterGameplaySubsystem::RegisterPlatform(const FMelodiaWaterPlatformState& State)
{
	if (!State.PlatformId.IsValid())
	{
		return false;
	}
	FMelodiaWaterPlatformState& Registered = PlatformStates.FindOrAdd(State.PlatformId.GetTagName());
	if (!Registered.PlatformId.IsValid())
	{
		Registered = State;
		if (bHasPendingSaveState)
		{
			for (const FMelodiaWaterPlatformState& Saved : PendingSaveState.PlatformStates)
			{
				if (Saved.PlatformId == State.PlatformId)
				{
					Registered = Saved;
					break;
				}
			}
		}
	}
	return true;
}

bool UMelodiaWaterGameplaySubsystem::UpdatePlatformState(const FMelodiaWaterPlatformState& State)
{
	if (!State.PlatformId.IsValid() || !PlatformStates.Contains(State.PlatformId.GetTagName()))
	{
		return false;
	}
	FMelodiaWaterPlatformState Sanitized = State;
	Sanitized.RouteProgress = FMath::Clamp(Sanitized.RouteProgress, 0.0f, 1.0f);
	PlatformStates[State.PlatformId.GetTagName()] = Sanitized;
	return true;
}

bool UMelodiaWaterGameplaySubsystem::IsPuzzleSolved(FGameplayTag PuzzleId) const
{
	return PuzzleId.IsValid() && CompletedPuzzleIds.Contains(PuzzleId);
}

void UMelodiaWaterGameplaySubsystem::CaptureSaveState(FMelodiaWaterGameplaySaveData& OutData) const
{
	OutData = FMelodiaWaterGameplaySaveData();
	OutData.PuzzleRevision = PuzzleRevision;
	OutData.CompletedPuzzleIds = CompletedPuzzleIds;

	TArray<FName> NetworkIds;
	Networks.GetKeys(NetworkIds);
	NetworkIds.Sort(FNameLexicalLess());
	for (const FName NetworkId : NetworkIds)
	{
		const FNetworkRuntime* Network = Networks.Find(NetworkId);
		if (!Network)
		{
			continue;
		}
		TArray<FName> NodeIds;
		Network->NodeStates.GetKeys(NodeIds);
		NodeIds.Sort(FNameLexicalLess());
		for (const FName NodeId : NodeIds)
		{
			FMelodiaWaterSavedNodeState Saved;
			Saved.NetworkId = NetworkId;
			Saved.NodeId = NodeId;
			Saved.State = Network->NodeStates[NodeId];
			OutData.NodeStates.Add(Saved);
		}
		TArray<FName> RouteIds;
		Network->OpenRoutes.GetKeys(RouteIds);
		RouteIds.Sort(FNameLexicalLess());
		for (const FName RouteId : RouteIds)
		{
			FMelodiaWaterSavedRouteState SavedRoute;
			SavedRoute.NetworkId = NetworkId;
			SavedRoute.RouteId = RouteId;
			SavedRoute.bOpen = Network->OpenRoutes[RouteId];
			OutData.RouteStates.Add(SavedRoute);
		}
	}

	TArray<FName> PlatformIds;
	PlatformStates.GetKeys(PlatformIds);
	PlatformIds.Sort(FNameLexicalLess());
	for (const FName PlatformId : PlatformIds)
	{
		OutData.PlatformStates.Add(PlatformStates[PlatformId]);
	}
}

void UMelodiaWaterGameplaySubsystem::RestoreSaveState(const FMelodiaWaterGameplaySaveData& Data)
{
	PendingSaveState = Data;
	bHasPendingSaveState = true;
	PuzzleRevision = FMath::Max(0, Data.PuzzleRevision);
	CompletedPuzzleIds = Data.CompletedPuzzleIds;

	for (const FMelodiaWaterSavedNodeState& Saved : Data.NodeStates)
	{
		if (FNetworkRuntime* Network = Networks.Find(Saved.NetworkId))
		{
			if (Network->NodeStates.Contains(Saved.NodeId))
			{
				Network->NodeStates[Saved.NodeId] = Saved.State;
			}
		}
	}
	for (const FMelodiaWaterSavedRouteState& Saved : Data.RouteStates)
	{
		if (FNetworkRuntime* Network = Networks.Find(Saved.NetworkId))
		{
			Network->OpenRoutes.Add(Saved.RouteId, Saved.bOpen);
		}
	}
	for (const FMelodiaWaterPlatformState& Saved : Data.PlatformStates)
	{
		if (PlatformStates.Contains(Saved.PlatformId.GetTagName()))
		{
			PlatformStates[Saved.PlatformId.GetTagName()] = Saved;
		}
	}
	for (const TPair<FName, FNetworkRuntime>& Pair : Networks)
	{
		RecomputeFlow(Pair.Key);
	}
}

void UMelodiaWaterGameplaySubsystem::ResetWaterGameplayState()
{
	Networks.Reset();
	PlatformStates.Reset();
	CompletedPuzzleIds.Reset();
	PuzzleRevision = 0;
	PendingSaveState = FMelodiaWaterGameplaySaveData();
	bHasPendingSaveState = false;
}

void UMelodiaWaterGameplaySubsystem::RecomputeFlow(FGameplayTag NetworkId)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaWaterGameplaySubsystem_RecomputeFlow);
	FNetworkRuntime* Network = FindNetwork(NetworkId);
	if (!Network)
	{
		return;
	}
	for (TPair<FName, FMelodiaWaterNodeState>& Pair : Network->NodeStates)
	{
		Pair.Value.FlowVelocity = FVector::ZeroVector;
	}
	for (const TPair<FName, FMelodiaWaterLinkConfig>& Pair : Network->LinkConfigs)
	{
		const FMelodiaWaterLinkConfig& Link = Pair.Value;
		if (!IsRouteOpen(*Network, RouteKey(Link)))
		{
			continue;
		}
		const FMelodiaWaterNodeConfig* SourceConfig = Network->NodeConfigs.Find(Link.SourceNodeId.GetTagName());
		const FMelodiaWaterNodeConfig* DestinationConfig = Network->NodeConfigs.Find(Link.DestinationNodeId.GetTagName());
		FMelodiaWaterNodeState* SourceState = Network->NodeStates.Find(Link.SourceNodeId.GetTagName());
		FMelodiaWaterNodeState* DestinationState = Network->NodeStates.Find(Link.DestinationNodeId.GetTagName());
		if (!SourceConfig || !DestinationConfig || !SourceState || !DestinationState)
		{
			continue;
		}
		const float Head = FMath::Max(0.0f, SourceState->Level - DestinationState->Level);
		const float Flow = FMath::Min(SourceConfig->MaxFlowStrength, Head * Link.TransferCapacity * (1.0f - FMath::Clamp(Link.Resistance, 0.0f, 1.0f)));
		const FVector Direction = SourceConfig->FlowDirection.IsNearlyZero() ? FVector::ForwardVector : SourceConfig->FlowDirection.GetSafeNormal();
		SourceState->FlowVelocity += Direction * Flow * -0.25f;
		DestinationState->FlowVelocity += Direction * Flow;
	}
}

void UMelodiaWaterGameplaySubsystem::Reject(const FMelodiaWaterOperationRequest& Request, const FString& Reason)
{
	OnOperationRejected.Broadcast(Request.NetworkId, Reason);
}

bool UMelodiaWaterGameplaySubsystem::FindNode(FGameplayTag NetworkId, FGameplayTag NodeId, FNetworkRuntime*& OutNetwork, FMelodiaWaterNodeConfig*& OutConfig, FMelodiaWaterNodeState*& OutState)
{
	OutNetwork = FindNetwork(NetworkId);
	OutConfig = nullptr;
	OutState = nullptr;
	if (!OutNetwork)
	{
		return false;
	}
	OutConfig = OutNetwork->NodeConfigs.Find(NodeId.GetTagName());
	OutState = OutNetwork->NodeStates.Find(NodeId.GetTagName());
	return OutConfig && OutState;
}

const UMelodiaWaterGameplaySubsystem::FNetworkRuntime* UMelodiaWaterGameplaySubsystem::FindNetwork(FGameplayTag NetworkId) const
{
	return Networks.Find(NetworkId.GetTagName());
}

UMelodiaWaterGameplaySubsystem::FNetworkRuntime* UMelodiaWaterGameplaySubsystem::FindNetwork(FGameplayTag NetworkId)
{
	return Networks.Find(NetworkId.GetTagName());
}

bool UMelodiaWaterGameplaySubsystem::IsRouteOpen(const FNetworkRuntime& Network, FGameplayTag RouteId) const
{
	if (!RouteId.IsValid())
	{
		return false;
	}
	const bool* Open = Network.OpenRoutes.Find(RouteId.GetTagName());
	return Open ? *Open : false;
}

FName UMelodiaWaterGameplaySubsystem::RouteKey(const FMelodiaWaterLinkConfig& Link) const
{
	return Link.RouteId.IsValid() ? Link.RouteId.GetTagName() : Link.LinkId.GetTagName();
}

void UMelodiaWaterGameplaySubsystem::ApplyPendingNodeState(FGameplayTag NetworkId, FGameplayTag NodeId, FMelodiaWaterNodeState& State)
{
	if (!bHasPendingSaveState)
	{
		return;
	}
	for (const FMelodiaWaterSavedNodeState& Saved : PendingSaveState.NodeStates)
	{
		if (Saved.NetworkId == NetworkId && Saved.NodeId == NodeId)
		{
			State = Saved.State;
			return;
		}
	}
}
