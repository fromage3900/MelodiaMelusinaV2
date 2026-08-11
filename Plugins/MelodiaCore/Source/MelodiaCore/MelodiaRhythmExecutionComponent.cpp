// Drives the tight-coupled note highway: song pattern -> beat-synced hits -> damage resolution.
// Adapted from MelodiaMelusina_PROD ΓÇö time-based beat clock replaces Quartz for Phase 2.

#include "MelodiaRhythmExecutionComponent.h"
#include "MelodiaAudioComponent.h"
#include "MelodiaBattleArena.h"
#include "MelodiaBattleSession.h"
#include "MelodiaRhythmHUDWidget.h"
#include "MelodiaSongSkillLibrary.h"
#include "MelodiaRhythmReactivitySubsystem.h"

namespace
{
FLinearColor GradeTint(const EMelodiaRhythmGrade Grade, const FLinearColor& DefaultTint)
{
	switch (Grade)
	{
	case EMelodiaRhythmGrade::Perfect:
		return FLinearColor(0.42f, 1.0f, 0.72f, 1.0f);   // Mint green
	case EMelodiaRhythmGrade::Great:
		return FLinearColor(0.62f, 0.92f, 1.0f, 1.0f);    // Cyan
	case EMelodiaRhythmGrade::Good:
		return FLinearColor(0.98f, 0.88f, 0.36f, 1.0f);   // Gold
	case EMelodiaRhythmGrade::Miss:
		return FLinearColor(0.96f, 0.28f, 0.42f, 1.0f);   // Rose
	default:
		return DefaultTint;
	}
}
}

UMelodiaRhythmExecutionComponent::UMelodiaRhythmExecutionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
}

void UMelodiaRhythmExecutionComponent::BeginPlay()
{
	Super::BeginPlay();
}

void UMelodiaRhythmExecutionComponent::TickComponent(const float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	if (ExecutionState != EMelodiaRhythmExecutionState::Active)
	{
		return;
	}

	// Advance the wall-clock accumulator. Used directly when bUseQuartzClock is false, and as the
	// automatic fallback GetCurrentBeatPosition() returns if the Quartz battle clock isn't running.
	const float BeatsPerSecond = BPM / 60.0f;
	AccumulatedBeatPosition += DeltaTime * BeatsPerSecond;

	const float CurrentBeatPosition = GetCurrentBeatPosition();

	// Metronome click on each integer beat
	const int32 CurrentWholeBeat = FMath::FloorToInt(CurrentBeatPosition);
	if (CurrentWholeBeat > LastMetronomeBeat && CurrentWholeBeat >= 0)
	{
		LastMetronomeBeat = CurrentWholeBeat;
		if (UMelodiaAudioComponent* Audio = GetOwner()->FindComponentByClass<UMelodiaAudioComponent>())
		{
			Audio->PlayMetronomeClick();
		}
		if (UWorld* World = GetWorld())
		{
			if (UMelodiaRhythmReactivitySubsystem* Reactivity = World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
			{
				Reactivity->NotifyBeat(BPM, CurrentBeatPosition - FMath::FloorToFloat(CurrentBeatPosition));
			}
		}
	}

	ResolveMissedNotes();

	if (ResolvedNoteCount >= ActiveNotes.Num())
	{
		FinishExecution();
	}
}

bool UMelodiaRhythmExecutionComponent::BeginSkillExecutionById(const FName SkillId)
{
	if (ExecutionState != EMelodiaRhythmExecutionState::Idle)
	{
		return false;
	}

	FMelodiaSongSkillRecipe SkillRecipe;
	if (!UMelodiaSongSkillLibrary::FindSongSkill(SkillId, SkillRecipe))
	{
		return false;
	}

	ActiveSkillId = SkillId;
	bSkillExecution = true;
	PendingCommandType = EMelodiaRhythmCommandType::Skill;
	PendingSkillCost = SkillRecipe.SPCostOverride > 0 ? SkillRecipe.SPCostOverride : 1;
	PendingSkillScalar = FMath::Max(0.0f, SkillRecipe.PowerScalar);
	if (SkillRecipe.ChartNotes.Num() > 0)
	{
		BuildNotesFromChart(SkillRecipe.ChartNotes, SkillRecipe.Instrument, SkillRecipe.Materials, true);
	}
	else
	{
		BuildNotesFromSong(
			SkillRecipe.NotePitches,
			SkillRecipe.NoteDurations,
			SkillRecipe.Instrument,
			SkillRecipe.Materials,
			true);
	}

	if (ActiveSpell.SpellElement != SkillRecipe.Element)
	{
		ActiveSpell.SpellElement = SkillRecipe.Element;
	}

	if (SkillRecipe.PowerScalar > 0.0f)
	{
		ActiveSpell.Power *= SkillRecipe.PowerScalar;
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia: Skill execution started ΓÇö %s (%d notes)"),
		*SkillRecipe.DisplayName.ToString(), ActiveNotes.Num());

	if (ActiveNotes.Num() > 0)
	{
		if (UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this))
		{
			Session->NotifyRhythmExecutionStarted();
		}
		return true;
	}
	CancelExecution();
	return false;
}

