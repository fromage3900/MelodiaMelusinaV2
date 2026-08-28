#include "MelodiaPCGWaterGameplayBridgeComponent.h"

#include "MelodiaWaterGameplaySubsystem.h"
#include "Stats/Stats.h"

UMelodiaPCGWaterGameplayBridgeComponent::UMelodiaPCGWaterGameplayBridgeComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	GradeStrength.Add(EMelodiaRhythmGrade::Good, 0.35f);
	GradeStrength.Add(EMelodiaRhythmGrade::Great, 0.70f);
	GradeStrength.Add(EMelodiaRhythmGrade::Perfect, 1.0f);
}

void UMelodiaPCGWaterGameplayBridgeComponent::BeginPlay()
{
	Super::BeginPlay();
	RebindToHost();
}

void UMelodiaPCGWaterGameplayBridgeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (APCGHeroMusicGraphHost* Host = BoundHost.Get())
	{
		Host->OnNoteJudged.RemoveDynamic(this, &ThisClass::HandleNoteJudged);
		Host->OnPatternCompleted.RemoveDynamic(this, &ThisClass::HandlePatternCompleted);
	}
	BoundHost.Reset();
	bBound = false;
	Super::EndPlay(EndPlayReason);
}

bool UMelodiaPCGWaterGameplayBridgeComponent::RebindToHost()
{
	if (APCGHeroMusicGraphHost* ExistingHost = BoundHost.Get())
	{
		ExistingHost->OnNoteJudged.RemoveDynamic(this, &ThisClass::HandleNoteJudged);
		ExistingHost->OnPatternCompleted.RemoveDynamic(this, &ThisClass::HandlePatternCompleted);
	}

	BoundHost = Cast<APCGHeroMusicGraphHost>(GetOwner());
	APCGHeroMusicGraphHost* Host = BoundHost.Get();
	if (!Host)
	{
		bBound = false;
		return false;
	}

	Host->OnNoteJudged.AddUniqueDynamic(this, &ThisClass::HandleNoteJudged);
	Host->OnPatternCompleted.AddUniqueDynamic(this, &ThisClass::HandlePatternCompleted);
	bBound = true;
	return true;
}

bool UMelodiaPCGWaterGameplayBridgeComponent::UnregisterWaterBindings()
{
	if (WaterNetworkId.IsNone())
	{
		return false;
	}
	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this))
	{
		return WaterGameplay->UnregisterNetworkBindings(WaterNetworkId);
	}
	return false;
}

void UMelodiaPCGWaterGameplayBridgeComponent::HandleNoteJudged(FPCGHeroMusicNoteEvent Event)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaPCGWaterGameplayBridge_HandleNoteJudged);
	if (!bBound || static_cast<uint8>(Event.Grade) < static_cast<uint8>(MinimumAcceptedGrade))
	{
		return;
	}
	AActor* SourceActor = Event.InteractingActor.Get();
	if (!SourceActor)
	{
		SourceActor = GetOwner();
	}
	SubmitResonance(GetStrengthForGrade(Event.Grade), NAME_None, PlatformRouteId, SourceActor);
}

void UMelodiaPCGWaterGameplayBridgeComponent::HandlePatternCompleted()
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaPCGWaterGameplayBridge_HandlePatternCompleted);
	if (!bBound || CompletionPuzzleId.IsNone())
	{
		return;
	}
	SubmitResonance(1.0f, CompletionPuzzleId, PlatformRouteId, GetOwner());
}

float UMelodiaPCGWaterGameplayBridgeComponent::GetStrengthForGrade(EMelodiaRhythmGrade Grade) const
{
	if (const float* Found = GradeStrength.Find(Grade))
	{
		return FMath::Clamp(*Found, 0.0f, 1.0f);
	}
	return 0.0f;
}

void UMelodiaPCGWaterGameplayBridgeComponent::SubmitResonance(float Strength, FName PuzzleId, FName RouteId, AActor* SourceActor)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaPCGWaterGameplayBridge_SubmitResonance);
	if (WaterNetworkId.IsNone() || TargetWaterNodeId.IsNone())
	{
		return;
	}

	FMelodiaWaterOperationRequest Request;
	Request.Operation = EMelodiaWaterGameplayOperation::ResonancePulse;
	Request.NetworkId = WaterNetworkId;
	Request.TargetWaterNodeId = TargetWaterNodeId;
	Request.ResonanceChannel = ResonanceChannel;
	Request.Strength = FMath::Clamp(Strength, 0.0f, 1.0f);
	Request.PuzzleId = PuzzleId;
	Request.RouteId = RouteId;
	Request.SourceActor = SourceActor;
	OnResonanceRequested.Broadcast(Request);

	if (UMelodiaWaterGameplaySubsystem* WaterGameplay = UMelodiaWaterGameplaySubsystem::Get(this))
	{
		if (WaterGameplay->ApplyOperation(Request))
		{
			LastAppliedStrength = Request.Strength;
		}
	}
}
