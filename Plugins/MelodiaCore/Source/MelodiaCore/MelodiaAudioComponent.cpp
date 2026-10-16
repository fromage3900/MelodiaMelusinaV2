#include "MelodiaAudioComponent.h"

#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "Sound/QuartzQuantizationUtilities.h"
#include "Quartz/QuartzSubsystem.h"
#include "Quartz/AudioMixerClockHandle.h"

const FName UMelodiaAudioComponent::BattleClockName(TEXT("MelodiaBattleClock"));

UMelodiaAudioComponent::UMelodiaAudioComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaAudioComponent::BeginPlay()
{
	Super::BeginPlay();
}

void UMelodiaAudioComponent::PlayTone(const float FrequencyHz, const float VolumeMultiplier)
{
	// One authored sample, pitched per call. Runtime USoundWaveProcedural tones were
	// cached and replayed; a procedural wave's queue is spent on its first play, so a
	// replay starved the mixer and crashed it on a null read.
	USoundBase* Sample = NoteSample.LoadSynchronous();
	if (!Sample || SFXVolume <= 0.0f)
	{
		return;
	}
	constexpr float C4Hz = 261.6256f;
	UAudioComponent* AC = UGameplayStatics::SpawnSound2D(this, Sample, SFXVolume * VolumeMultiplier,
		FMath::Clamp(FrequencyHz / C4Hz, 0.125f, 8.0f));
	if (AC)
	{
		AC->bIsUISound = true;
	}
}

void UMelodiaAudioComponent::PlayHitSFX(EMelodiaRhythmGrade Grade)
{
	switch (Grade)
	{
	case EMelodiaRhythmGrade::Perfect:
		PlayTone(880.0f, 1.0f);
		break;
	case EMelodiaRhythmGrade::Great:
		PlayTone(660.0f, 0.8f);
		break;
	case EMelodiaRhythmGrade::Good:
		PlayTone(440.0f, 0.6f);
		break;
	default:
		PlayMissSFX();
		break;
	}
}

void UMelodiaAudioComponent::PlayMissSFX()
{
	PlayTone(220.0f, 1.0f);
}

void UMelodiaAudioComponent::PlayMetronomeClick()
{
	PlayTone(1000.0f, 0.3f);
}

void UMelodiaAudioComponent::PlayMusicalNote(const int32 MidiNote, const float DurationSeconds, const float Velocity)
{
	const int32 ClampedMidi = FMath::Clamp(MidiNote, 0, 127);
	const float FrequencyHz = 440.0f * FMath::Pow(2.0f, (static_cast<float>(ClampedMidi) - 69.0f) / 12.0f);
	PlayTone(FrequencyHz, FMath::Clamp(Velocity, 0.0f, 1.0f));
}

void UMelodiaAudioComponent::PlayBGM(FName SkillId)
{
	StopBGM();

	USoundWave* BGM_Sound = LoadObject<USoundWave>(nullptr,
		*FString::Printf(TEXT("/Game/Audio/BGM/BGM_%s.BGM_%s"), *SkillId.ToString(), *SkillId.ToString()));
	if (!BGM_Sound)
	{
		// Sourced track: Zundamon "Sewaa" (131 BPM, 2:35) for faster skills.
		if (SkillId == TEXT("tempo_shift") || SkillId == TEXT("crescendo_wave"))
		{
			BGM_Sound = LoadObject<USoundWave>(nullptr,
				TEXT("/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Full.SW_BGM_Zundamon_Sewaa_Full"));
		}
	}
	if (!BGM_Sound)
	{
		// Sourced cover: Melusina "Duvet" cover (93 BPM, ~3:31), looped in-editor.
		BGM_Sound = LoadObject<USoundWave>(nullptr,
			TEXT("/Game/Melodia/Audio/BGM/SW_BGM_Battle_Duvet_Cover.SW_BGM_Battle_Duvet_Cover"));
	}
	if (!BGM_Sound)
	{
		// Slice stopgap: fall back to the placeholder 128-BPM battle loop
		// (exactly 30.0s / 64 beats). NOTE: set the wave's Looping flag in-editor.
		BGM_Sound = LoadObject<USoundWave>(nullptr,
			TEXT("/Game/Melodia/Audio/BGM/SW_BGM_Battle_Placeholder_128.SW_BGM_Battle_Placeholder_128"));
	}
	if (!BGM_Sound)
	{
		UE_LOG(LogTemp, Verbose, TEXT("MelodiaAudio: BGM asset not found for %s"), *SkillId.ToString());
		return;
	}

	BGMComponent = UGameplayStatics::SpawnSound2D(this, BGM_Sound, BGMVolume, 1.0f, 0.0f, nullptr, true, false);
	if (BGMComponent)
	{
		BGMComponent->bIsUISound = false;
	}
}

void UMelodiaAudioComponent::StopBGM()
{
	if (BGMComponent)
	{
		BGMComponent->Stop();
		BGMComponent = nullptr;
	}
}

