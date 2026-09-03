#include "MelodiaRhythmCombatSubsystem.h"
#include "MelodiaRhythmSkillDefinition.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaTokenWalletSubsystem.h"
#include "MelodiaSongDataAsset.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaIntegrationConfig.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/AssetData.h"
#include "Engine/AssetManager.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "Stats/Stats.h"

UMelodiaRhythmCombatSubsystem* UMelodiaRhythmCombatSubsystem::Get(const UObject* WorldContextObject)
{
	if (const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull) : nullptr)
	{
		return World->GetSubsystem<UMelodiaRhythmCombatSubsystem>();
	}
	return nullptr;
}

void UMelodiaRhythmCombatSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Auto-discover all skill DataAssets under the configured directory.
	// This runs once at subsystem init; Blueprint-side registrations (e.g. from
	// an in-game unlock) can still call RegisterSkill() later.
	{
		FAssetRegistryModule& AssetRegistry = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
		TArray<FAssetData> AssetList;
		FARFilter Filter;
		Filter.ClassPaths.Add(UMelodiaRhythmSkillDefinition::StaticClass()->GetClassPathName());
		Filter.bRecursivePaths = true;
		Filter.PackagePaths.Add(TEXT("/Game/MelodiaIntegration/Config"));
		AssetRegistry.Get().GetAssets(Filter, AssetList);

		SkillCatalog.Reset();
		for (const FAssetData& Asset : AssetList)
		{
			if (UMelodiaRhythmSkillDefinition* Skill = Cast<UMelodiaRhythmSkillDefinition>(Asset.GetAsset()))
			{
				if (!Skill->SkillId.IsNone())
				{
					SkillCatalog.Add(Skill->SkillId, Skill);
				}
			}
		}
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia rhythm combat subsystem loaded %d skills from asset registry."), SkillCatalog.Num());
}

void UMelodiaRhythmCombatSubsystem::Deinitialize()
{
	// Stop ticking and drop the HUD reference before teardown; a world torn down
	// mid-session must not leave IsTickable() true against a dead subsystem.
	bSessionActive = false;
	SessionNotes.Reset();
	BoundHUD.Reset();

	// The world is going away; there is no turn to advance and ProcessEvent into
	// a tearing-down world is not safe. Drop the deferral without dispatching.
	DeferredSkill = nullptr;

	// Restore before the world tears down so a scaled unit that outlives this
	// subsystem (PIE restart reusing actors) never carries a buff forward.
	RestoreRhythmAttackScalar();

	SkillCatalog.Reset();
	Super::Deinitialize();
}

void UMelodiaRhythmCombatSubsystem::RegisterSkill(UMelodiaRhythmSkillDefinition* InSkill)
{
	if (InSkill && !InSkill->SkillId.IsNone())
	{
		SkillCatalog.Add(InSkill->SkillId, InSkill);
	}
}

UMelodiaRhythmSkillDefinition* UMelodiaRhythmCombatSubsystem::FindSkill(FName SkillId) const
{
	if (const TObjectPtr<UMelodiaRhythmSkillDefinition>* Found = SkillCatalog.Find(SkillId))
	{
		return *Found;
	}
	return nullptr;
}

int32 UMelodiaRhythmCombatSubsystem::StartSession(FName SkillId)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaRhythmCombatSubsystem_StartSession);
	// A new session invalidates any previous one and its pending request.
	InvalidateSession();

	// A new session supersedes the previous session's damage latch, so it starts
	// at identity. Reset here rather than in ResetSessionAccumulators: that path
	// is shared with InvalidateSession, which must leave a finished session's
	// latch intact for the anim-notify still to read. Unconditional and before
	// the skill lookup, so even a StartSession that fails to find its skill
	// cannot leave a stale multiplier behind.
	PendingDamageMultiplier = 1.0f;

	// Only registered skills can start an authoritative session.
	const UMelodiaRhythmSkillDefinition* Skill = FindSkill(SkillId);
	if (!Skill)
	{
		return 0;
	}

	ActiveSkillId = SkillId;
	ActiveSessionId = NextSessionId++;
	bResultAccepted = false;
	bHasPendingRequest = false;
	PendingRequest = FMelodiaRhythmEffectRequest();

	// Clears chart state and accumulators, so activation must follow it.
	ResetSessionAccumulators();

	// Seed the tempo from the live clock; falls back to the skill's authored BPM
	// when no clock is running, so an uncharted session still advances sanely.
	SessionSecondsPerBeat = (Skill->TempoBPM > KINDA_SMALL_NUMBER) ? (60.0f / Skill->TempoBPM) : 0.46875f;
	if (const UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this))
	{
		const FMelodiaMusicTime MusicTime = MusicClock->GetMusicTime();
		if (MusicTime.bValid && MusicTime.SecondsPerBeat > KINDA_SMALL_NUMBER)
		{
			SessionSecondsPerBeat = MusicTime.SecondsPerBeat;
		}
	}

	// The authored window is IntroBeats (lead-in, nothing hittable) + ActiveBeats.
	// Set here, after ResetSessionAccumulators zeroed it and before the chart load
	// reads it, so charted and uncharted sessions alike have a real end beat and
	// can therefore self-close in Tick.
	SessionEndBeat = static_cast<float>(FMath::Max(0, Skill->IntroBeats))
		+ static_cast<float>(FMath::Max(1, Skill->ActiveBeats));

	bSessionCharted = LoadChartForSkill(Skill);
	bSessionActive = true;
	SessionBeat = 0.0f;

	if (!bSessionCharted)
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM session=%d skill=%s started UNCHARTED (beat-proximity grading)"),
			ActiveSessionId, *SkillId.ToString());
	}

	PushHighwayToHUD(bSessionCharted);

	return ActiveSessionId;
}

