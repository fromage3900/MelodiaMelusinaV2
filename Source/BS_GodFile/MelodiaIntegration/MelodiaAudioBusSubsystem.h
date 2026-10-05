#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/WorldSubsystem.h"
#include "MelodiaAudioBusSubsystem.generated.h"

class UMaterialParameterCollection;
class USoundMix;
class USoundClass;

/**
 * The single runtime owner of Melodia's four audio bus gains.
 *
 * This is the "proper audio bus system" the owner asked for: every audible surface in the
 * game routes through one of four SoundClasses (SCL_Ambience / SCL_Music / SCL_SFX /
 * SCL_Voice). This subsystem is the ONLY thing that moves their class-override volumes at
 * runtime. Nothing else writes these four class overrides.
 *
 * Sources (read-only, in priority order):
 *   1. MPC_MelodiaAudioBus lanes (Bus_AmbienceLevel / Bus_MusicLevel / Bus_SFXLevel /
 *      Bus_VoiceLevel), written by the OSC bridge (TD owns the mix) with a C++ neutral 1.0
 *      fallback when no TD input is present.
 *   2. The ambience lane additionally folds in the harmonic tension register so dread pulls
 *      the ambience bed back -- this SUPERSEDES the tension duck MelodiaCore's
 *      UMelodiaRhythmReactivitySubsystem::UpdateTensionAmbienceDuck used to own. That
 *      MelodiaCore path is retired (see its .cpp) so exactly one writer touches SCL_Ambience.
 *
 * No second writer, no second bus, no damage or gameplay authority. Presentation only.
 *
 * Ownership map (canon): one writer per surface.
 *   SCL_Ambience -> THIS subsystem (folds tension)
 *   SCL_Music    -> THIS subsystem
 *   SCL_SFX      -> THIS subsystem
 *   SCL_Voice    -> THIS subsystem
 *   MPC_MelodiaAudioBus lanes -> osc_server.py (TD) / C++ neutral fallback
 *   MPC_Melodia_HarmonicState -> UMelodiaHarmonicStateSubsystem (separate surface, not here)
 */
UCLASS()
class BS_GODFILE_API UMelodiaAudioBusSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** This subsystem is the sole runtime writer of the four bus class overrides. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Audio Bus")
	bool IsSingleWriter() const { return true; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Audio Bus")
	float GetAmbienceLevel() const { return LastAmbienceLevel; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Audio Bus")
	float GetMusicLevel() const { return LastMusicLevel; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Audio Bus")
	float GetSFXLevel() const { return LastSFXLevel; }

	UFUNCTION(BlueprintPure, Category = "Melodia|Audio Bus")
	float GetVoiceLevel() const { return LastVoiceLevel; }

private:
	bool TickBus(float DeltaTime);
	/** Epsilon-gated class override. Only touches the engine when ComputedLevel moved
	 *  >= 0.01 from LastWritten; on pass, LastWritten becomes ComputedLevel (the value
	 *  Get*Level() then reports). */
	void ApplyLane(USoundClass* Class, float ComputedLevel, float& LastWritten);

	UPROPERTY(Transient)
	TObjectPtr<UMaterialParameterCollection> BusCollection; // MPC_MelodiaAudioBus (read)

	UPROPERTY(Transient)
	TObjectPtr<USoundMix> AudioBusMix;                      // SM_MelodiaAudioBus (the mix we drive)

	// The four bus classes (loaded once). Any missing one is a silent no-op for that lane.
	UPROPERTY(Transient)
	TObjectPtr<USoundClass> AmbienceClass;
	UPROPERTY(Transient)
	TObjectPtr<USoundClass> MusicClass;
	UPROPERTY(Transient)
	TObjectPtr<USoundClass> SFXClass;
	UPROPERTY(Transient)
	TObjectPtr<USoundClass> VoiceClass;

	FTSTicker::FDelegateHandle TickerHandle;

	// Last published levels, so the tick skips redundant SetSoundMixClassOverride calls
	// (the engine re-fades on every change; hammering it every frame is the MelodiaCore trap).
	float LastAmbienceLevel = 1.0f;
	float LastMusicLevel = 1.0f;
	float LastSFXLevel = 1.0f;
	float LastVoiceLevel = 1.0f;

	// The tension duck this subsystem now owns (supersedes MelodiaCore's retired path).
	// Full ambience at rest, -6 dB (~0.5x) at max dread, same shape MelodiaCore documented.
	float TensionSustain = 0.0f;
};
