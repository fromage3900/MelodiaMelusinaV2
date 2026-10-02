#include "MelodiaHybridEncounterComponent.h"

#include "Engine/DamageEvents.h"
#include "Engine/World.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaRhythmSkillDefinition.h"

UMelodiaHybridEncounterComponent::UMelodiaHybridEncounterComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaHybridEncounterComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this))
	{
		Rhythm->OnRhythmComplete.AddUniqueDynamic(this, &ThisClass::HandleRhythmComplete);
	}
}

void UMelodiaHybridEncounterComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UMelodiaExternalJRPGBridgeSubsystem* Bridge =
		UMelodiaExternalJRPGBridgeSubsystem::GetGameInstanceSubsystem(GetWorld() ? GetWorld()->GetGameInstance() : nullptr))
	{
		Bridge->UnbindWorldDamageResolver(this);
	}
	if (UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this))
	{
		Rhythm->OnRhythmComplete.RemoveDynamic(this, &ThisClass::HandleRhythmComplete);
		if (SequenceSessionId != 0 && Rhythm->GetActiveSessionId() == SequenceSessionId)
		{
			Rhythm->InvalidateSession();
			Rhythm->ClearPendingDamageMultiplier();
		}
	}
	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		Input->PopContext(RhythmInputHandle);
	}
	RhythmInputHandle = FMelodiaInputContextHandle();
	SequenceSessionId = 0;
	PendingEffectSessionId = 0;
	Super::EndPlay(EndPlayReason);
}

bool UMelodiaHybridEncounterComponent::EnterSequence(const FName RhythmSkillId)
{
	if (PresentationMode != EMelodiaHybridPresentationMode::Flow || EncounterId.IsNone()
		|| !IsValid(GetOwner()) || !GetOwner()->CanBeDamaged())
	{
		return false;
	}
	UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this);
	UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this);
	const UMelodiaRhythmSkillDefinition* Skill = Rhythm ? Rhythm->FindSkill(RhythmSkillId) : nullptr;
	if (!Rhythm || !Input || Rhythm->GetActiveSessionId() != 0 || !Skill
		|| (Skill->EffectType != EMelodiaRhythmEffectType::Damage
			&& Skill->EffectType != EMelodiaRhythmEffectType::Crit))
	{
		return false;
	}

	const int32 StartedSessionId = Rhythm->StartSession(RhythmSkillId);
	if (StartedSessionId == 0)
	{
		return false;
	}
	const FMelodiaInputContextHandle Handle = Input->PushContext(EMelodiaInputContext::Rhythm, this);
	if (!Handle.IsValid())
	{
		Rhythm->InvalidateSession();
		return false;
	}

	SequenceSessionId = StartedSessionId;
	PendingEffectSessionId = 0;
	bSequenceEffectConsumed = false;
	RhythmInputHandle = Handle;
	PresentationMode = EMelodiaHybridPresentationMode::Sequence;
	OnPresentationModeChanged.Broadcast(PresentationMode, GetOwner());
	return true;
}

bool UMelodiaHybridEncounterComponent::CancelSequence()
{
	if (PresentationMode != EMelodiaHybridPresentationMode::Sequence)
	{
		return false;
	}
	// Clear the identity before notifying any listener. A late stock callback
	// cannot turn a cancelled phrase into damage, even after another entry.
	const int32 CancelledSession = SequenceSessionId;
	PendingEffectSessionId = 0;
	SequenceSessionId = 0;
	bSequenceEffectConsumed = true;
	if (UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this))
	{
		if (Rhythm->GetActiveSessionId() == CancelledSession)
		{
			Rhythm->InvalidateSession();
			Rhythm->ClearPendingDamageMultiplier();
		}
	}
	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		Input->PopContext(RhythmInputHandle);
	}
	RhythmInputHandle = FMelodiaInputContextHandle();
	PresentationMode = EMelodiaHybridPresentationMode::Flow;
	OnPresentationModeChanged.Broadcast(PresentationMode, GetOwner());
	return true;
}