void UMelodiaRhythmCombatSubsystem::ResetSessionAccumulators()
{
	SessionHitCount = 0;
	SessionMissCount = 0;
	SessionGradeTotal = 0;

	SessionNotes.Reset();
	bSessionActive = false;
	bSessionCharted = false;
	SessionBeat = 0.0f;
	SessionEndBeat = 0.0f;

	// PendingDamageMultiplier is deliberately NOT reset here. It is the output of
	// an already-finished session, not accumulator state, and this function is
	// also reached from InvalidateSession (battle end, save recovery, HUD hide) --
	// resetting it here destroyed a latch the damage notify had not read yet.
	// StartSession owns the reset instead.
}

void UMelodiaRhythmCombatSubsystem::BindRhythmHUD(UMelodiaRhythmHUDWidget* InHUD)
{
	BoundHUD = InHUD;
}

FName UMelodiaRhythmCombatSubsystem::ResolveRhythmSkillId(const UObject* StockSkill) const
{
	if (!StockSkill)
	{
		return NAME_None;
	}

	const UGameInstance* GI = GetWorld() ? GetWorld()->GetGameInstance() : nullptr;
	const UMelodiaNarrativeSubsystem* Narrative = GI ? GI->GetSubsystem<UMelodiaNarrativeSubsystem>() : nullptr;
	const UMelodiaIntegrationConfig* IntegrationConfig = Narrative ? Narrative->Config : nullptr;
	if (!IntegrationConfig)
	{
		return NAME_None;
	}

	// Key on the generated class name as it appears at runtime (e.g. BP_FocusAttack_C).
	const FName ClassName = StockSkill->GetClass()->GetFName();
	if (const FName* Found = IntegrationConfig->StockSkillRhythmIds.Find(ClassName))
	{
		return *Found;
	}

	UE_LOG(LogTemp, Verbose, TEXT("MELODIA_RHYTHM no rhythm id mapped for stock skill class '%s'"),
		*ClassName.ToString());
	return NAME_None;
}

FText UMelodiaRhythmCombatSubsystem::GradeToText(const EMelodiaSkillGrade Grade)
{
	switch (Grade)
	{
	case EMelodiaSkillGrade::Perfect:	return NSLOCTEXT("Melodia", "RhythmPerfect", "PERFECT");
	case EMelodiaSkillGrade::Great:		return NSLOCTEXT("Melodia", "RhythmGreat", "GREAT");
	case EMelodiaSkillGrade::Good:		return NSLOCTEXT("Melodia", "RhythmGood", "GOOD");
	default:							return NSLOCTEXT("Melodia", "RhythmMiss", "MISS");
	}
}

