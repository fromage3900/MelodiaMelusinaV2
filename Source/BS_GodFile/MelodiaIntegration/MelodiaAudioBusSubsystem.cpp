#include "MelodiaAudioBusSubsystem.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Sound/SoundMix.h"
#include "Sound/SoundClass.h"
#include "Kismet/GameplayStatics.h"
#include "Containers/Ticker.h"
#include "Engine/World.h"

void UMelodiaAudioBusSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Read surface + write surface. Missing assets are silent no-ops for their lane
	// (same policy as MelodiaCore's tension duck: SetSoundMixClassOverride on a null
	// class is skipped, not fatal).
	BusCollection = LoadObject<UMaterialParameterCollection>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/MPC_MelodiaAudioBus.MPC_MelodiaAudioBus"));
	AudioBusMix = LoadObject<USoundMix>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/SM_MelodiaAudioBus.SM_MelodiaAudioBus"));
	AmbienceClass = LoadObject<USoundClass>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Ambience.SCL_Ambience"));
	MusicClass = LoadObject<USoundClass>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Music.SCL_Music"));
	SFXClass = LoadObject<USoundClass>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/SoundClasses/SCL_SFX.SCL_SFX"));
	VoiceClass = LoadObject<USoundClass>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/SoundClasses/SCL_Voice.SCL_Voice"));

	if (!BusCollection || !AudioBusMix)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("[AudioBus] MPC_MelodiaAudioBus or SM_MelodiaAudioBus missing -- bus writer idle until assets exist."));
	}

	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMelodiaAudioBusSubsystem::TickBus));
}

void UMelodiaAudioBusSubsystem::Deinitialize()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	Super::Deinitialize();
}

void UMelodiaAudioBusSubsystem::ApplyLane(USoundClass* Class, float ComputedLevel, float& LastWritten)
{
	if (!Class || !AudioBusMix)
	{
		return;
	}
	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	// Only touch the engine when the target actually moved (same epsilon policy as
	// MelodiaCore's UpdateTensionAmbienceDuck: SetSoundMixClassOverride re-fades on
	// every call, so per-frame spam would keep the fade from ever settling).
	if (FMath::IsNearlyEqual(ComputedLevel, LastWritten, 0.01f))
	{
		return;
	}
	// Mirrors MelodiaCore's proven call shape (Decision 033) exactly.
	UGameplayStatics::SetSoundMixClassOverride(World, AudioBusMix, Class, ComputedLevel, 1.0f, 1.5f, true);
	LastWritten = ComputedLevel;
}

bool UMelodiaAudioBusSubsystem::TickBus(float DeltaTime)
{
	if (!BusCollection || !AudioBusMix)
	{
		return true;
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return true;
	}
	UMaterialParameterCollectionInstance* Instance = World->GetParameterCollectionInstance(BusCollection);
	if (!Instance)
	{
		return true;
	}

	// C++ neutral fallback: missing lanes stay at full gain (1.0).
	float AmbienceOsc = 1.0f, MusicOsc = 1.0f, SFXOsc = 1.0f, VoiceOsc = 1.0f;
	Instance->GetScalarParameterValue(FName(TEXT("Bus_AmbienceLevel")), AmbienceOsc);
	Instance->GetScalarParameterValue(FName(TEXT("Bus_MusicLevel")), MusicOsc);
	Instance->GetScalarParameterValue(FName(TEXT("Bus_SFXLevel")), SFXOsc);
	Instance->GetScalarParameterValue(FName(TEXT("Bus_VoiceLevel")), VoiceOsc);

	// Tension duck, now owned here. Eases toward the reactivity sustain register so a
	// lingering dread lingers in the mix, and releases slowly when it drops.
	if (const UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		const float TargetTension = FMath::Clamp(Reactivity->GetSignal().TensionSustain, 0.0f, 1.0f);
		const float Rate = TargetTension > TensionSustain ? 4.0f : 0.35f;
		TensionSustain = FMath::FInterpTo(TensionSustain, TargetTension, DeltaTime, Rate);
	}
	else
	{
		TensionSustain = FMath::FInterpTo(TensionSustain, 0.0f, DeltaTime, 0.35f);
	}

	const float AmbienceDuck = 1.0f - TensionSustain * 0.5f; // -6 dB at max dread
	const float AmbienceLevel = FMath::Clamp(AmbienceOsc * AmbienceDuck, 0.0f, 1.0f);

	ApplyLane(AmbienceClass, AmbienceLevel, LastAmbienceLevel);
	ApplyLane(MusicClass, FMath::Clamp(MusicOsc, 0.0f, 1.0f), LastMusicLevel);
	ApplyLane(SFXClass, FMath::Clamp(SFXOsc, 0.0f, 1.0f), LastSFXLevel);
	ApplyLane(VoiceClass, FMath::Clamp(VoiceOsc, 0.0f, 1.0f), LastVoiceLevel);

	return true;
}
