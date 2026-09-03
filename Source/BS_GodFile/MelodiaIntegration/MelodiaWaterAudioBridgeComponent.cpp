#include "MelodiaWaterAudioBridgeComponent.h"

#include "Components/AudioComponent.h"
#include "Kismet/GameplayStatics.h"
#include "MetasoundSource.h"
#include "Sound/SoundAttenuation.h"
#include "Sound/SoundConcurrency.h"
#include "MelodiaWaterInteractionSubsystem.h"
#include "MelodiaWaterProfile.h"
#include "UObject/ConstructorHelpers.h"

UMelodiaWaterAudioBridgeComponent::UMelodiaWaterAudioBridgeComponent()
{
	PrimaryComponentTick.bCanEverTick = false;

	static ConstructorHelpers::FObjectFinder<UMelodiaWaterProfile> ProfileFinder(
		TEXT("/Game/MelodiaIntegration/Water/Profiles/DA_WaterV10_Default.DA_WaterV10_Default"));
	if (ProfileFinder.Succeeded())
	{
		Profile = ProfileFinder.Object;
	}

	static ConstructorHelpers::FObjectFinder<UMetaSoundSource> SurfaceMovementFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/MS_Water_SurfaceMovement.MS_Water_SurfaceMovement"));
	DefaultSurfaceMovementMetaSound = SurfaceMovementFinder.Succeeded() ? SurfaceMovementFinder.Object : nullptr;
	static ConstructorHelpers::FObjectFinder<UMetaSoundSource> SurfaceEntryFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/MS_Water_SurfaceEntry.MS_Water_SurfaceEntry"));
	DefaultSurfaceEntryMetaSound = SurfaceEntryFinder.Succeeded() ? SurfaceEntryFinder.Object : nullptr;
	static ConstructorHelpers::FObjectFinder<UMetaSoundSource> UnderwaterBubbleFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/MS_Water_UnderwaterBubble.MS_Water_UnderwaterBubble"));
	DefaultUnderwaterBubbleMetaSound = UnderwaterBubbleFinder.Succeeded() ? UnderwaterBubbleFinder.Object : nullptr;
	static ConstructorHelpers::FObjectFinder<UMetaSoundSource> WaterImpactFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/MS_Water_Impact.MS_Water_Impact"));
	DefaultWaterImpactMetaSound = WaterImpactFinder.Succeeded() ? WaterImpactFinder.Object : nullptr;
	static ConstructorHelpers::FObjectFinder<UMetaSoundSource> ReemergenceFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/MS_Water_Reemergence.MS_Water_Reemergence"));
	DefaultReemergenceMetaSound = ReemergenceFinder.Succeeded() ? ReemergenceFinder.Object : nullptr;
	static ConstructorHelpers::FObjectFinder<USoundConcurrency> ConcurrencyFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/SC_WaterV10_AudioConcurrency.SC_WaterV10_AudioConcurrency"));
	DefaultAudioConcurrency = ConcurrencyFinder.Succeeded() ? ConcurrencyFinder.Object : nullptr;
	static ConstructorHelpers::FObjectFinder<USoundAttenuation> AttenuationFinder(
		TEXT("/Game/EnvSandbox/Water/v10/Audio/SA_WaterV10_3D_Attenuation.SA_WaterV10_3D_Attenuation"));
	DefaultAudioAttenuation = AttenuationFinder.Succeeded() ? AttenuationFinder.Object : nullptr;
}

