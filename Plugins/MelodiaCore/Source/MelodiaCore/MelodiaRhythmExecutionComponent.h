// Drives the tight-coupled note highway: song pattern -> beat-synced hits -> damage resolution.
// Adapted from MelodiaMelusina_PROD ΓÇö simplified beat clock (time-based, no Quartz for Phase 2).

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaRulesGenerated.h"
#include "MelodiaSongSkillLibrary.h"
#include "MelodiaSongDataAsset.h"
#include "MelodiaRhythmExecutionComponent.generated.h"

UENUM(BlueprintType)
enum class EMelodiaRhythmExecutionState : uint8
{
	Idle UMETA(DisplayName="Idle"),
	Active UMETA(DisplayName="Active"),
	Resolving UMETA(DisplayName="Resolving")
};

UENUM(BlueprintType)
enum class EMelodiaRhythmCommandType : uint8
{
	None UMETA(DisplayName="None"),
	Basic UMETA(DisplayName="Basic"),
	Skill UMETA(DisplayName="Skill")
};

USTRUCT(BlueprintType)
struct FMelodiaRhythmExecutionResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	EMelodiaRhythmCommandType CommandType = EMelodiaRhythmCommandType::None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	FName SkillId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 SkillCost = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	float SkillScalar = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	float AverageGradeMultiplier = MelodiaRulesGen::MissMultiplier;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 HitCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 PerfectCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 MissCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 TotalNotes = 0;
};

USTRUCT(BlueprintType)
struct FMelodiaHighwayNote
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	float TargetBeat = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 Pitch = 60;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	int32 LaneIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	EMelodiaRhythmGrade Grade = EMelodiaRhythmGrade::Miss;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	bool bResolved = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm")
	bool bCountsAsHit = false;
};

UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaRhythmExecutionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaRhythmExecutionComponent();

	virtual void BeginPlay() override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	FMelodiaRhythmWindows RhythmWindows;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	float LeadInBeats = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	float ScrollBeatsAhead = 2.5f;

	/** BPM for the time-based beat clock. Used directly when bUseQuartzClock is false, and as the fallback source otherwise. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	float BPM = 128.0f;

	/** When true, GetCurrentBeatPosition() reads from the owning actor's UMelodiaAudioComponent Quartz
	 * battle clock (StartBattleClock/PlayBGMQuantized) instead of the wall-clock accumulator. Automatically
	 * falls back to the wall-clock accumulator if no MelodiaAudioComponent is present or its battle clock
	 * isn't running, so this is safe to leave on. Judgment windows/multipliers are unaffected either way. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	bool bUseQuartzClock = true;

	/** Optional song pack ΓÇö Basic uses Songs[ActiveSongIndex].BasicChartNotes when non-empty. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	TSoftObjectPtr<UMelodiaSongDataAsset> SongPack;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Rhythm Execution")
	int32 ActiveSongIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	EMelodiaRhythmExecutionState ExecutionState = EMelodiaRhythmExecutionState::Idle;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	bool bSkillExecution = false;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	FMelodiaGeneratedSpell ActiveSpell;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	FName ActiveSkillId = NAME_None;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	TArray<FMelodiaHighwayNote> ActiveNotes;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	int32 CurrentNoteIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	int32 ResolvedNoteCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	float ExecutionStartBeat = 0.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	float AverageGradeMultiplier = 1.0f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	FMelodiaRhythmExecutionResult LastExecutionResult;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	int32 PerfectCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|Rhythm Execution")
	int32 HitCount = 0;

	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm Execution")
	bool BeginSkillExecutionById(FName SkillId);

	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm Execution")
	bool BeginBasicExecution();

	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm Execution")
	bool TryHitCurrentNote();

	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm Execution")
	bool TryHitNoteInLane(int32 LaneIndex);

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm Execution")
	bool IsExecutionActive() const;

	UFUNCTION(BlueprintPure, Category="Melodia|Rhythm Execution")
	float GetCurrentBeatPosition() const;

	UFUNCTION(BlueprintCallable, Category="Melodia|Rhythm Execution")
	void CancelExecution();

private:
	void BuildNotesFromSong(const TArray<int32>& NotePitches, const TArray<float>& NoteDurations, EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials, const bool bSkill);
	void BuildNotesFromChart(const TArray<FMelodiaChartNote>& ChartNotes, EMelodiaInstrument Instrument, const TArray<FMelodiaSongMaterialInput>& Materials, const bool bSkill);
	void BuildBasicNotes();
	void ResolveMissedNotes();
	void FinishExecution();
	float GetBeatLengthSeconds() const;
	FMelodiaRhythmExecutionResult BuildExecutionResult() const;

	/** Time-based beat accumulator (replaces Quartz MusicManager for Phase 2). */
	float AccumulatedBeatPosition = 0.0f;
	double ExecutionStartTime = 0.0;
	int32 PendingSkillCost = 0;
	float PendingSkillScalar = 1.0f;
	EMelodiaRhythmCommandType PendingCommandType = EMelodiaRhythmCommandType::None;

	/** Last integer beat for metronome click deduplication */
	int32 LastMetronomeBeat = -1;
};
