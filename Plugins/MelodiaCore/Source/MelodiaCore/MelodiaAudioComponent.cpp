#include "MelodiaAudioComponent.h"

#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundWaveProcedural.h"
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

	PerfectTone = CreateTone(880.0f, 0.12f);
	GreatTone = CreateTone(660.0f, 0.12f);
	GoodTone = CreateTone(440.0f, 0.10f);
	MissTone = CreateTone(220.0f, 0.20f);
	ClickTone = CreateTone(1000.0f, 0.04f);
}

USoundWave* UMelodiaAudioComponent::CreateTone(float FrequencyHz, float DurationSec, float Volume)
{
	constexpr int32 SampleRate = 44100;
	const int32 NumSamples = FMath::Max(32, FMath::CeilToInt(SampleRate * DurationSec));

	TArray<uint8> RawData;
	RawData.SetNumUninitialized(NumSamples * sizeof(int16));
	int16* SampleData = reinterpret_cast<int16*>(RawData.GetData());

	const float EnvDuration = FMath::Min(0.008f, DurationSec * 0.15f);

	for (int32 i = 0; i < NumSamples; ++i)
	{
		const float t = static_cast<float>(i) / SampleRate;
		float Envelope = 1.0f;
		if (t < EnvDuration)
		{
			Envelope = t / EnvDuration;
		}
		else if (t > DurationSec - EnvDuration)
		{
			Envelope = (DurationSec - t) / EnvDuration;
		}
		const float Sample = FMath::Sin(2.0f * PI * FrequencyHz * t) * Envelope * FMath::Clamp(Volume, 0.0f, 1.0f);
		SampleData[i] = static_cast<int16>(FMath::Clamp(Sample * 32767.0f, -32767.0f, 32767.0f));
	}

	USoundWaveProcedural* Sound = NewObject<USoundWaveProcedural>(GetTransientPackage());
	Sound->Duration = DurationSec;
	Sound->SetSampleRate(SampleRate);
	Sound->NumChannels = 1;
	Sound->SoundGroup = SOUNDGROUP_UI;
	Sound->QueueAudio(RawData.GetData(), RawData.Num());

	return Sound;
}

void UMelodiaAudioComponent::PlaySound(USoundWave* Sound, float VolumeMultiplier)
{
	if (!Sound || SFXVolume <= 0.0f)
	{
		return;
	}

	UAudioComponent* AC = UGameplayStatics::SpawnSound2D(this, Sound, SFXVolume * VolumeMultiplier, 1.0f, 0.0f, nullptr, false, false);
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
		PlaySound(PerfectTone, 1.0f);
		break;
	case EMelodiaRhythmGrade::Great:
		PlaySound(GreatTone, 0.8f);
		break;
	case EMelodiaRhythmGrade::Good:
		PlaySound(GoodTone, 0.6f);
		break;
	default:
		PlayMissSFX();
		break;
	}
}

void UMelodiaAudioComponent::PlayMissSFX()
{
	PlaySound(MissTone, 1.0f);
}

void UMelodiaAudioComponent::PlayMetronomeClick()
{
	PlaySound(ClickTone, 0.3f);
}

void UMelodiaAudioComponent::PlayMusicalNote(const int32 MidiNote, const float DurationSeconds, const float Velocity)
{
	const int32 ClampedMidi = FMath::Clamp(MidiNote, 0, 127);
	const float FrequencyHz = 440.0f * FMath::Pow(2.0f, (static_cast<float>(ClampedMidi) - 69.0f) / 12.0f);
	const float ClampedDuration = FMath::Clamp(DurationSeconds, 0.03f, 2.0f);
	const float ClampedVelocity = FMath::Clamp(Velocity, 0.0f, 1.0f);
	USoundWave* Tone = CreateTone(FrequencyHz, ClampedDuration, ClampedVelocity);
	if (!Tone)
	{
		return;
	}
	ActiveMusicalTones.Add(Tone);
	while (ActiveMusicalTones.Num() > 64)
	{
		ActiveMusicalTones.RemoveAt(0);
	}
	PlaySound(Tone);
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