bool UMelodiaRhythmCombatSubsystem::LoadChartForSkill(const UMelodiaRhythmSkillDefinition* Skill)
{
	SessionNotes.Reset();
	if (!Skill)
	{
		return false;
	}

	// PatternAsset is a soft UObject ref so a skill can point at any future chart
	// container; today the only shape we understand is UMelodiaSongDataAsset.
	const UMelodiaSongDataAsset* SongAsset = Cast<UMelodiaSongDataAsset>(Skill->PatternAsset.LoadSynchronous());
	if (!SongAsset || SongAsset->Songs.Num() == 0)
	{
		return false;
	}

	// The quantum draw may have latched which chart in the song asset plays this
	// battle. Empty latch / out of range / service down -> first authored chart,
	// the classical default.
	const int32 SongIndex = FMath::Clamp(SongSelectionIndices.FindRef(Skill->SkillId), 0, SongAsset->Songs.Num() - 1);
	const FMelodiaSongChart& Chart = SongAsset->Songs[SongIndex];
	if (Chart.BasicChartNotes.Num() == 0)
	{
		return false;
	}

	UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM song selection skill=%s chart=%d \"%s\""),
		*Skill->SkillId.ToString(), SongIndex, *Chart.SongTitle.ToString());

	// SessionEndBeat is owned by StartSession (it must exist for uncharted sessions
	// too); this only reads it to clip the chart to the playable window.
	const float IntroBeats = static_cast<float>(FMath::Max(0, Skill->IntroBeats));

	// Rebase: chart beat 0 maps to session beat IntroBeats, so the player gets the
	// lead-in to read the highway before the first note is live.
	for (const FMelodiaChartNote& Note : Chart.BasicChartNotes)
	{
		const float SessionTargetBeat = IntroBeats + Note.TargetBeat;
		if (SessionTargetBeat > SessionEndBeat)
		{
			continue;
		}

		FMelodiaHighwayNote Highway;
		Highway.TargetBeat = SessionTargetBeat;
		Highway.Pitch = Note.Pitch;
		Highway.LaneIndex = FMath::Clamp(Note.LaneIndex, 0, 3);
		Highway.bResolved = false;
		Highway.bCountsAsHit = false;
		SessionNotes.Add(Highway);
	}

	SessionNotes.Sort([](const FMelodiaHighwayNote& A, const FMelodiaHighwayNote& B)
	{
		return A.TargetBeat < B.TargetBeat;
	});

	UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM chart loaded skill=%s notes=%d window=%.2f beats"),
		*Skill->SkillId.ToString(), SessionNotes.Num(), SessionEndBeat);

	return SessionNotes.Num() > 0;
}

void UMelodiaRhythmCombatSubsystem::PushHighwayToHUD(const bool bActive)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaRhythmCombatSubsystem_PushHighwayToHUD);
	UMelodiaRhythmHUDWidget* HUD = BoundHUD.Get();
	if (!HUD)
	{
		return;
	}

	if (!bActive)
	{
		HUD->SetNoteHighwayActive(false, TArray<FMelodiaHighwayNote>(), 0.0f, ScrollBeatsAhead);
		return;
	}

	// This integration drives the shared native-painted widget independently of
	// UMelodiaBattleSession, whose ambient mode is normally Exploration in a
	// stock JRPG encounter. Select the highway presentation explicitly while the
	// authoritative rhythm session is active.
	HUD->SetHUDMode(EMelodiaHUDMode::BattleHighway);

	// Only hand the HUD the notes currently on screen. Passing the whole chart
	// would make the widget re-filter it every frame.
	TArray<FMelodiaHighwayNote> Visible;
	Visible.Reserve(SessionNotes.Num());
	for (const FMelodiaHighwayNote& Note : SessionNotes)
	{
		if (Note.bResolved)
		{
			continue;
		}
		if (Note.TargetBeat >= SessionBeat - ExpiryGraceBeats && Note.TargetBeat <= SessionBeat + ScrollBeatsAhead)
		{
			Visible.Add(Note);
		}
	}

	HUD->SetNoteHighwayActive(true, Visible, SessionBeat, ScrollBeatsAhead);
}

void UMelodiaRhythmCombatSubsystem::Tick(const float DeltaTime)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaRhythmCombatSubsystem_Tick);
	Super::Tick(DeltaTime);

	if (!bSessionActive)
	{
		return;
	}

	// Advance session-relative musical position. SecondsPerBeat is resampled from
	// the clock each tick so a tempo change mid-session does not desync the chart.
	if (const UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this))
	{
		const FMelodiaMusicTime MusicTime = MusicClock->GetMusicTime();
		if (MusicTime.bValid && MusicTime.SecondsPerBeat > KINDA_SMALL_NUMBER)
		{
			SessionSecondsPerBeat = MusicTime.SecondsPerBeat;
		}
	}

	SessionBeat += DeltaTime / FMath::Max(SessionSecondsPerBeat, KINDA_SMALL_NUMBER);

	// Expire notes the player never hit. A note can only expire once it is past
	// the widest legal hit window, so this never steals a hittable note.
	if (bSessionCharted)
	{
		for (FMelodiaHighwayNote& Note : SessionNotes)
		{
			if (!Note.bResolved && SessionBeat > Note.TargetBeat + ExpiryGraceBeats)
			{
				Note.bResolved = true;
				Note.bCountsAsHit = false;
				++SessionMissCount;
				UE_LOG(LogTemp, Verbose, TEXT("MELODIA_RHYTHM note expired lane=%d beat=%.3f"),
					Note.LaneIndex, Note.TargetBeat);
			}
		}
	}

	PushHighwayToHUD(true);

	// Every session ends on its own once its authored window closes. Charted or
	// not, SessionEndBeat comes from the skill's IntroBeats + ActiveBeats, so no
	// session depends on an external caller to close it.
	if (SessionBeat > SessionEndBeat + ExpiryGraceBeats)
	{
		FinishSession();
	}
}

