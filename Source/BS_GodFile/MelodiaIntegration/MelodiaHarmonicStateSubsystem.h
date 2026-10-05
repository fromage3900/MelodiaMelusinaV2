#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaHarmonicStateSubsystem.generated.h"

class UMaterialParameterCollection;
struct FMelodiaMusicTime;

/**
 * Single writer of MPC_Melodia_HarmonicState.
 *
 * This subsystem turns the project's existing musical-time spine (UMelodiaMusicClockSubsystem,
 * read-only) plus the rhythm reactivity note/command events into a continuous harmonic
 * description of the current musical moment: tension, consonance, mode, resolution pressure.
 *
 * Contract (mirrors UMelodiaCymaticsWriterSubsystem / AUDIO_REACTIVE_CANON.md):
 * - READS: UMelodiaMusicClockSubsystem (BeatPhase / BeatInBar / TotalBeats / Bar / TempoBPM),
 *   note presses via UMelodiaRhythmReactivitySubsystem events, the canonical palette's
 *   Bass/Mid/Treble/BeatIntensity for the no-TD fallback lane.
 * - WRITES: MPC_Melodia_HarmonicState only. Nothing else may write it; no second writer exists.
 * - PRESENTATION-ONLY: it publishes musical state. Game systems read it and decide what that
 *   means for aggression, pacing, lighting and palette. Nothing in here computes damage,
 *   advances turns, or owns gameplay.
 *
 * Parameter contract on MPC_Melodia_HarmonicState (all scalars unless noted):
 *   Harmonic_Tension        0..1   Composite tension. Rising through a bar's back half, spiking
 *                                 on dissonant intervals, decaying after a resolution. This is
 *                                 the "how heated is the world right now" lane.
 *   Harmonic_Consonance     0..1   Stability of the current pitch content. 1 at rest / pure
 *                                 consonance, dropping as intervals get rough.
 *   Harmonic_Dissonance     0..1   Raw interval roughness of the last authored notes, decayed.
 *   Harmonic_Mode           0..4   0=neutral/rest, 1=major, 2=minor, 3=dominant(7th), 4=chromatic
 *                                 (aug/dim). Slowly eased, so a pass on a key does not strobe.
 *   Harmonic_Resolution     0..1   How much the tension just released since last frame (positive
 *                                   only). Consumers use it as a "breath" pulse (camera, doors,
 *                                   reverb swell).
 *   Harmonic_BarPhase       0..1   Normalized position inside the 8-beat harmonic cycle the
 *                                 authored content is expected to phrase over.
 *   Harmonic_Tempo          BPM    Tempo mirror for consumers that want a single read.
 *
 * Note-input model:
 * Notes arrive as point events (piano keys, rhythm lanes, cymatic hits all call
 * NotifyPlayedNote). This subsystem keeps a short rolling window of the last N notes and
 * re-evaluates the interval set on each press. Between presses the pitch content decays
 * (each note "forgets" after a few beats) so the state settles toward the consonant rest
 * rather than freezing on whatever was last pressed.
 */
UCLASS()
class BS_GODFILE_API UMelodiaHarmonicStateSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** This subsystem is the sole writer of the harmonic state MPC (always true). */
	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	bool IsSingleWriter() const { return true; }

	/**
	 * Author a played note (MIDI number). Called by presentation/rhythm surfaces that need to
	 * feed the harmonic picture beyond the reactivity pulses they already fire.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Harmonic State")
	void NotifyNote(int32 MidiNoteNumber, float Velocity01 = 1.0f);

	/**
	 * PCG awareness feedback: the fraction of resonant PCG content near the listener (0..1).
	 * Fed by UMelodiaPCGResonanceSensorComponent (read-only data source). This subsystem is
	 * still the sole writer of the lane; the sensor only hands it a number.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Harmonic State")
	void SetPCGResonanceDensity(float Density01);

	/**
	 * Author a chord change explicitly (e.g. from a song section table). Clears the decay
	 * window and seeds the pitch set so the mode/tension lock to the new harmony immediately.
	 * Pass absolute MIDI numbers (60 = C4; relative offsets from the root use 60+offset).
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Harmonic State")
	void SetChord(const TArray<int32>& MidNumbers);

	// ── Read-only consumers (one frame old is fine; everything eases) ───────
	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetTension() const { return Tension; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetConsonance() const { return Consonance; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetDissonance() const { return Dissonance; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetMode() const { return static_cast<float>(Mode); }

	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetResolution() const { return ResolutionPulse; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetBarPhase() const { return BarPhase01; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	float GetPCGResonanceDensity() const { return PCGResonanceDensity; }

	/** True when the tension crossed TensionThreshold upward within the last N frames. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Harmonic State")
	bool IsTense() const;

private:
	bool TickState(float DeltaTime);
	void Evaluate(const FMelodiaMusicTime& Time, float DeltaTime);
	void DecayNotes(float DeltaTime);

	/** MelodiaCore reactivity delegate target (OnNotePlayed). */
	UFUNCTION()
	void OnNotePlayed(int32 MidiNote, EMelodiaRhythmGrade Grade);

	/** Interval roughness 0..1 for a pitch-class distance 0..11. */
	static float IntervalRoughness(int32 Semitones);

	/** Slow exponential approach toward Target at Rate (units/second). */
	static float EaseFloat(float Current, float Target, float Rate, float DeltaTime);

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> StateCollection; // MPC_Melodia_HarmonicState (write)

	FTSTicker::FDelegateHandle TickerHandle;

	/** WorldSubsystem init order is not guaranteed; the note-feed bind retries on tick. */
	bool bNoteFeedBound = false;
	void TryBindNoteFeed();

	// Rolling note window (MIDI number + remaining lifetime in seconds + last-seen intensity)
	struct FActiveNote
	{
		int32 Midi = 0;
		float Lifetime = 0.0f;
		float Energy = 0.0f;
	};
	TArray<FActiveNote> ActiveNotes;
	static constexpr int32 MaxActiveNotes = 8;
	/** Notes forget after this many beats (read through the music clock's seconds-per-beat). */
	float SecondsPerBeat = 0.46875f; // 128 BPM default until the clock reports one

	// Eased outputs (what gets published and what consumers read)
	float Tension = 0.0f;
	float Consonance = 0.5f;
	float Dissonance = 0.0f;
	uint8 Mode = 0;
	float ResolutionPulse = 0.0f;
	float BarPhase01 = 0.0f;

	float LastTensionForResolution = 0.0f;

	/** Eased PCG resonance density lane (0..1), published as PCG_ResonanceDensity. */
	float PCGResonanceDensity = 0.0f;

	/** Above this, IsTense() reports true and the "breath" consumers may act. */
	static constexpr float TensionThreshold = 0.65f;
};