void UMelodiaWaterAudioBridgeComponent::BeginPlay()
{
	Super::BeginPlay();

	if (UWorld* World = GetWorld())
	{
		WaterSubsystem = World->GetSubsystem<UMelodiaWaterInteractionSubsystem>();
		if (WaterSubsystem)
		{
			WaterSubsystem->OnContactEvent.AddUniqueDynamic(this, &ThisClass::HandleWaterContact);
		}
	}

	if (Profile)
	{
		MaxAudioEventsPerSecond = FMath::Min(MaxAudioEventsPerSecond, FMath::Max(1, Profile->MaxAudioEventsPerSecond));
		MaxConcurrentVoices = FMath::Min(MaxConcurrentVoices, FMath::Max(1, Profile->MaxAudioVoices));
		bAudioReady = (!Profile->SurfaceMovementMetaSound.IsNull() || IsValid(DefaultSurfaceMovementMetaSound))
			&& (!Profile->SurfaceEntryMetaSound.IsNull() || IsValid(DefaultSurfaceEntryMetaSound))
			&& (!Profile->UnderwaterBubbleMetaSound.IsNull() || IsValid(DefaultUnderwaterBubbleMetaSound))
			&& (!Profile->WaterImpactMetaSound.IsNull() || IsValid(DefaultWaterImpactMetaSound))
			&& (!Profile->ReemergenceMetaSound.IsNull() || IsValid(DefaultReemergenceMetaSound))
			&& (!Profile->AudioConcurrency.IsNull() || IsValid(DefaultAudioConcurrency))
			&& (!Profile->AudioAttenuation.IsNull() || IsValid(DefaultAudioAttenuation));
	}

	if (!bAudioReady)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia water audio bridge has no MetaSound profile assignments on %s"), *GetNameSafe(GetOwner()));
	}
}

void UMelodiaWaterAudioBridgeComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (WaterSubsystem)
	{
		WaterSubsystem->OnContactEvent.RemoveDynamic(this, &ThisClass::HandleWaterContact);
		WaterSubsystem = nullptr;
	}

	for (const TWeakObjectPtr<UAudioComponent>& WeakAudio : ActiveAudioComponents)
	{
		if (UAudioComponent* Audio = WeakAudio.Get())
		{
			Audio->Stop();
			Audio->DestroyComponent();
		}
	}
	ActiveAudioComponents.Reset();
	ActiveAudioVoices = 0;
	Super::EndPlay(EndPlayReason);
}

void UMelodiaWaterAudioBridgeComponent::HandleWaterContact(FMelodiaWaterContactEvent Event)
{
	if (!bEnabled || (bOnlySpawnForOwner && Event.SourceActor != GetOwner()) || Event.Intensity < MinimumIntensity)
	{
		return;
	}
	if (Event.EventType == EMelodiaWaterContactType::ProximityEntered
		|| Event.EventType == EMelodiaWaterContactType::ProximityExited
		|| Event.EventType == EMelodiaWaterContactType::SwimStarted
		|| Event.EventType == EMelodiaWaterContactType::SwimStopped)
	{
		return;
	}

	UMetaSoundSource* Sound = ResolveSound(Event);
	if (!Sound || !CanPlayEvent(Event))
	{
		++RejectedAudioEvents;
		return;
	}

	if (PlayWaterMetaSound(Event, Sound))
	{
		++AudioEventsThisWindow;
	}
	else
	{
		++RejectedAudioEvents;
	}
}

UMetaSoundSource* UMelodiaWaterAudioBridgeComponent::ResolveSound(const FMelodiaWaterContactEvent& Event) const
{
	if (!Profile)
	{
		return nullptr;
	}

	const TSoftObjectPtr<UMetaSoundSource>* SoundRef = nullptr;
	switch (Event.EventType)
	{
	case EMelodiaWaterContactType::DiveStarted:
		SoundRef = &Profile->UnderwaterBubbleMetaSound;
		break;
	case EMelodiaWaterContactType::SurfaceEntry:
		SoundRef = &Profile->SurfaceEntryMetaSound;
		break;
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::WaterImpact:
		SoundRef = &Profile->WaterImpactMetaSound;
		break;
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::DiveStopped:
	case EMelodiaWaterContactType::SwimStopped:
		SoundRef = &Profile->ReemergenceMetaSound;
		break;
	case EMelodiaWaterContactType::Ripple:
		SoundRef = Event.Sample.bUnderwater || Event.Sample.Immersion >= 0.8f
			? &Profile->UnderwaterBubbleMetaSound
			: &Profile->SurfaceMovementMetaSound;
		break;
	case EMelodiaWaterContactType::Footstep:
	case EMelodiaWaterContactType::SwimStarted:
	default:
		SoundRef = &Profile->SurfaceMovementMetaSound;
		break;
	}

	if (SoundRef && !SoundRef->IsNull())
	{
		if (UMetaSoundSource* ProfileSound = SoundRef->LoadSynchronous())
		{
			return ProfileSound;
		}
	}

	switch (Event.EventType)
	{
	case EMelodiaWaterContactType::DiveStarted:
	case EMelodiaWaterContactType::Ripple:
		return Event.Sample.bUnderwater || Event.Sample.Immersion >= 0.8f
			? DefaultUnderwaterBubbleMetaSound.Get()
			: DefaultSurfaceMovementMetaSound.Get();
	case EMelodiaWaterContactType::SurfaceEntry:
		return DefaultSurfaceEntryMetaSound;
	case EMelodiaWaterContactType::Splash:
	case EMelodiaWaterContactType::WaterImpact:
		return DefaultWaterImpactMetaSound;
	case EMelodiaWaterContactType::SurfaceExit:
	case EMelodiaWaterContactType::DiveStopped:
		return DefaultReemergenceMetaSound;
	default:
		return DefaultSurfaceMovementMetaSound;
	}
}

