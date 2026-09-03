#include "MelodiaGameUserSettings.h"

#include "Kismet/GameplayStatics.h"
#include "Sound/SoundClass.h"
#include "Sound/SoundMix.h"

namespace
{
	constexpr TCHAR UserPreferencesMixPath[] = TEXT("/Game/Melodia/Audio/SM_MelodiaUserPreferences.SM_MelodiaUserPreferences");
	constexpr TCHAR MasterClassPath[] = TEXT("/Engine/EngineSounds/Master.Master");
	constexpr TCHAR MusicClassPath[] = TEXT("/Engine/EngineSounds/Music.Music");
	constexpr TCHAR SfxClassPath[] = TEXT("/Engine/EngineSounds/SFX.SFX");
}

UMelodiaGameUserSettings* UMelodiaGameUserSettings::Get()
{
	return Cast<UMelodiaGameUserSettings>(UGameUserSettings::GetGameUserSettings());
}

void UMelodiaGameUserSettings::ApplyMelodiaPreferences(const UObject* WorldContextObject)
{
	MasterVolume = FMath::Clamp(MasterVolume, 0.0f, 1.0f);
	MusicVolume = FMath::Clamp(MusicVolume, 0.0f, 1.0f);
	SFXVolume = FMath::Clamp(SFXVolume, 0.0f, 1.0f);
	UIScale = FMath::Clamp(UIScale, 0.8f, 1.3f);

	if (WorldContextObject)
	{
		USoundMix* Mix = LoadObject<USoundMix>(nullptr, UserPreferencesMixPath);
		USoundClass* Master = LoadObject<USoundClass>(nullptr, MasterClassPath);
		USoundClass* Music = LoadObject<USoundClass>(nullptr, MusicClassPath);
		USoundClass* SFX = LoadObject<USoundClass>(nullptr, SfxClassPath);
		if (Mix)
		{
			UGameplayStatics::PushSoundMixModifier(WorldContextObject, Mix);
			if (Master) UGameplayStatics::SetSoundMixClassOverride(WorldContextObject, Mix, Master, MasterVolume, 1.0f, 0.05f);
			if (Music) UGameplayStatics::SetSoundMixClassOverride(WorldContextObject, Mix, Music, MusicVolume, 1.0f, 0.05f);
			if (SFX) UGameplayStatics::SetSoundMixClassOverride(WorldContextObject, Mix, SFX, SFXVolume, 1.0f, 0.05f);
		}
	}

	ApplySettings(false);
	SaveSettings();
}