bool UMelodiaRhythmExecutionComponent::BeginBasicExecution()
{
	if (ExecutionState != EMelodiaRhythmExecutionState::Idle)
	{
		return false;
	}

	bSkillExecution = false;
	ActiveSkillId = NAME_None;
	PendingCommandType = EMelodiaRhythmCommandType::Basic;
	PendingSkillCost = 0;
	PendingSkillScalar = 1.0f;
	BuildBasicNotes();

	UE_LOG(LogTemp, Log, TEXT("Melodia: Basic execution started (%d notes)"), ActiveNotes.Num());
	if (ActiveNotes.Num() > 0)
	{
		if (UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this))
		{
			Session->NotifyRhythmExecutionStarted();
		}
		return true;
	}
	CancelExecution();
	return false;
}

bool UMelodiaRhythmExecutionComponent::TryHitCurrentNote()
{
	if (ExecutionState != EMelodiaRhythmExecutionState::Active || !ActiveNotes.IsValidIndex(CurrentNoteIndex))
	{
		return false;
	}

	FMelodiaHighwayNote& Note = ActiveNotes[CurrentNoteIndex];
	if (Note.bResolved)
	{
		return false;
	}

	const float BeatPosition = GetCurrentBeatPosition();
	const float TimingErrorMs = FMath::Abs(BeatPosition - Note.TargetBeat) * GetBeatLengthSeconds() * 1000.0f;

	const FMelodiaRhythmGradeResult GradeResult = UMelodiaCoreRulesLibrary::GradeInputFromTimingErrorMs(TimingErrorMs, RhythmWindows);
	Note.Grade = GradeResult.Grade;
	Note.bCountsAsHit = GradeResult.bCountsAsHit;
	Note.bResolved = true;

	if (GradeResult.Grade == EMelodiaRhythmGrade::Perfect)
	{
		++PerfectCount;
	}
	if (GradeResult.bCountsAsHit)
	{
		++HitCount;
	}

	UE_LOG(LogTemp, Log, TEXT("Melodia: Note hit! Grade=%s (%.1fms error), Beat=%.2f/Target=%.2f"),
		*GradeResult.DisplayText.ToString(), TimingErrorMs, BeatPosition, Note.TargetBeat);

	if (UMelodiaAudioComponent* Audio = GetOwner()->FindComponentByClass<UMelodiaAudioComponent>())
	{
		Audio->PlayHitSFX(GradeResult.Grade);
	}

	if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
	{
		HUD->SetJudgment(GradeResult.DisplayText);
		HUD->PushFloatingCombatText(GradeResult.DisplayText.ToString(), true, GradeTint(GradeResult.Grade, FLinearColor::White));
		HUD->DoPulse();
		if (GradeResult.Grade == EMelodiaRhythmGrade::Perfect)
		{
			HUD->TriggerSparkleBurst();
			HUD->NotifyPerfectHit();
		}
	}

	// Feel: Perfect gets a micro-freeze + pop; Great a light shake.
	if (AMelodiaBattleArena* Arena = Cast<AMelodiaBattleArena>(GetOwner()))
	{
		if (GradeResult.Grade == EMelodiaRhythmGrade::Perfect)
		{
			Arena->Hitstop(0.05f, 0.08f);
			Arena->PostProcessPop(1.0f);
			Arena->PlayShake(0.3f);
		}
		else if (GradeResult.Grade == EMelodiaRhythmGrade::Great)
		{
			Arena->PlayShake(0.15f);
		}
	}

	++CurrentNoteIndex;
	++ResolvedNoteCount;
	return true;
}