EMelodiaSkillGrade UMelodiaRhythmCombatSubsystem::RegisterLaneHit(const int32 LaneIndex)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaRhythmCombatSubsystem_RegisterLaneHit);
	// A press outside a session must never bank a hit.
	if (ActiveSessionId == 0 || bResultAccepted)
	{
		return EMelodiaSkillGrade::Miss;
	}

	float TimingErrorMs = 0.0f;

	if (bSessionCharted)
	{
		// Charted: judge the press against the nearest unresolved note IN THIS LANE.
		// Pressing a lane with no pending note is a Miss -- otherwise mashing all
		// four lanes would guarantee a hit on every note.
		FMelodiaHighwayNote* Nearest = nullptr;
		float NearestDelta = TNumericLimits<float>::Max();
		for (FMelodiaHighwayNote& Note : SessionNotes)
		{
			if (Note.bResolved || Note.LaneIndex != LaneIndex)
			{
				continue;
			}
			const float Delta = FMath::Abs(Note.TargetBeat - SessionBeat);
			if (Delta < NearestDelta)
			{
				NearestDelta = Delta;
				Nearest = &Note;
			}
		}

		if (!Nearest || NearestDelta > ExpiryGraceBeats)
		{
			++SessionMissCount;
			UE_LOG(LogTemp, Verbose, TEXT("MELODIA_RHYTHM lane=%d pressed with no note in range"), LaneIndex);
			// A judged miss inside a live session. Timing error is genuinely
			// undefined here (there was no note to be early or late against), so
			// it reports 0 rather than a fabricated number.
			if (UMelodiaRhythmHUDWidget* HUD = BoundHUD.Get())
			{
				HUD->SetJudgment(GradeToText(EMelodiaSkillGrade::Miss));
			}
			OnLaneHitJudged.Broadcast(LaneIndex, EMelodiaSkillGrade::Miss, 0.0f);
			return EMelodiaSkillGrade::Miss;
		}

		// Consume the note now so a second press in the same lane cannot double-score it.
		Nearest->bResolved = true;
		TimingErrorMs = NearestDelta * SessionSecondsPerBeat * 1000.0f;
		Nearest->bCountsAsHit = TimingErrorMs <= RhythmWindows.GoodWindowMs;
	}
	else
	{
		// Uncharted fallback: grade against the nearest beat. With no clock running
		// there is no meaningful timing error, so the press grades as a Miss rather
		// than silently scoring against wall time.
		const UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this);
		if (!MusicClock || !MusicClock->HasMusicalTime())
		{
			++SessionMissCount;
			UE_LOG(LogTemp, Verbose, TEXT("MELODIA_RHYTHM lane=%d graded Miss (no musical time)"), LaneIndex);
			if (UMelodiaRhythmHUDWidget* HUD = BoundHUD.Get())
			{
				HUD->SetJudgment(GradeToText(EMelodiaSkillGrade::Miss));
			}
			OnLaneHitJudged.Broadcast(LaneIndex, EMelodiaSkillGrade::Miss, 0.0f);
			return EMelodiaSkillGrade::Miss;
		}

		TimingErrorMs = MusicClock->GetTimingErrorMsToNearestBeat();
	}
	const FMelodiaRhythmGradeResult GradeResult =
		UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(FMath::Abs(TimingErrorMs), RhythmWindows);

	// EMelodiaRhythmGrade and EMelodiaSkillGrade declare the same four members in
	// the same order; map explicitly rather than casting so a future divergence
	// in either enum becomes a compile error instead of a silent mis-grade.
	EMelodiaSkillGrade Grade = EMelodiaSkillGrade::Miss;
	switch (GradeResult.Grade)
	{
	case EMelodiaRhythmGrade::Perfect:	Grade = EMelodiaSkillGrade::Perfect;	break;
	case EMelodiaRhythmGrade::Great:	Grade = EMelodiaSkillGrade::Great;		break;
	case EMelodiaRhythmGrade::Good:		Grade = EMelodiaSkillGrade::Good;		break;
	case EMelodiaRhythmGrade::Miss:		Grade = EMelodiaSkillGrade::Miss;		break;
	}

	if (GradeResult.bCountsAsHit)
	{
		++SessionHitCount;
		SessionGradeTotal += static_cast<int32>(Grade);
	}
	else
	{
		++SessionMissCount;
	}

	// Immediate player-facing feedback -- without this the player has no way to read
	// whether a press landed, which is the difference between a rhythm game and a
	// timing test performed in the dark.
	if (UMelodiaRhythmHUDWidget* HUD = BoundHUD.Get())
	{
		HUD->SetJudgment(GradeToText(Grade));
	}

	UE_LOG(LogTemp, Verbose, TEXT("MELODIA_RHYTHM lane=%d error=%.1fms grade=%s hits=%d misses=%d"),
		LaneIndex, TimingErrorMs, *UEnum::GetValueAsString(Grade), SessionHitCount, SessionMissCount);

	// Per-press presentation seam. Broadcast AFTER the counters and the HUD text
	// so any listener that reads GetSessionHitCount()/GetSessionMissCount() sees
	// this press already counted rather than the previous frame's totals.
	OnLaneHitJudged.Broadcast(LaneIndex, Grade, TimingErrorMs);

	return Grade;
}

