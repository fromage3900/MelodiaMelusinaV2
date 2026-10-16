#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "MelodiaCoreRulesLibrary.h"
#include "MelodiaAudioComponent.generated.h"

class USoundBase;
class UAudioComponent;
class UQuartzClockHandle;

UCLASS(Blueprintable, ClassGroup=(Melodia), meta=(BlueprintSpawnableComponent))
class MELODIACORE_API UMelodiaAudioComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UMelodiaAudioComponent();

	virtual void BeginPlay() override;

	/** Play a hit sound corresponding to the given grade */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void PlayHitSFX(EMelodiaRhythmGrade Grade);

	/** Play a miss sound effect */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void PlayMissSFX();

	/** Play a metronome click on the current beat */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void PlayMetronomeClick();

	/** Play a MIDI note on NoteSample, pitch-shifted from its C4 root. Used by the
	 * interactable PCG music nodes. DurationSeconds is kept for callers; the
	 * sample's own decay sets the length. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void PlayMusicalNote(int32 MidiNote, float DurationSeconds = 0.18f, float Velocity = 0.75f);

	/** Start BGM for a given skill/song */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void PlayBGM(FName SkillId);

	/** Record which skill the current battle is using; PlayBGMQuantized sources the BGM from it. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void SetCurrentSkill(FName SkillId) { CurrentSkillId = SkillId; }

	/** Stop current BGM */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio")
	void StopBGM();

	/** Start (or restart) the Quartz battle clock at the given BPM. No-op if Quartz is unavailable (RhythmExecutionComponent falls back to its wall-clock accumulator in that case). */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio|Quartz")
	void StartBattleClock(float InBPM = 128.0f);

	/** Play the placeholder 128-BPM battle BGM quantized to the next bar boundary on the battle clock. Starts the clock first if it isn't already running. */
	UFUNCTION(BlueprintCallable, Category="Melodia|Audio|Quartz")
	void PlayBGMQuantized();

	/** Current song beat position (fractional, zero-based within the bar) from the Quartz transport. Returns 0 if the battle clock isn't running. */
	UFUNCTION(BlueprintPure, Category="Melodia|Audio|Quartz")
	float GetSongBeatPosition() const;

	/** Whether the Quartz battle clock exists and is currently running. */
	UFUNCTION(BlueprintPure, Category="Melodia|Audio|Quartz")
	bool IsBattleClockRunning() const;

	/** BPM the battle clock was last started at. 0 when the clock has never been started. */
	UFUNCTION(BlueprintPure, Category="Melodia|Audio|Quartz")
	float GetBattleClockBPM() const { return BattleClockBPM; }

	/** Master volume scalar for SFX */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Audio", meta=(ClampMin="0.0", ClampMax="1.0"))
	float SFXVolume = 0.5f;

	/** One authored C4 note every SFX, grade tone and musical note is pitched from. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Audio")
	TSoftObjectPtr<USoundBase> NoteSample = TSoftObjectPtr<USoundBase>(FSoftObjectPath(TEXT("/Game/Melodia/Audio/WaveHarp/SW_WaveHarp_Orchestra_C4.SW_WaveHarp_Orchestra_C4")));

	/** Master volume scalar for BGM */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Melodia|Audio", meta=(ClampMin="0.0", ClampMax="1.0"))
	float BGMVolume = 0.3f;

private:
	/** Play NoteSample at FrequencyHz (pitch relative to its C4 root). */
	void PlayTone(float FrequencyHz, float VolumeMultiplier = 1.0f);

	UPROPERTY()
	TObjectPtr<UAudioComponent> BGMComponent;

	/** Quartz clock driving battle-synced BGM playback and GetSongBeatPosition. */
	UPROPERTY()
	TObjectPtr<UQuartzClockHandle> BattleClockHandle;

	/** Tempo the battle clock was started at, so consumers can convert beats to milliseconds. */
	float BattleClockBPM = 0.0f;

	/** Skill id of the current battle, used to source per-skill BGM. */
	FName CurrentSkillId;

	static const FName BattleClockName;
};