bool UMelodiaRhythmExecutionComponent::TryHitNoteInLane(int32 LaneIndex)
{
	if (ExecutionState != EMelodiaRhythmExecutionState::Active)
	{
		return false;
	}

	// Resolve only the nearest currently hittable note.  Selecting the first
	// unresolved lane entry allowed an early press to consume a future note.
	const float BeatPosition = GetCurrentBeatPosition();
	const float BeatLengthSeconds = GetBeatLengthSeconds();
	int32 BestNoteIndex = INDEX_NONE;
	float BestCorrectedErrorMs = TNumericLimits<float>::Max();
	for (int32 i = 0; i < ActiveNotes.Num(); ++i)
	{
		FMelodiaHighwayNote& Note = ActiveNotes[i];
		if (Note.LaneIndex != LaneIndex || Note.bResolved)
		{
			continue;
		}

		const float RawErrorMs = FMath::Abs(BeatPosition - Note.TargetBeat) * BeatLengthSeconds * 1000.0f;
		const float CorrectedErrorMs = FMath::Abs(RawErrorMs - RhythmWindows.LatencyOffsetMs);
		if (CorrectedErrorMs <= RhythmWindows.GoodWindowMs && CorrectedErrorMs < BestCorrectedErrorMs)
		{
			BestCorrectedErrorMs = CorrectedErrorMs;
			BestNoteIndex = i;
		}
	}

	if (BestNoteIndex == INDEX_NONE)
	{
		return false;
	}

	CurrentNoteIndex = BestNoteIndex;
	return TryHitCurrentNote();
}

bool UMelodiaRhythmExecutionComponent::IsExecutionActive() const
{
	return ExecutionState == EMelodiaRhythmExecutionState::Active;
}

float UMelodiaRhythmExecutionComponent::GetCurrentBeatPosition() const
{
	if (bUseQuartzClock)
	{
		if (const AActor* Owner = GetOwner())
		{
			if (UMelodiaAudioComponent* Audio = Owner->FindComponentByClass<UMelodiaAudioComponent>())
			{
				if (Audio->IsBattleClockRunning())
				{
					return Audio->GetSongBeatPosition();
				}
			}
		}
	}
	return AccumulatedBeatPosition;
}

void UMelodiaRhythmExecutionComponent::CancelExecution()
{
	ExecutionState = EMelodiaRhythmExecutionState::Idle;
	ActiveNotes.Reset();
	CurrentNoteIndex = 0;
	ResolvedNoteCount = 0;
	bSkillExecution = false;
	ActiveSkillId = NAME_None;
	PendingCommandType = EMelodiaRhythmCommandType::None;
	PendingSkillCost = 0;
	PendingSkillScalar = 1.0f;
	AccumulatedBeatPosition = 0.0f;
	LastMetronomeBeat = -1;
}