bool UMelodiaRhythmCombatSubsystem::FinishSession()
{
	if (ActiveSessionId == 0 || bResultAccepted)
	{
		return false;
	}

	// Aggregate grade is the mean of the graded hits. No hits at all is a Miss --
	// a session the player never connected with must not score as Good.
	EMelodiaSkillGrade Aggregate = EMelodiaSkillGrade::Miss;
	if (SessionHitCount > 0)
	{
		const int32 Mean = FMath::RoundToInt(static_cast<float>(SessionGradeTotal) / static_cast<float>(SessionHitCount));
		Aggregate = static_cast<EMelodiaSkillGrade>(
			FMath::Clamp(Mean,
				static_cast<int32>(EMelodiaSkillGrade::Miss),
				static_cast<int32>(EMelodiaSkillGrade::Perfect)));
	}

	const int32 Hits = SessionHitCount;
	const int32 Misses = SessionMissCount;

	// SubmitRatedInput remains the only path that validates a result and builds a
	// pending effect request; this wrapper adds no second authority.
	const bool bAccepted = SubmitRatedInput(Aggregate, Hits, Misses);

	// Latch the effective scalar for the anim-notify that lands later. Only on
	// acceptance -- a rejected result must leave stock damage at identity.
	if (bAccepted)
	{
		PendingDamageMultiplier = FMath::Max(0.0f, PendingRequest.BaseMagnitude * PendingRequest.RhythmScalar);
	}

	UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM session=%d finished grade=%s hits=%d misses=%d accepted=%s"),
		ActiveSessionId, *UEnum::GetValueAsString(Aggregate), Hits, Misses, bAccepted ? TEXT("true") : TEXT("false"));

	// Stop ticking and clear the highway before anyone reacts to the broadcast,
	// so a listener that immediately starts another session sees a clean slate.
	bSessionActive = false;
	PushHighwayToHUD(false);

	// Session verdict. The per-press feedback in RegisterLaneHit leaves the last
	// single press on screen; without this the player reads one note's grade as
	// the whole session's result. Damage-frame feedback (floating combat text,
	// damage flash) is deliberately NOT pushed here -- it belongs on the notify
	// that actually applies the damage, not on session close.
	if (UMelodiaRhythmHUDWidget* HUD = BoundHUD.Get())
	{
		HUD->SetJudgment(GradeToText(Aggregate));
		HUD->ShowBattleStatus(FString::Printf(TEXT("%d / %d"), Hits, Hits + Misses));

		if (Aggregate == EMelodiaSkillGrade::Perfect || Aggregate == EMelodiaSkillGrade::Great)
		{
			HUD->TriggerSparkleBurst();
		}
	}

	// Broadcast even when the result was rejected. Listeners use this to pop the
	// rhythm input context and hide the highway; gating it on acceptance would
	// strand the player in a rhythm HUD they can no longer dismiss.
	OnRhythmComplete.Broadcast(Aggregate, Hits, Misses);

	// The deferred stock invocation this session was started for. PendingDamageMultiplier
	// was latched above, so the montage's damage notify now reads a real scalar
	// instead of identity. Cleared before dispatch: if a listener above already
	// superseded the session (StartSession -> InvalidateSession), DeferredSkill is
	// null here and nothing fires twice.
	if (UObject* SkillToUse = DeferredSkill)
	{
		DeferredSkill = nullptr;

		// Fold the latched scalar into the attacker's stats so the stock damage
		// calculation consumes it. Must precede dispatch: stock reads the stats
		// during the montage that UseSkill starts.
		ApplyRhythmAttackScalar();

		InvokeStockUseSkill(SkillToUse);
	}

	// Consume the pending effect request now that the skill has been dispatched.
	// An OnRhythmComplete listener may already have popped it (documented BP
	// DealDamage seam); ConsumePendingRequest is exactly-once either way, and this
	// fallback guarantees the wallet integration (SP cost / shard reward) runs
	// once per accepted session even with zero Blueprint wiring. It clears only
	// the request -- never PendingDamageMultiplier -- so the montage's damage
	// notify still reads the latched scalar. A listener that superseded the
	// session during the broadcast cleared bHasPendingRequest, making this a
	// harmless no-op.
	FMelodiaRhythmEffectRequest ConsumedRequest;
	if (ConsumePendingRequest(ConsumedRequest))
	{
		UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM session=%d effect request consumed by rhythm subsystem (effect=%s scalar=%.2f)"),
			ActiveSessionId, *UEnum::GetValueAsString(ConsumedRequest.EffectType), ConsumedRequest.RhythmScalar);
	}

	return bAccepted;
}