void UMelodiaAudioComponent::StartBattleClock(float InBPM)
{
	UWorld* World = GetWorld();
	UQuartzSubsystem* QuartzSubsystem = World ? UQuartzSubsystem::Get(World) : nullptr;
	if (!QuartzSubsystem)
	{
		return;
	}

	FQuartzClockSettings ClockSettings;
	BattleClockHandle = QuartzSubsystem->CreateNewClock(this, BattleClockName, ClockSettings, /*bOverrideSettingsIfClockExists=*/true);
	if (!BattleClockHandle)
	{
		return;
	}

	// Quartz's ref-out ClockHandle params require a raw-pointer lvalue; TObjectPtr can't bind directly.
	UQuartzClockHandle* RawClockHandle = BattleClockHandle;
	RawClockHandle->StartClock(this, RawClockHandle);

	const FQuartzQuantizationBoundary ImmediateBoundary(EQuartzCommandQuantization::None);
	const FOnQuartzCommandEventBP EmptyDelegate;
	const float ClampedBPM = FMath::Max(1.0f, InBPM);
	RawClockHandle->SetBeatsPerMinute(this, ImmediateBoundary, EmptyDelegate, RawClockHandle, ClampedBPM);
	BattleClockHandle = RawClockHandle;
	BattleClockBPM = ClampedBPM;
}

void UMelodiaAudioComponent::PlayBGMQuantized()
{
	StopBGM();

	// Mirror PlayBGM's sourcing chain: Sewaa (131 BPM) for fast skills, Duvet
	// cover (93 BPM) otherwise, placeholder 128-BPM loop as the stopgap.
	USoundWave* BGM_Sound = nullptr;
	if (CurrentSkillId == TEXT("tempo_shift") || CurrentSkillId == TEXT("crescendo_wave"))
	{
		BGM_Sound = LoadObject<USoundWave>(nullptr,
			TEXT("/Game/Melodia/Audio/BGM/SW_BGM_Zundamon_Sewaa_Full.SW_BGM_Zundamon_Sewaa_Full"));
	}
	if (!BGM_Sound)
	{
		BGM_Sound = LoadObject<USoundWave>(nullptr,
			TEXT("/Game/Melodia/Audio/BGM/SW_BGM_Battle_Duvet_Cover.SW_BGM_Battle_Duvet_Cover"));
	}
	if (!BGM_Sound)
	{
		BGM_Sound = LoadObject<USoundWave>(nullptr,
			TEXT("/Game/Melodia/Audio/BGM/SW_BGM_Battle_Placeholder_128.SW_BGM_Battle_Placeholder_128"));
	}
	if (!BGM_Sound)
	{
		UE_LOG(LogTemp, Verbose, TEXT("MelodiaAudio: Quartz placeholder BGM asset not found"));
		return;
	}

	if (!BattleClockHandle)
	{
		StartBattleClock(128.0f);
	}

	if (!BattleClockHandle)
	{
		// Quartz unavailable ΓÇö fall back to immediate (unquantized) playback so BGM still plays.
		BGMComponent = UGameplayStatics::SpawnSound2D(this, BGM_Sound, BGMVolume, 1.0f, 0.0f, nullptr, true, false);
		if (BGMComponent)
		{
			BGMComponent->bIsUISound = false;
		}
		return;
	}

	BGMComponent = UGameplayStatics::CreateSound2D(this, BGM_Sound, BGMVolume, 1.0f, 0.0f, nullptr, true, false);
	if (!BGMComponent)
	{
		return;
	}
	BGMComponent->bIsUISound = false;

	FQuartzQuantizationBoundary BarBoundary(EQuartzCommandQuantization::Bar);
	const FOnQuartzCommandEventBP EmptyDelegate;
	UQuartzClockHandle* RawClockHandle = BattleClockHandle;
	BGMComponent->PlayQuantized(this, RawClockHandle, BarBoundary, EmptyDelegate);
	BattleClockHandle = RawClockHandle;
}

float UMelodiaAudioComponent::GetSongBeatPosition() const
{
	UWorld* World = GetWorld();
	UQuartzSubsystem* QuartzSubsystem = World ? UQuartzSubsystem::Get(World) : nullptr;
	if (!BattleClockHandle || !QuartzSubsystem || !QuartzSubsystem->DoesClockExist(this, BattleClockName))
	{
		return 0.0f;
	}

	const FQuartzTransportTimeStamp Timestamp = QuartzSubsystem->GetCurrentClockTimestamp(this, BattleClockName);
	// Quartz reports 1-based Bar/Beat; report a zero-based running beat count within the current bar.
	return static_cast<float>(FMath::Max(0, Timestamp.Beat - 1)) + Timestamp.BeatFraction;
}

bool UMelodiaAudioComponent::IsBattleClockRunning() const
{
	UWorld* World = GetWorld();
	UQuartzSubsystem* QuartzSubsystem = World ? UQuartzSubsystem::Get(World) : nullptr;
	return BattleClockHandle && QuartzSubsystem && QuartzSubsystem->IsClockRunning(this, BattleClockName);
}