void UMelodiaRhythmExecutionComponent::BuildNotesFromSong(const TArray<int32>& NotePitches, const TArray<float>& NoteDurations, const EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials, const bool bSkill)
{
	ActiveSpell = UMelodiaCoreRulesLibrary::GenerateSpellFromSong(NotePitches, NoteDurations, Instrument, Materials);

	// Reset beat clock
	AccumulatedBeatPosition = 0.0f;
	ExecutionStartBeat = 0.0f;
	ExecutionStartTime = FPlatformTime::Seconds();

	ActiveNotes.Reset();
	CurrentNoteIndex = 0;
	ResolvedNoteCount = 0;
	PerfectCount = 0;
	HitCount = 0;

	float BeatCursor = LeadInBeats;
	const int32 NoteCount = FMath::Max(ActiveSpell.HitCount, NotePitches.Num());
	for (int32 Index = 0; Index < NoteCount; ++Index)
	{
		FMelodiaHighwayNote Note;
		Note.TargetBeat = BeatCursor;
		Note.Pitch = NotePitches.IsValidIndex(Index) ? NotePitches[Index] : 60;
		Note.LaneIndex = Index % 4; // Distribute across 4 lanes
		ActiveNotes.Add(Note);

		const float DurationBeats = NoteDurations.IsValidIndex(Index) ? FMath::Max(0.25f, NoteDurations[Index]) : 1.0f;
		BeatCursor += DurationBeats;
	}

	ExecutionState = EMelodiaRhythmExecutionState::Active;
}

void UMelodiaRhythmExecutionComponent::BuildNotesFromChart(const TArray<FMelodiaChartNote>& ChartNotes, const EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials, const bool bSkill)
{
	TArray<int32> Pitches;
	TArray<float> Durations;
	Pitches.Reserve(ChartNotes.Num());
	Durations.Reserve(ChartNotes.Num());
	for (const FMelodiaChartNote& ChartNote : ChartNotes)
	{
		Pitches.Add(ChartNote.Pitch);
		Durations.Add(FMath::Max(0.25f, ChartNote.DurationBeats));
	}

	ActiveSpell = UMelodiaCoreRulesLibrary::GenerateSpellFromSong(Pitches, Durations, Instrument, Materials);

	AccumulatedBeatPosition = 0.0f;
	ExecutionStartBeat = 0.0f;
	ExecutionStartTime = FPlatformTime::Seconds();

	ActiveNotes.Reset();
	CurrentNoteIndex = 0;
	ResolvedNoteCount = 0;
	PerfectCount = 0;
	HitCount = 0;

	float BeatCursor = LeadInBeats;
	bool bUseAbsoluteBeats = false;
	for (const FMelodiaChartNote& ChartNote : ChartNotes)
	{
		if (ChartNote.TargetBeat > 0.0f)
		{
			bUseAbsoluteBeats = true;
			break;
		}
	}

	for (int32 Index = 0; Index < ChartNotes.Num(); ++Index)
	{
		const FMelodiaChartNote& ChartNote = ChartNotes[Index];
		FMelodiaHighwayNote Note;
		if (bUseAbsoluteBeats)
		{
			Note.TargetBeat = LeadInBeats + FMath::Max(0.0f, ChartNote.TargetBeat);
		}
		else
		{
			Note.TargetBeat = BeatCursor;
			BeatCursor += FMath::Max(0.25f, ChartNote.DurationBeats);
		}
		Note.Pitch = ChartNote.Pitch;
		Note.LaneIndex = FMath::Clamp(ChartNote.LaneIndex, 0, 3);
		ActiveNotes.Add(Note);
	}

	ExecutionState = EMelodiaRhythmExecutionState::Active;
}

void UMelodiaRhythmExecutionComponent::BuildBasicNotes()
{
	// Authored 4-lane Basic chart (research: DataAsset chart notes > Index%4 fallback)
	TArray<FMelodiaChartNote> BasicChart;
	auto AddNote = [&BasicChart](float Beat, int32 Lane, int32 Pitch, float Dur)
	{
		FMelodiaChartNote N;
		N.TargetBeat = Beat;
		N.LaneIndex = Lane;
		N.Pitch = Pitch;
		N.DurationBeats = Dur;
		BasicChart.Add(N);
	};
	AddNote(0.0f, 0, 64, 1.0f);
	AddNote(1.0f, 1, 67, 1.0f);
	AddNote(2.0f, 2, 71, 1.0f);
	AddNote(3.0f, 3, 72, 1.0f);
	TArray<FMelodiaSongMaterialInput> EmptyMaterials;
	BuildNotesFromChart(BasicChart, EMelodiaInstrument::MusicBox, EmptyMaterials, false);
}