bool UMelodiaRhythmCombatSubsystem::UseSkillWithRhythm(UObject* StockSkill)
{
	if (!IsValid(StockSkill))
	{
		return false;
	}

	const UMelodiaMusicClockSubsystem* MusicClock = UMelodiaMusicClockSubsystem::Get(this);
	if (!MusicClock || !MusicClock->HasMusicalTime())
	{
		// No clock means no meaningful rhythm session. Reset exactly as a new
		// session would, then preserve the stock skill's immediate call stack and
		// identity damage. This is also the melodia.Rhythm.Disable A/B path.
		InvalidateSession();
		ClearPendingDamageMultiplier();
		UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM musical time unavailable; invoking stock UseSkill on '%s' immediately."),
			*StockSkill->GetName());
		InvokeStockUseSkill(StockSkill);
		return false;
	}

	// StartSession invalidates any previous session first, which is also what
	// drops a stale deferral -- so the assignment below must follow this call.
	const int32 SessionId = StartSession(ResolveRhythmSkillId(StockSkill));
	if (SessionId == 0)
	{
		// Unmapped or unregistered skill: stock behaviour on this call stack.
		InvokeStockUseSkill(StockSkill);
		return false;
	}

	DeferredSkill = StockSkill;
	UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM session=%d deferring UseSkill on '%s' until the session closes"),
		SessionId, *StockSkill->GetName());
	return true;
}

void UMelodiaRhythmCombatSubsystem::ApplyRhythmAttackScalar()
{
	// Lazy restore: a previous turn's scale is undone here rather than on a timer,
	// so stats cannot compound across turns even if a session ended abnormally.
	RestoreRhythmAttackScalar();

	const float Scalar = PendingDamageMultiplier;
	if (FMath::IsNearlyEqual(Scalar, 1.0f))
	{
		// Identity multiplier is stock behaviour. Touch nothing.
		return;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	AActor* BattleController = nullptr;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_BattleController")))
		{
			BattleController = *It;
			break;
		}
	}
	if (!BattleController)
	{
		// Ordinary outside battle -- a rhythm session can close with no fight running.
		return;
	}

	const FObjectPropertyBase* AttackerProperty =
		FindFProperty<FObjectPropertyBase>(BattleController->GetClass(), TEXT("currentAttackingUnit"));
	if (!AttackerProperty)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_RHYTHM_ATTACK '%s' has no 'currentAttackingUnit'; the stock contract changed."),
			*BattleController->GetClass()->GetName());
		return;
	}

	UObject* Unit = AttackerProperty->GetObjectPropertyValue_InContainer(BattleController);
	if (!IsValid(Unit))
	{
		// No unit is mid-turn. Expected between turns; not an error.
		return;
	}

	FIntProperty* MinAttack = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("minAttack"));
	FIntProperty* MaxAttack = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("maxAttack"));
	if (!MinAttack || !MaxAttack)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_RHYTHM_ATTACK unit '%s' lacks minAttack/maxAttack; the stock contract changed."),
			*Unit->GetClass()->GetName());
		return;
	}

	SavedMinAttack = MinAttack->GetPropertyValue_InContainer(Unit);
	SavedMaxAttack = MaxAttack->GetPropertyValue_InContainer(Unit);

	// Round rather than truncate so a 1.5x Perfect on a 40-56 spread reads 60-84,
	// not 60-83; stock stats are whole numbers and the UI prints them verbatim.
	MinAttack->SetPropertyValue_InContainer(Unit, FMath::RoundToInt(SavedMinAttack * Scalar));
	MaxAttack->SetPropertyValue_InContainer(Unit, FMath::RoundToInt(SavedMaxAttack * Scalar));

	ScaledAttackUnit = Unit;
	bAttackScalarApplied = true;

	UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM_ATTACK_SCALED unit=%s scalar=%.2f attack %d-%d -> %d-%d"),
		*Unit->GetName(), Scalar, SavedMinAttack, SavedMaxAttack,
		MinAttack->GetPropertyValue_InContainer(Unit), MaxAttack->GetPropertyValue_InContainer(Unit));
}

