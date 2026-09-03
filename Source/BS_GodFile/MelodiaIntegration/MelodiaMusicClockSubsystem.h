#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Containers/Ticker.h"
#include "Harmonix/MusicalTimebase.h"
#include "MelodiaMusicClockSubsystem.generated.h"

class UMusicClockComponent;
class UMelodiaAudioComponent;

/**
 * Where the current musical time is coming from.
 *
 * Harmonix is authored musical time (tempo map, bars, sections, calibrated
 * timebases) and is always preferred.  Quartz is the sample-accurate battle
 * transport and provides beat phase only.  There is deliberately no third
 * option: when neither is running the project has no musical time, and
 * presentation code must degrade rather than invent a beat.
 */
UENUM(BlueprintType)
enum class EMelodiaMusicClockSource : uint8
{
	None		UMETA(DisplayName = "None"),
	Harmonix	UMETA(DisplayName = "Harmonix"),
	Quartz		UMETA(DisplayName = "Quartz")
};

/**
 * One sample of musical time.  Read-only presentation data.
 *
 * Fields marked "Harmonix only" are 0 when the active source is Quartz, which
 * knows beat phase but has no authored tempo map.  Always branch on bValid
 * before using anything here.
 */
USTRUCT(BlueprintType)
struct FMelodiaMusicTime
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	bool bValid = false;

	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	EMelodiaMusicClockSource Source = EMelodiaMusicClockSource::None;

	/** 0..1 position within the current beat.  The value presentation should drive pulses from. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	float BeatPhase = 0.0f;

	/** Zero-based fractional beat within the current bar. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	float BeatInBar = 0.0f;

	/** Fractional beats since the start of the authored content.  Harmonix only. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	float TotalBeats = 0.0f;

	/** One-based bar number.  Harmonix only. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	int32 Bar = 0;

	/** Beats per minute at the current position. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	float TempoBPM = 0.0f;

	/** Seconds per beat at the current position.  0 when the tempo is unknown. */
	UPROPERTY(BlueprintReadOnly, Category = "Melodia|Music Clock")
	float SecondsPerBeat = 0.0f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMelodiaBeatEvent, int32, BeatNumber, int32, BeatInBar);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaBarEvent, int32, BarNumber);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMelodiaMusicClockSourceChanged, EMelodiaMusicClockSource, NewSource);

/**
 * The project's single source of musical time.
 *
 * AUTHORITY (Decisions 009 and 011, Harmonix MIDI Rhythm Contract 2026-07-29):
 * this subsystem is presentation-only.  It never issues a command, computes
 * damage, mutates party/inventory/quest/save state, or advances a turn.  The
 * stock TurnBasedJRPG controller owns all of that.  Nothing here may be wired
 * into a damage path.
 *
 * DELEGATION: all musical time comes from Harmonix (authored tempo map) or
 * Quartz (sample-accurate battle transport).  Wall-clock accumulators are not
 * permitted anywhere in the project -- they drift against real audio within a
 * minute and produce timing that feels wrong for reasons players cannot name.
 * If neither clock is running, HasMusicalTime() is false and consumers must
 * degrade gracefully instead of fabricating a beat.
 *
 * TIMEBASE: use ExperiencedTime to score player input (what the player is
 * actually hearing and seeing) and VideoRenderTime to drive visuals.  Using
 * one where the other belongs is the difference between a rhythm layer that
 * feels tight and one that feels mushy.
 */