void UMelodiaRhythmExecutionComponent::ResolveMissedNotes()
{
	const float BeatPosition = GetCurrentBeatPosition();
	const float BeatLength = GetBeatLengthSeconds();
	const float MissWindowBeats = RhythmWindows.GoodWindowMs / FMath::Max(BeatLength * 1000.0f, KINDA_SMALL_NUMBER);

	// Scan all notes ΓÇö lanes are independent so any note can time out regardless of CurrentNoteIndex
	for (int32 i = 0; i < ActiveNotes.Num(); ++i)
	{
		FMelodiaHighwayNote& Note = ActiveNotes[i];
		if (Note.bResolved)
		{
			continue;
		}

		if (BeatPosition <= Note.TargetBeat + MissWindowBeats)
		{
			continue;
		}

		Note.Grade = EMelodiaRhythmGrade::Miss;
		Note.bCountsAsHit = false;
		Note.bResolved = true;
		++ResolvedNoteCount;

		UE_LOG(LogTemp, Log, TEXT("Melodia: Note MISSED at beat %.2f (target was %.2f) Lane=%d"),
			BeatPosition, Note.TargetBeat, Note.LaneIndex);

		if (UMelodiaAudioComponent* Audio = GetOwner()->FindComponentByClass<UMelodiaAudioComponent>())
		{
			Audio->PlayMissSFX();
		}

		if (UMelodiaRhythmHUDWidget* HUD = UMelodiaRhythmHUDWidget::FindFirst(this))
		{
			HUD->SetJudgment(FText::FromString(TEXT("Miss")));
			HUD->PushFloatingCombatText(TEXT("Miss"), true, GradeTint(EMelodiaRhythmGrade::Miss, FLinearColor::White));
		}
	}
}

void UMelodiaRhythmExecutionComponent::FinishExecution()
{
	if (ExecutionState != EMelodiaRhythmExecutionState::Active)
	{
		return;
	}

	ExecutionState = EMelodiaRhythmExecutionState::Resolving;

	LastExecutionResult = BuildExecutionResult();
	AverageGradeMultiplier = LastExecutionResult.AverageGradeMultiplier;

	UE_LOG(LogTemp, Log, TEXT("Melodia: Execution finished ΓÇö %d/%d hits, %d perfect, avg mult=%.2f"),
		HitCount, ActiveNotes.Num(), PerfectCount, AverageGradeMultiplier);

	// Notify battle session
	if (UMelodiaBattleSession* Session = UMelodiaBattleSession::Get(this))
	{
		Session->NotifyRhythmExecutionFinished(LastExecutionResult);
	}

	CancelExecution();
}

float UMelodiaRhythmExecutionComponent::GetBeatLengthSeconds() const
{
	return 60.0f / FMath::Max(1.0f, BPM);
}

FMelodiaRhythmExecutionResult UMelodiaRhythmExecutionComponent::BuildExecutionResult() const
{
	FMelodiaRhythmExecutionResult Result;
	Result.CommandType = PendingCommandType;
	Result.SkillId = PendingCommandType == EMelodiaRhythmCommandType::Skill ? ActiveSkillId : NAME_None;
	Result.SkillCost = PendingSkillCost;
	Result.SkillScalar = PendingSkillScalar;
	Result.HitCount = HitCount;
	Result.PerfectCount = PerfectCount;
	Result.TotalNotes = ActiveNotes.Num();

	float MultiplierSum = 0.0f;
	int32 ComboCount = 0;
	int32 Misses = 0;
	for (const FMelodiaHighwayNote& Note : ActiveNotes)
	{
		MultiplierSum += UMelodiaCoreRulesLibrary::GetRhythmCombatMultiplier(Note.Grade, ComboCount);
		if (Note.Grade == EMelodiaRhythmGrade::Miss)
		{
			++Misses;
		}
		++ComboCount;
	}

	Result.MissCount = Misses;
	Result.AverageGradeMultiplier = Result.TotalNotes > 0
		? MultiplierSum / static_cast<float>(Result.TotalNotes)
		: 0.4f;
	return Result;
}