void UMelodiaRhythmCombatSubsystem::RestoreRhythmAttackScalar()
{
	if (!bAttackScalarApplied)
	{
		return;
	}

	// Clear the flag first: a unit destroyed mid-battle must not leave the
	// subsystem believing a scale is still outstanding.
	bAttackScalarApplied = false;

	UObject* Unit = ScaledAttackUnit.Get();
	ScaledAttackUnit = nullptr;
	if (!IsValid(Unit))
	{
		return;
	}

	FIntProperty* MinAttack = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("minAttack"));
	FIntProperty* MaxAttack = FindFProperty<FIntProperty>(Unit->GetClass(), TEXT("maxAttack"));
	if (!MinAttack || !MaxAttack)
	{
		return;
	}

	MinAttack->SetPropertyValue_InContainer(Unit, SavedMinAttack);
	MaxAttack->SetPropertyValue_InContainer(Unit, SavedMaxAttack);

	UE_LOG(LogTemp, Log, TEXT("MELODIA_RHYTHM_ATTACK_RESTORED unit=%s attack restored to %d-%d"),
		*Unit->GetName(), SavedMinAttack, SavedMaxAttack);
}

void UMelodiaRhythmCombatSubsystem::InvokeStockUseSkill(UObject* StockSkill)
{
	if (!IsValid(StockSkill))
	{
		return;
	}

	UFunction* UseSkill = StockSkill->FindFunction(TEXT("UseSkill"));
	if (!UseSkill)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_RHYTHM stock skill '%s' (%s) has no UseSkill; the turn cannot advance."),
			*StockSkill->GetName(), *StockSkill->GetClass()->GetName());
		return;
	}

	// UseSkill is a no-parameter call on BP_BattleSkillBase (self only). If the
	// stock signature ever grows a parameter, fail loudly rather than passing a
	// zeroed block that would silently mean something.
	if (UseSkill->ParmsSize != 0)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_RHYTHM stock UseSkill on '%s' takes parameters (%d bytes); refusing to guess them."),
			*StockSkill->GetClass()->GetName(), UseSkill->ParmsSize);
		return;
	}

	StockSkill->ProcessEvent(UseSkill, nullptr);
}

bool UMelodiaRhythmCombatSubsystem::SubmitResult(const FMelodiaAuthoritativeRhythmResult& InResult)
{
	// No active session, already accepted a result, or invalid result: reject.
	if (ActiveSessionId == 0 || bResultAccepted || !InResult.bValid)
	{
		return false;
	}

	// Duplicate session ID: reject.
	if (InResult.SessionId != ActiveSessionId)
	{
		return false;
	}

	UMelodiaRhythmSkillDefinition* Skill = FindSkill(ActiveSkillId);
	if (!Skill)
	{
		return false;
	}

	bResultAccepted = true;
	PendingRequest = BuildEffectRequest(Skill, InResult);
	bHasPendingRequest = true;

	return true;
}

bool UMelodiaRhythmCombatSubsystem::SubmitRatedInput(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount)
{
	// No active session, already accepted a result: reject.
	if (ActiveSessionId == 0 || bResultAccepted)
	{
		return false;
	}

	UMelodiaRhythmSkillDefinition* Skill = FindSkill(ActiveSkillId);
	if (!Skill)
	{
		return false;
	}

	// Build the authoritative result from the graded input. The presentation
	// layer never computes damage; it only supplies the grade and hit/miss
	// counts. The subsystem owns the conversion to an authoritative result.
	FMelodiaAuthoritativeRhythmResult Result;
	Result.bValid = true;
	Result.SessionId = ActiveSessionId;
	Result.Grade = Grade;
	Result.HitCount = HitCount;
	Result.MissCount = MissCount;
	Result.NoteCount = HitCount + MissCount;
	Result.Accuracy = Result.NoteCount > 0 ? static_cast<float>(HitCount) / static_cast<float>(Result.NoteCount) : 0.0f;
	Result.ClockSource = UMelodiaMusicClockSubsystem::Get(this) ? UMelodiaMusicClockSubsystem::Get(this)->GetClockSource() : EMelodiaMusicClockSource::None;

	return SubmitResult(Result);
}

bool UMelodiaRhythmCombatSubsystem::HasPendingRequest() const
{
	return bHasPendingRequest;
}