bool UMelodiaWaterAudioBridgeComponent::CanPlayEvent(const FMelodiaWaterContactEvent& Event)
{
	if (!bAudioReady || !Profile)
	{
		return false;
	}

	const float Now = GetWorld() ? GetWorld()->GetTimeSeconds() : Event.Duration;
	const bool bReemergenceEvent = Event.EventType == EMelodiaWaterContactType::SurfaceExit
		|| Event.EventType == EMelodiaWaterContactType::DiveStopped;
	if (bReemergenceEvent && Now - LastReemergenceTime < 0.35f)
	{
		return false;
	}
	if (AudioWindowStart <= 0.0f || Now - AudioWindowStart >= 1.0f)
	{
		AudioWindowStart = Now;
		AudioEventsThisWindow = 0;
		RejectedAudioEvents = 0;
	}

	CleanupActiveVoices();
	return AudioEventsThisWindow < MaxAudioEventsPerSecond && ActiveAudioVoices < MaxConcurrentVoices;
}

void UMelodiaWaterAudioBridgeComponent::CleanupActiveVoices()
{
	ActiveAudioComponents.RemoveAll([](const TWeakObjectPtr<UAudioComponent>& WeakAudio)
	{
		return !WeakAudio.IsValid() || !WeakAudio->IsPlaying();
	});
	ActiveAudioVoices = ActiveAudioComponents.Num();
}

UAudioComponent* UMelodiaWaterAudioBridgeComponent::PlayWaterMetaSound(const FMelodiaWaterContactEvent& Event, UMetaSoundSource* Sound)
{
	if (!Sound || !GetWorld())
	{
		return nullptr;
	}

	// .Get() on the TObjectPtr side: LoadSynchronous() returns a raw pointer, so
	// without it the conditional has two convertible-but-distinct types and MSVC
	// rejects it (C2445).
	USoundConcurrency* Concurrency = Profile && !Profile->AudioConcurrency.IsNull()
		? Profile->AudioConcurrency.LoadSynchronous()
		: DefaultAudioConcurrency.Get();
	USoundAttenuation* Attenuation = Profile && !Profile->AudioAttenuation.IsNull()
		? Profile->AudioAttenuation.LoadSynchronous()
		: DefaultAudioAttenuation.Get();
	const float Speed = Event.ImpactVelocity.Size();
	const float Volume = FMath::Lerp(0.2f, 1.0f, FMath::Clamp(Event.Intensity, 0.0f, 1.0f));
	const float Pitch = FMath::Clamp(0.92f + Speed / 5000.0f, 0.85f, 1.18f);

	UAudioComponent* Audio = UGameplayStatics::SpawnSoundAtLocation(
		this,
		Sound,
		Event.ContactLocation,
		FRotator::ZeroRotator,
		Volume,
		Pitch,
		0.0f,
		Attenuation,
		Concurrency,
		true);
	if (!Audio)
	{
		return nullptr;
	}

	Audio->SetFloatParameter(IntensityParameter, Event.Intensity);
	Audio->SetFloatParameter(ImmersionParameter, Event.Sample.Immersion);
	Audio->SetFloatParameter(VelocityParameter, Speed);
	Audio->SetFloatParameter(DepthParameter, Event.Sample.ImmersionDepth);
	ActiveAudioComponents.Add(Audio);
	ActiveAudioVoices = ActiveAudioComponents.Num();
	if (Event.EventType == EMelodiaWaterContactType::SurfaceExit
		|| Event.EventType == EMelodiaWaterContactType::DiveStopped)
	{
		LastReemergenceTime = GetWorld() ? GetWorld()->GetTimeSeconds() : Event.Duration;
	}
	return Audio;
}