bool UMelodiaHybridEncounterComponent::ExitSequence()
{
	if (PresentationMode != EMelodiaHybridPresentationMode::Sequence || PendingEffectSessionId != 0)
	{
		return false;
	}
	if (UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this))
	{
		if (Rhythm->GetActiveSessionId() == SequenceSessionId)
		{
			if (Rhythm->IsSessionActive())
			{
				return false;
			}
			Rhythm->InvalidateSession();
			Rhythm->ClearPendingDamageMultiplier();
		}
	}
	if (UMelodiaInputContextSubsystem* Input = UMelodiaInputContextSubsystem::Get(this))
	{
		Input->PopContext(RhythmInputHandle);
	}
	RhythmInputHandle = FMelodiaInputContextHandle();
	SequenceSessionId = 0;
	PresentationMode = EMelodiaHybridPresentationMode::Flow;
	OnPresentationModeChanged.Broadcast(PresentationMode, GetOwner());
	return true;
}

EMelodiaSkillGrade UMelodiaHybridEncounterComponent::RegisterSequenceLaneHit(const int32 LaneIndex)
{
	UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this);
	return PresentationMode == EMelodiaHybridPresentationMode::Sequence && Rhythm
		&& Rhythm->GetActiveSessionId() == SequenceSessionId
		? Rhythm->RegisterLaneHit(LaneIndex)
		: EMelodiaSkillGrade::Miss;
}

bool UMelodiaHybridEncounterComponent::FinishSequencePhrase()
{
	UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this);
	return PresentationMode == EMelodiaHybridPresentationMode::Sequence && Rhythm
		&& Rhythm->GetActiveSessionId() == SequenceSessionId && Rhythm->FinishSession();
}

void UMelodiaHybridEncounterComponent::HandleRhythmComplete(const EMelodiaSkillGrade Grade,
	const int32 HitCount, const int32 MissCount)
{
	UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this);
	if (PresentationMode != EMelodiaHybridPresentationMode::Sequence || !Rhythm
		|| Rhythm->GetActiveSessionId() != SequenceSessionId || PendingEffectSessionId != 0
		|| bSequenceEffectConsumed)
	{
		return;
	}
	FMelodiaRhythmEffectRequest Request;
	if (Rhythm->ConsumePendingRequest(Request) && Request.SessionId == SequenceSessionId)
	{
		PendingEffectSessionId = Request.SessionId;
		OnWorldEffectRequested.Broadcast(GetOwner(), Request);
	}
}

bool UMelodiaHybridEncounterComponent::ApplyResolvedSequenceDamage(const float FinalDamage, const int32 SessionId)
{
	const UMelodiaRhythmCombatSubsystem* Rhythm = UMelodiaRhythmCombatSubsystem::Get(this);
	if (PresentationMode != EMelodiaHybridPresentationMode::Sequence || SessionId == 0
		|| !Rhythm || Rhythm->GetActiveSessionId() != SessionId
		|| PendingEffectSessionId != SessionId || bSequenceEffectConsumed
		|| !FMath::IsFinite(FinalDamage) || FinalDamage < 0.0f)
	{
		return false;
	}
	AActor* Target = GetOwner();
	if (!IsValid(Target))
	{
		return false;
	}
	// Clear before calling the target: death/outcome callbacks may re-enter here.
	PendingEffectSessionId = 0;
	bSequenceEffectConsumed = true;
	// A stock miss (zero) is a resolved effect too. It spends the session without
	// writing HP, permitting the normal return to Flow.
	if (FinalDamage == 0.0f)
	{
		return true;
	}
	FDamageEvent DamageEvent;
	Target->TakeDamage(FinalDamage, DamageEvent, nullptr, nullptr);
	return true;
}

bool UMelodiaHybridEncounterComponent::ApplyResolvedFlowDamage(const float FinalDamage)
{
	AActor* Target = GetOwner();
	if (PresentationMode != EMelodiaHybridPresentationMode::Flow || !IsValid(Target) || !Target->CanBeDamaged()
		|| !FMath::IsFinite(FinalDamage) || FinalDamage <= 0.0f)
	{
		return false;
	}
	FDamageEvent DamageEvent;
	return Target->TakeDamage(FinalDamage, DamageEvent, nullptr, nullptr) > 0.0f;
}