bool UMelodiaRhythmCombatSubsystem::ConsumePendingRequest(FMelodiaRhythmEffectRequest& OutRequest)
{
	if (!bHasPendingRequest)
	{
		return false;
	}

	OutRequest = PendingRequest;
	OutRequest.bConsumed = true;
	bHasPendingRequest = false;
	PendingRequest = FMelodiaRhythmEffectRequest();

	// Wallet integration happens exactly once, on consumption.
	ApplyWalletIntegration(OutRequest);

	return true;
}

void UMelodiaRhythmCombatSubsystem::SetSongSelectionIndex(const FName SkillId, const int32 SongIndex)
{
	SongSelectionIndices.Add(SkillId, FMath::Max(0, SongIndex));
}

void UMelodiaRhythmCombatSubsystem::ClearSongSelections()
{
	SongSelectionIndices.Reset();
}

void UMelodiaRhythmCombatSubsystem::InvalidateSession()
{
	// Drop, do not fire. Every caller is a teardown path -- save recovery, battle
	// end, rhythm-HUD hide, or a superseding StartSession -- so there is no turn
	// left to advance, and dispatching a stock attack during save recovery would
	// be worse than not dispatching one. Warned rather than silent so a session
	// that dies unexpectedly is visible in the log.
	if (DeferredSkill)
	{
		UE_LOG(LogTemp, Warning, TEXT("MELODIA_RHYTHM dropped deferred UseSkill on '%s': session %d invalidated before it closed."),
			*DeferredSkill->GetName(), ActiveSessionId);
		DeferredSkill = nullptr;
	}

	// A dropped session must not leave a buffed attacker behind. Every teardown
	// path funnels through here, so this is where the scale is guaranteed undone.
	RestoreRhythmAttackScalar();

	ActiveSkillId = NAME_None;
	ActiveSessionId = 0;
	bResultAccepted = false;
	bHasPendingRequest = false;
	PendingRequest = FMelodiaRhythmEffectRequest();
	ResetSessionAccumulators();
}

FMelodiaRhythmEffectRequest UMelodiaRhythmCombatSubsystem::BuildEffectRequest(const UMelodiaRhythmSkillDefinition* Skill, const FMelodiaAuthoritativeRhythmResult& InResult) const
{
	FMelodiaRhythmEffectRequest Request;
	Request.SkillId = Skill->SkillId;
	Request.SessionId = InResult.SessionId;
	Request.EffectType = Skill->EffectType;
	Request.BaseMagnitude = Skill->BaseMagnitude;
	Request.RhythmScalar = ResolveMagnitude(Skill, InResult.Grade);
	Request.TargetMode = Skill->TargetMode;
	Request.TargetCount = Skill->TargetCount;
	Request.Duration = Skill->Duration;
	Request.TurnShift = (InResult.Grade == EMelodiaSkillGrade::Great || InResult.Grade == EMelodiaSkillGrade::Perfect)
		? Skill->MaxTurnShift
		: 0;

	return Request;
}

float UMelodiaRhythmCombatSubsystem::ResolveMagnitude(const UMelodiaRhythmSkillDefinition* Skill, EMelodiaSkillGrade Grade) const
{
	switch (Skill->EffectType)
	{
	case EMelodiaRhythmEffectType::Damage:
	case EMelodiaRhythmEffectType::Crit:
		return Skill->DamageMultipliers.Get(Grade);
	case EMelodiaRhythmEffectType::Heal:
	case EMelodiaRhythmEffectType::RemoveDebuff:
		return Skill->HealMultipliers.Get(Grade);
	case EMelodiaRhythmEffectType::Debuff:
		return Skill->ResourceMultipliers.Get(Grade);
	default:
		return 1.0f;
	}
}

void UMelodiaRhythmCombatSubsystem::ApplyWalletIntegration(const FMelodiaRhythmEffectRequest& Request)
{
	// Rhythm skills may spend mana and grant shards as rewards, following the
	// same OnWalletChanged -> UI pattern as UMelodiaTokenWalletSubsystem.
	// No second wallet is created; this is a thin consumer of the canonical one.
	UMelodiaRhythmSkillDefinition* Skill = FindSkill(Request.SkillId);
	if (!Skill)
	{
		return;
	}

	UMelodiaTokenWalletSubsystem* Wallet = UMelodiaTokenWalletSubsystem::Get(this);
	if (!Wallet)
	{
		return;
	}

	// Spend SP cost (mana) when the skill has one.
	if (Skill->SPCost > 0)
	{
		Wallet->TrySpendMana(static_cast<float>(Skill->SPCost));
	}

	// Grant a small shard reward on strong grades (Perfect/Greater).
	if (Request.RhythmScalar >= 1.2f)
	{
		Wallet->TryGrantShards(TEXT("Forte"), 1, FName(*FString::Printf(TEXT("RhythmSkill_%s_%d"), *Request.SkillId.ToString(), Request.SessionId)));
	}
}
