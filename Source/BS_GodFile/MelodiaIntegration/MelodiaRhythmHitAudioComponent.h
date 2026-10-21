#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MetasoundSource.h"
#include "MelodiaRhythmCombatTypes.h"
#include "MelodiaRhythmHitAudioComponent.generated.h"

class UMelodiaRhythmCombatSubsystem;
class USoundConcurrency;
class UAudioComponent;
class USoundClass;

/**
 * Per-note hit SFX for the rhythm layer. Presentation-only.
 *
 * WHY THIS EXISTS: FMelodiaLaneHitJudged is broadcast once per JUDGED PRESS
 * (misses included) by UMelodiaRhythmCombatSubsystem, carrying LaneIndex,
 * Grade and TimingErrorMs. Its own doc comment says per-press presentation
 * binds there, not to OnRhythmComplete -- which fires once per phrase and
 * would give a whole bar one sound. As of 2026-09-25 the delegate had ZERO
 * bindings anywhere in the project (Monolith reflection across every HUD /
 * BattleUI / Rhythm Blueprint on disk), so the rhythm layer was silent.
 *
 * ONE GRAPH, NOT FOUR: the grade is a PARAMETER, not an asset. A rhythm hit
 * layer only sounds like one instrument if Perfect, Great, Good and Miss are
 * four expressions of the same voice; four separate MetaSounds would drift
 * apart the first time someone retuned one of them, and four assets is four
 * parallel implementations of one thing. The graph branches on HitGrade.
 *
 * AUTHORITY: presentation-only. This never applies damage, mutates a result,
 * or influences a grade. It reacts to a judgement that has already been made.
 * It reads the rhythm combat subsystem; it is not the combat authority.
 *
 * TIMING: the attack is fired with ZERO added delay. Humanising the TIMING
 * makes a rhythm game feel broken -- the player is scored against
 * ExperiencedTime, so any offset between the press and the sound reads as
 * input lag. Humanise the TIMBRE instead (lane spread, per-hit pitch/volume
 * jitter) and let the reverb tail land late, which is desirable.
 */
UCLASS(ClassGroup = (Melodia), meta = (BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaRhythmHitAudioComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaRhythmHitAudioComponent();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** True once the delegate is bound and the graph is assigned. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm|Audio")
	bool IsAudioReady() const { return bAudioReady; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm|Audio")
	int32 GetPlayedHitCount() const { return PlayedHitCount; }

	/** Hits suppressed by the voice budget. Surfaced so it is diagnosable. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Rhythm|Audio")
	int32 GetDroppedHitCount() const { return DroppedHitCount; }

	/** Manual fire, for authoring a UI preview. Runtime binds the delegate. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Rhythm|Audio")
	void PlayHit(int32 LaneIndex, EMelodiaSkillGrade Grade, float TimingErrorMs = 0.0f);

protected:
	/** Signature must match FMelodiaLaneHitJudged exactly. */
	UFUNCTION()
	void HandleLaneHitJudged(int32 LaneIndex, EMelodiaSkillGrade Grade, float TimingErrorMs);

	/** One-shot cleanup: a hit is a transient voice, not a resident component. */
	UFUNCTION()
	void HandleVoiceFinished(UAudioComponent* Finished);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|Assets")
	TObjectPtr<UMetaSoundSource> HitMetaSound = nullptr;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|Assets")
	TObjectPtr<USoundConcurrency> HitConcurrency = nullptr;

	/**
	 * Semitones added per lane. FOUR, not five: a 4-step major seventh
	 * (C-E-G-B) is the dream-pop register this game lives in, while a 5-step
	 * spread puts a major 7th in the stack that clashes under dense chords.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio", meta = (ClampMin = "0.0", ClampMax = "12.0"))
	float LanePitchSpreadSemitones = 4.0f;

	/** +/- cents of random pitch per hit. Breaks up 4-on-the-bar repetition. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio", meta = (ClampMin = "0.0", ClampMax = "200.0"))
	float PitchJitterCents = 25.0f;
	// SonicIdentity grade assets (optional override)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|SonicIdentity")
	TObjectPtr<USoundBase> HitPerfect = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|SonicIdentity")
	TObjectPtr<USoundBase> HitGreat = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|SonicIdentity")
	TObjectPtr<USoundBase> HitGood = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|SonicIdentity")
	TObjectPtr<USoundBase> HitMiss = nullptr;
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio|SonicIdentity")
	bool bPreferSonicIdentity = true;
	/** +/- fraction of base volume, per hit. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Melodia|Rhythm|Audio", meta = (ClampMin = "0.0", ClampMax = "0.5"))
	float VolumeJitter = 0.12f;

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Audio|Voice", meta = (ClampMin = "1", ClampMax = "32"))
	int32 MaxConcurrentVoices = 8;

	/** grade enum value as a float: Miss 0, Good 1, Great 2, Perfect 3. */
	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Audio|MetaSound")
	FName GradeParameter = TEXT("HitGrade");

	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Audio|MetaSound")
	FName LaneParameter = TEXT("HitLane");

	/** Normalised 0..1 error. Deliberately UNUSED by the graph for now: timbre
	 *  driven by timing error risks sounding broken rather than informative. */
	UPROPERTY(EditAnywhere, Category = "Melodia|Rhythm|Audio|MetaSound")
	FName TimingParameter = TEXT("HitTimingMs");

	UPROPERTY(Transient)
	TArray<TWeakObjectPtr<UAudioComponent>> ActiveVoices;

	UPROPERTY(Transient)
	TObjectPtr<UMelodiaRhythmCombatSubsystem> RhythmSubsystem = nullptr;

	int32 PlayedHitCount = 0;
	int32 DroppedHitCount = 0;
	bool bAudioReady = false;
};
