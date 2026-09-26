#include "MelodiaRhythmHitAudioComponent.h"

#include "Kismet/GameplayStatics.h"

#include "Components/AudioComponent.h"
#include "Engine/World.h"
#include "MelodiaRhythmCombatSubsystem.h"

UMelodiaRhythmHitAudioComponent::UMelodiaRhythmHitAudioComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UMelodiaRhythmHitAudioComponent::BeginPlay()
{
	Super::BeginPlay();

	// The delegate is the ONLY trigger. Binding to OnRhythmComplete instead
	// would give a whole phrase one sound, which is exactly why this component
	// exists rather than a hook on the session result.
	if (UWorld* World = GetWorld())
	{
		if (UMelodiaRhythmCombatSubsystem* Rhythm = World->GetSubsystem<UMelodiaRhythmCombatSubsystem>())
		{
			Rhythm->OnLaneHitJudged.AddUniqueDynamic(this, &UMelodiaRhythmHitAudioComponent::HandleLaneHitJudged);
			RhythmSubsystem = Rhythm;
		}
	}

	bAudioReady = HitMetaSound != nullptr;
}

void UMelodiaRhythmHitAudioComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (RhythmSubsystem)
	{
		RhythmSubsystem->OnLaneHitJudged.RemoveDynamic(this, &UMelodiaRhythmHitAudioComponent::HandleLaneHitJudged);
		RhythmSubsystem = nullptr;
	}

	for (const TWeakObjectPtr<UAudioComponent>& WeakAudio : ActiveVoices)
	{
		if (UAudioComponent* Audio = WeakAudio.Get())
		{
			Audio->Stop();
			Audio->DestroyComponent();
		}
	}
	ActiveVoices.Empty();

	Super::EndPlay(EndPlayReason);
}

void UMelodiaRhythmHitAudioComponent::HandleLaneHitJudged(int32 LaneIndex, EMelodiaSkillGrade Grade, float TimingErrorMs)
{
	PlayHit(LaneIndex, Grade, TimingErrorMs);
}

void UMelodiaRhythmHitAudioComponent::PlayHit(int32 LaneIndex, EMelodiaSkillGrade Grade, float TimingErrorMs)
{
	// CreateSound2D builds the component without starting it, so the grade
	// parameters below still land before Play.
	UAudioComponent* Audio = HitMetaSound
		? UGameplayStatics::CreateSound2D(this, HitMetaSound, 1.0f, 1.0f, 0.0f, HitConcurrency, false, false)
		: nullptr;
	if (!Audio)
	{
		return;
	}

	// Voice budget, on the same idiom as UMelodiaWaterAudioBridgeComponent: a
	// dense phrase can outrun the mixer, and dropped voices read as a glitch
	// rather than as a limit.
	ActiveVoices.RemoveAll([](const TWeakObjectPtr<UAudioComponent>& WeakAudio)
	{
		return !WeakAudio.IsValid() || !WeakAudio->IsPlaying();
	});
	if (ActiveVoices.Num() >= MaxConcurrentVoices)
	{
		Audio->DestroyComponent();
		++DroppedHitCount;
		return;
	}

	// TIMBRE is humanised; TIMING is not. See the header comment.
	const float LaneSemitones = static_cast<float>(FMath::Max(0, LaneIndex)) * LanePitchSpreadSemitones;
	const float Jitter = FMath::FRandRange(-PitchJitterCents, PitchJitterCents);
	const float Pitch = FMath::Pow(2.0f, (LaneSemitones + Jitter / 100.0f) / 12.0f);
	const float Volume = FMath::Clamp(FMath::FRandRange(1.0f - VolumeJitter, 1.0f + VolumeJitter), 0.0f, 2.0f);

	Audio->SetVolumeMultiplier(Volume);
	Audio->SetPitchMultiplier(Pitch);

	// PARAMETERS BEFORE PLAY. This is the whole reason the component builds the
	// audio component by hand instead of using SpawnSoundAtLocation: that
	// helper starts playback inside the call, so a SetFloatParameter afterwards
	// can land AFTER the graph's On Play block has already read HitGrade -- and
	// every grade would sound identical, which is the single failure mode that
	// would make this whole lane pointless.
	Audio->SetFloatParameter(GradeParameter, static_cast<float>(static_cast<uint8>(Grade)));
	Audio->SetFloatParameter(LaneParameter, static_cast<float>(LaneIndex));
	// Clamp so an absurd timing error cannot drive a filter into a silent or
	// screaming state; the graph reads a bounded 0..1.
	Audio->SetFloatParameter(TimingParameter, FMath::Clamp(FMath::Abs(TimingErrorMs) / 200.0f, 0.0f, 1.0f));

	Audio->OnAudioFinishedNative.AddUObject(this, &UMelodiaRhythmHitAudioComponent::HandleVoiceFinished);
	Audio->Play();
	ActiveVoices.Add(Audio);
	++PlayedHitCount;
}

void UMelodiaRhythmHitAudioComponent::HandleVoiceFinished(UAudioComponent* Finished)
{
	if (!Finished)
	{
		return;
	}
	ActiveVoices.Remove(Finished);
	Finished->DestroyComponent();
}
