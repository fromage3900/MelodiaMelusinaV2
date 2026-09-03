#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaRhythmCombatTypes.h"
#include "MelodiaJRPGPresentationRhythmComponent.generated.h"

class UMelodiaAudioComponent;
class UMusicClockComponent;
class UNiagaraSystem;

/**
 * Immutable rhythm feedback for the stock JRPG bridge.  This structure is
 * deliberately presentation-only: PresentationScalar is visual intensity,
 * not a combat multiplier.
 */
USTRUCT(BlueprintType)
struct FJRPGPresentationRhythmResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category="Melodia|JRPG Rhythm")
	EMelodiaRhythmGrade Grade = EMelodiaRhythmGrade::Miss;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|JRPG Rhythm")
	float PresentationScalar = 0.25f;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|JRPG Rhythm")
	int32 HitCount = 0;

	UPROPERTY(BlueprintReadOnly, Category="Melodia|JRPG Rhythm")
	int32 MissCount = 1;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaJRPGPresentationRhythmResult, FJRPGPresentationRhythmResult, Result);

/**
 * A non-authoritative rhythm grading boundary for the stock TurnBasedJRPG
 * flow.  It never starts a Melodia battle session and never changes damage,
 * resources, HP, victory state, or turn state.
 */
UCLASS(ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class BS_GODFILE_API UMelodiaJRPGPresentationRhythmComponent final : public UActorComponent
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	/** BPM used only when no authored Harmonix clock is running. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Quartz", meta=(ClampMin="1.0"))
	float QuartzFallbackBPM = 128.0f;

	/** Starts and registers the stock controller's Quartz fallback transport. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Quartz")
	bool bEnableQuartzFallback = true;

	/** Authored Harmonix clock (owned by the MetaSound music source actor). When set, it is registered into UMelodiaMusicClockSubsystem and preferred over Quartz. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Harmonix")
	TObjectPtr<UMusicClockComponent> HarmonixClock;

	/** Plays the battle BGM (Duvet cover, placeholder fallback) once the music clock is running. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Audio")
	bool bPlayBattleBGM = true;

	/** Metronome click on every integer beat while a session clock is running. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Audio")
	bool bPlayMetronomeClick = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm")
	FMelodiaRhythmWindows RhythmWindows;

	/**
	 * Per-press burst spawned on every judged lane press.
	 *
	 * The default points at NS_Melodia_LaneHit, which currently lives under
	 * Content/EnvSandbox/VFX/Candidates/ -- a loop-output folder that gets swept.
	 * This is a soft pointer and an EditAnywhere property precisely so promoting
	 * the asset out of Candidates/ is a reslot in the Blueprint, not a code edit.
	 * Left empty, no burst spawns and nothing else changes.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Lane FX")
	TSoftObjectPtr<UNiagaraSystem> LaneHitEffect =
		TSoftObjectPtr<UNiagaraSystem>(FSoftObjectPath(
			TEXT("/Game/EnvSandbox/VFX/Candidates/Melodia/NS_Melodia_LaneHit.NS_Melodia_LaneHit")));

	/** Lateral spacing between lane burst origins, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Lane FX", meta=(ClampMin="0.0"))
	float LaneSpacing = 60.0f;

	/** Height above the owner at which lane bursts spawn, in cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Lane FX")
	float LaneHitHeight = 110.0f;

	/**
	 * Spawn the burst on a Miss too. On by default: a press that produces no
	 * visible response at all reads as dropped input rather than as a miss.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|JRPG Rhythm|Lane FX")
	bool bSpawnLaneHitOnMiss = true;

	UPROPERTY(BlueprintAssignable, Category="Melodia|JRPG Rhythm")
	FMelodiaJRPGPresentationRhythmResult OnPresentationRhythmResult;

	/** Classifies one supplied timing error without applying any gameplay effect. */
	UFUNCTION(BlueprintPure, Category="Melodia|JRPG Rhythm")
	FJRPGPresentationRhythmResult EvaluateTimingError(float TimingErrorMs) const;

	/** Emits the presentation result for a UI overlay or VFX listener. */
	UFUNCTION(BlueprintCallable, Category="Melodia|JRPG Rhythm")
	FJRPGPresentationRhythmResult RecordTimingError(float TimingErrorMs);

	/**
	 * Grades an input that happened this instant, taking its timing error from
	 * the music-clock authority on the player's calibrated experienced timebase.
	 * This is the entry point authored skills should use -- callers never
	 * compute timing themselves.
	 *
	 * Returns a Miss-graded result with a zero scalar when no music clock is
	 * running, so a skill invoked without music simply gets no decoration.
	 */
	UFUNCTION(BlueprintCallable, Category="Melodia|JRPG Rhythm")
	FJRPGPresentationRhythmResult RecordInputNow();

private:
	/**
	 * Fans an authoritative rhythm session result out to the presentation
	 * listeners. Bound to UMelodiaRhythmCombatSubsystem::OnRhythmComplete in
	 * BeginPlay and unbound in EndPlay -- this component is world-scoped, which
	 * matches the lifetime of the world subsystem that owns the delegate.
	 *
	 * Presentation only. This must never call ClearPendingDamageMultiplier:
	 * FinishSession has just latched the damage scalar, and the damage notify is
	 * an async callback on a call stack this fan-out knows nothing about, so
	 * clearing here would silently wipe the session's damage back to identity.
	 * (InvalidateSession no longer clears the latch, but it is still not this
	 * component's to call -- presentation does not end authoritative sessions.)
	 */
	UFUNCTION()
	void HandleRhythmSessionCompleted(EMelodiaSkillGrade Grade, int32 HitCount, int32 MissCount);

	/** Metronome edge: plays a click when the music clock crosses a beat boundary. */
	UFUNCTION()
	void HandleMelodiaBeat(int32 BeatNumber, int32 BeatInBar);

	/**
	 * Per-press burst. Bound to UMelodiaRhythmCombatSubsystem::OnLaneHitJudged,
	 * which fires once per judged press -- OnRhythmComplete would give one event
	 * for the whole phrase and cannot punctuate individual notes.
	 *
	 * Presentation-only: reads the judgement, spawns FX, writes no session state.
	 */
	UFUNCTION()
	void HandleLaneHitJudged(int32 LaneIndex, EMelodiaSkillGrade Grade, float TimingErrorMs);

	static float GetPresentationScalar(EMelodiaRhythmGrade Grade);

	TWeakObjectPtr<UMelodiaAudioComponent> RegisteredQuartzAudio;
	TWeakObjectPtr<UMusicClockComponent> RegisteredHarmonixClock;
};