UCLASS()
class BS_GODFILE_API UMelodiaMusicClockSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void OnWorldBeginPlay(UWorld& InWorld) override;

	/**
	 * Put a running Harmonix clock on the battle controller and register it.
	 *
	 * Until this existed, HasMusicalTime() was false in every session: the
	 * presentation component's HarmonixClock property was never assigned, no
	 * MetaSound music actor was ever placed, and the Quartz fallback needed a
	 * UMelodiaAudioComponent that no actor carried. Every consumer is gated on
	 * that one bool, so BeatPhase and BeatPulse sat at 0.0 forever -- which is
	 * why all 89 assets bound to MPC_Melodia_Palette rendered flat and the OSC
	 * beat feed to TouchDesigner (port 9000) never sent a packet, since the send
	 * lives inside the same branch.
	 *
	 * This is NOT the hand-rolled 120 BPM sine that used to live in
	 * MelodiaAudioReactivePresentationSubsystem and was deliberately deleted for
	 * drifting against 128 BPM source music. This is Harmonix's own clock in its
	 * sanctioned WallClock mode, registered through the normal path, so
	 * HasMusicalTime() is honestly true and every consumer reads a real tempo
	 * map rather than an invented one. WallClock needs no MIDI asset and no
	 * audio: FWallClockMusicClockDriver falls back to DefaultMaps when TempoMap
	 * is null.
	 *
	 * Runs at world begin play, not battle start, because the beat is published
	 * in battle or not -- exploration ambience is meant to get musical time for
	 * free. Idempotent: an authored MetaSound-driven clock registered later
	 * still wins, because RegisterMusicClock prefers the most recent running one.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Clock")
	bool EnsureBattleControllerMusicClock();

	/**
	 * Project-wide accessor, matching UMelodiaPersonaSubsystem::Get.  Any actor,
	 * widget, or component can reach musical time through this without knowing
	 * which clock is live.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock", meta = (WorldContext = "WorldContextObject"))
	static UMelodiaMusicClockSubsystem* Get(const UObject* WorldContextObject);

	/**
	 * One-node ambient beat phase (0..1) on the visual timebase.  Safe to call
	 * from anything, anywhere; returns 0 when no music is playing.
	 *
	 * This is the cheap way to make the world feel scored -- lantern flicker,
	 * idle sway, petal drift, UI breathing.  It is presentation only and is not
	 * restricted to battle.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock", meta = (WorldContext = "WorldContextObject"))
	static float GetMusicBeatPhase(const UObject* WorldContextObject);

	/**
	 * Smooth 0..1 pulse that peaks on the beat, for driving intensity directly.
	 * Usually what ambient callers want instead of raw phase, which sawtooths.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock", meta = (WorldContext = "WorldContextObject"))
	static float GetMusicPulse(const UObject* WorldContextObject);

	/** Timebase presentation should use for visuals. */
	static constexpr ECalibratedMusicTimebase VisualTimebase = ECalibratedMusicTimebase::VideoRenderTime;

	/** Timebase input scoring must use. */
	static constexpr ECalibratedMusicTimebase InputTimebase = ECalibratedMusicTimebase::ExperiencedTime;

	/**
	 * Register the authored Harmonix clock.  Call from the presentation actor
	 * that owns the MetaSound music source.  The most recently registered
	 * running clock wins.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Clock")
	void RegisterMusicClock(UMusicClockComponent* InClock);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Clock")
	void UnregisterMusicClock(UMusicClockComponent* InClock);

	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	UMusicClockComponent* GetActiveMusicClock() const;

	/**
	 * Register a project-owned Quartz transport as the fallback clock. Harmonix
	 * still wins whenever its registered clock is running. The subsystem keeps
	 * only a weak reference and never owns or starts combat gameplay.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Clock")
	void RegisterQuartzAudioComponent(UMelodiaAudioComponent* InAudioComponent);

	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Clock")
	void UnregisterQuartzAudioComponent(UMelodiaAudioComponent* InAudioComponent);

	/** True when Harmonix or Quartz is actually running and the rhythm layer is enabled. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	bool HasMusicalTime() const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	EMelodiaMusicClockSource GetClockSource() const;

	/** Full musical-time sample.  Defaults to the visual timebase. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	FMelodiaMusicTime GetMusicTime(ECalibratedMusicTimebase Timebase = ECalibratedMusicTimebase::VideoRenderTime) const;

	/** 0..1 within the current beat.  Returns 0 when there is no musical time. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetBeatPhase(ECalibratedMusicTimebase Timebase = ECalibratedMusicTimebase::VideoRenderTime) const;

	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetTempoBPM() const;

	/**
	 * Seconds until the next beat boundary, for landing a transition on the beat.
	 *
	 * **Returns 0 when no music is playing.** That is deliberate and load-bearing:
	 * a caller that delays by this value degrades to "act immediately" rather
	 * than waiting forever for a beat that will never arrive. Never write a
	 * transition that waits on a beat *event* -- ask for the delay instead.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetSecondsToNextBeat() const;

	/**
	 * Seconds until the next bar boundary. Returns 0 with no music, and falls
	 * back to the next beat under Quartz, which has no bar length.
	 *
	 * Prefer GetSecondsToNextBeat for turn transitions: waiting a whole bar can
	 * add ~2s at 120 BPM, which reads as the game being unresponsive.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetSecondsToNextBar() const;

	/**
	 * Length of one musical subdivision in seconds -- 4 for sixteenths, 3 for
	 * triplets, 1 for a whole beat.
	 *
	 * Intended for pacing the dialogue typewriter to the track so text renders
	 * on musical subdivisions instead of a static interval. Returns 0 when no
	 * music is playing; callers must fall back to their authored constant.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetSubdivisionSeconds(int32 Divisions = 4) const;

	/**
	 * Signed milliseconds from now to the nearest beat, measured on the input
	 * timebase and corrected by the calibration offset.  Negative is early.
	 *
	 * This is a measurement, not a judgement: it returns how far off the beat
	 * the player was.  Grading it into a presentation tier is
	 * UMelodiaJRPGPresentationRhythmComponent's job, and the result may only
	 * drive visuals and audio -- never damage.
	 */
	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetTimingErrorMsToNearestBeat() const;

	/**
	 * Player-facing audio/visual calibration offset in milliseconds, applied to
	 * every input timing measurement.  Owned by UMelodiaGameUserSettings; this
	 * is the runtime mirror.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Music Clock")
	void SetCalibrationOffsetMs(float InOffsetMs);

	UFUNCTION(BlueprintPure, Category = "Melodia|Music Clock")
	float GetCalibrationOffsetMs() const { return CalibrationOffsetMs; }

	/** Beat boundary crossed.  BeatNumber is running; BeatInBar is zero-based within the bar. */
	UPROPERTY(BlueprintAssignable, Category = "Melodia|Music Clock")
	FMelodiaBeatEvent OnMelodiaBeat;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Music Clock")
	FMelodiaBarEvent OnMelodiaBar;

	UPROPERTY(BlueprintAssignable, Category = "Melodia|Music Clock")
	FMelodiaMusicClockSourceChanged OnClockSourceChanged;

private:
	// Dynamic multicast targets for the Harmonix clock component.
	UFUNCTION()
	void HandleHarmonixBeat(int BeatNumber, int BeatInBar);
	UFUNCTION()
	void HandleHarmonixBar(int BarNumber);

	void BindHarmonixClock(UMusicClockComponent* InClock);
	void UnbindHarmonixClock(UMusicClockComponent* InClock);

	/** Returns the explicitly registered project-owned Quartz battle transport. */
	UMelodiaAudioComponent* ResolveQuartzAudioComponent() const;

	bool IsHarmonixClockRunning() const;
	bool IsQuartzClockRunning() const;

	/** Polls the Quartz beat boundary and refreshes the reported source. */
	bool TickClock(float DeltaTime);

	// Weak pointers deliberately carry no UPROPERTY: they must not keep the
	// clock or battle controller alive, and UHT does not accept mutable
	// reflected properties.
	TWeakObjectPtr<UMusicClockComponent> ActiveMusicClock;
	TWeakObjectPtr<UMelodiaAudioComponent> RegisteredQuartzAudio;

	FTSTicker::FDelegateHandle TickerHandle;

	EMelodiaMusicClockSource ReportedSource = EMelodiaMusicClockSource::None;
	float CalibrationOffsetMs = 0.0f;

	/** Quartz-only beat-edge detection; unused while Harmonix drives events. */
	int32 LastQuartzBeatIndex = -1;
	int32 QuartzRunningBeat = 0;
};
