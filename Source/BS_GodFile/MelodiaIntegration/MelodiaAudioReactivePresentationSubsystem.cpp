#include "MelodiaAudioReactivePresentationSubsystem.h"

#include "Kismet/KismetMaterialLibrary.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialParameterCollection.h"
#include "MelodiaBattleSession.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaInputContextSubsystem.h"
#include "Containers/Ticker.h"

namespace
{
	// Grandmaster MPC: the deck melts into MPC_Melodia_Palette live editor agnostic.
	constexpr TCHAR AudioMpcPath[] = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");
}

void UMelodiaAudioReactivePresentationSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	if (UGameInstance* GameInstance = GetGameInstance())
	{
		NarrativeSubsystem = GameInstance->GetSubsystem<UMelodiaNarrativeSubsystem>();
		BattleSession = GameInstance->GetSubsystem<UMelodiaBattleSession>();
		ExternalBridge = GameInstance->GetSubsystem<UMelodiaExternalJRPGBridgeSubsystem>();
		if (NarrativeSubsystem)
		{
			NarrativeSubsystem->OnBattleRequested.AddUniqueDynamic(this, &ThisClass::HandleNarrativeBattleRequested);
			NarrativeSubsystem->OnBattleCompleted.AddUniqueDynamic(this, &ThisClass::HandleNarrativeBattleEnded);
			NarrativeSubsystem->OnBattleAborted.AddUniqueDynamic(this, &ThisClass::HandleNarrativeBattleAborted);
		}
		if (BattleSession)
		{
			BattleSession->OnBattlePhaseChanged.AddUniqueDynamic(this, &ThisClass::HandleMelodiaBattlePhaseChanged);
		}
		if (ExternalBridge)
		{
			ExternalBridge->OnJRPGBattleStarted.AddUniqueDynamic(this, &ThisClass::HandleExternalBattleStarted);
			ExternalBridge->OnJRPGBattleEnded.AddUniqueDynamic(this, &ThisClass::HandleExternalBattleEnded);
		}
	}
	AudioParameterCollection = LoadObject<UMaterialParameterCollection>(nullptr, AudioMpcPath);
	if (!AudioParameterCollection)
	{
		UE_LOG(LogTemp, Warning, TEXT("Melodia audio-reactive presentation disabled: missing %s"), AudioMpcPath);
	}
	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &ThisClass::TickPresentation));
}

void UMelodiaAudioReactivePresentationSubsystem::Deinitialize()
{
	if (NarrativeSubsystem)
	{
		NarrativeSubsystem->OnBattleRequested.RemoveDynamic(this, &ThisClass::HandleNarrativeBattleRequested);
		NarrativeSubsystem->OnBattleCompleted.RemoveDynamic(this, &ThisClass::HandleNarrativeBattleEnded);
		NarrativeSubsystem->OnBattleAborted.RemoveDynamic(this, &ThisClass::HandleNarrativeBattleAborted);
	}
	if (BattleSession)
	{
		BattleSession->OnBattlePhaseChanged.RemoveDynamic(this, &ThisClass::HandleMelodiaBattlePhaseChanged);
	}
	if (ExternalBridge)
	{
		ExternalBridge->OnJRPGBattleStarted.RemoveDynamic(this, &ThisClass::HandleExternalBattleStarted);
		ExternalBridge->OnJRPGBattleEnded.RemoveDynamic(this, &ThisClass::HandleExternalBattleEnded);
	}
	FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
	SetBattleActive(false, 0.0f);
	AudioParameterCollection = nullptr;
	ExternalBridge = nullptr;
	BattleSession = nullptr;
	NarrativeSubsystem = nullptr;
	Super::Deinitialize();
}

void UMelodiaAudioReactivePresentationSubsystem::HandleNarrativeBattleRequested(FName EncounterId) { SetBattleActive(true, 0.45f); PushBattleInputContext(); }
void UMelodiaAudioReactivePresentationSubsystem::HandleNarrativeBattleEnded(FName EncounterId, EMelodiaBattleResult Result) { SetBattleActive(false, 0.0f); PopBattleInputContext(); }
void UMelodiaAudioReactivePresentationSubsystem::HandleNarrativeBattleAborted(FName EncounterId, FString Reason) { SetBattleActive(false, 0.0f); PopBattleInputContext(); }
void UMelodiaAudioReactivePresentationSubsystem::HandleExternalBattleStarted(FName EncounterId) { SetBattleActive(true, 0.55f); PushBattleInputContext(); }
void UMelodiaAudioReactivePresentationSubsystem::HandleExternalBattleEnded(uint8 BattleResult) { SetBattleActive(false, 0.0f); PopBattleInputContext(); }

void UMelodiaAudioReactivePresentationSubsystem::HandleMelodiaBattlePhaseChanged(EMelodiaBattlePhase NewPhase, EMelodiaBattlePhase PreviousPhase)
{
	SetBattleActive(NewPhase != EMelodiaBattlePhase::None, NewPhase == EMelodiaBattlePhase::RhythmExecution ? 1.0f : 0.65f);
}

void UMelodiaAudioReactivePresentationSubsystem::PulseImpact(float Strength)
{
	ImpactPulse = FMath::Max(ImpactPulse, FMath::Clamp(Strength, 0.0f, 1.0f));
}

bool UMelodiaAudioReactivePresentationSubsystem::TickPresentation(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!AudioParameterCollection || !World)
	{
		return true;
	}

	// Musical time comes only from the music-clock authority (Harmonix, else
	// Quartz).  The wall-clock 120 BPM fallback that used to live here was
	// removed: it drifted, and it was hardcoded against 128 BPM source music, so
	// every "beat" it drew was wrong.  With no clock running the beat-driven
	// parameters stay flat rather than pulsing to an invented tempo.
	// Beat is published whenever a clock is running, in battle or not: exploration
	// ambience (lantern flicker, idle sway, petal drift, UI breathing) gets the
	// same musical time for free. Battle intensity stays gated on battle below.
	float BeatPhase = 0.0f;
	bool bHasMusicalTime = false;
	if (const UMelodiaMusicClockSubsystem* MusicClock = World->GetSubsystem<UMelodiaMusicClockSubsystem>())
	{
		bHasMusicalTime = MusicClock->HasMusicalTime();
		BeatPhase = bHasMusicalTime ? MusicClock->GetBeatPhase(UMelodiaMusicClockSubsystem::VisualTimebase) : 0.0f;

		// Forward the clock's real tempo rather than keeping a second hardcoded
		// copy. Two BPM sources that can disagree is exactly how TouchDesigner
		// ends up scoring to a tempo the materials are not pulsing at.
		if (bHasMusicalTime)
		{
			const float ClockBPM = MusicClock->GetTempoBPM();
			if (ClockBPM > 0.0f)
			{
				LastKnownBPM = ClockBPM;
			}
		}
	}
	// Beat edge into the reactivity subsystem (MPC drive + OSC to TouchDesigner on
	// 9000). Driven from here rather than from AMelodiaBattleArena's
	// RhythmExecutionComponent -- that actor is never spawned, which is why TD saw a
	// dead socket. This subsystem already owns musical time every tick, so the beat
	// TD receives is the same one the materials pulse to, by construction.
	//
	// Fires once per beat, on the phase wrap, NOT every frame: NotifyBeat sets
	// BeatPulse to 1.0 and Publish()es immediately, so calling it per-frame would
	// pin the pulse high and flood the socket.
	if (bHasMusicalTime && BeatPhase < LastBeatPhase)
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity =
				World->GetSubsystem<UMelodiaRhythmReactivitySubsystem>())
		{
			Reactivity->NotifyBeat(LastKnownBPM, BeatPhase);
		}
	}
	LastBeatPhase = bHasMusicalTime ? BeatPhase : 0.0f;

	ImpactPulse = FMath::Max(0.0f, ImpactPulse - DeltaTime * 3.5f);
	// cos^2, not sin^2: BeatPhase is 0 ON the beat, so sin^2 peaked at phase 0.5
	// and every MPC consumer pulsed on the off-beat. Same correction as
	// UMelodiaMusicClockSubsystem::GetMusicPulse, which is the canonical copy --
	// if this formula ever needs changing again, change it there and call it.
	float BeatPulseValue = bHasMusicalTime ? FMath::Square(FMath::Cos(BeatPhase * PI)) : 0.0f;
	// Ownership (Phase 0 reconciliation): this subsystem owns the beat namespace
	// on MPC_Melodia_Palette -- it is the only writer of BeatPhase/BeatPulse/
	// BeatIntensity/Treble because it is the one with the music clock and it
	// publishes the continuous cos^2 pulse every frame. UMelodiaRhythmReactivity
	// Subsystem keeps its internal beat values for OSC/reactive materials but no
	// longer writes the MPC beat params. RhythmPulse (CommandEnergy) is owned by
	// that plugin subsystem; this module's impact energy lives on Mid only.
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("GlobalReactivity"), bBattleActive ? BattleIntensity : 0.0f);
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("Bass"), bBattleActive ? BattleIntensity : 0.0f);
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("Mid"), ImpactPulse);
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("Treble"), BeatPulseValue);
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("BeatPhase"), BeatPhase);
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("BeatPulse"), BeatPulseValue);
	UKismetMaterialLibrary::SetScalarParameterValue(World, AudioParameterCollection, TEXT("BeatIntensity"), BeatPulseValue);
	return true;
}

void UMelodiaAudioReactivePresentationSubsystem::PushBattleInputContext()
{
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UMelodiaInputContextSubsystem* InputCtx = GI->GetSubsystem<UMelodiaInputContextSubsystem>())
		{
			BattleContextHandle = InputCtx->PushContext(EMelodiaInputContext::Battle, this);
		}
	}
}

void UMelodiaAudioReactivePresentationSubsystem::PopBattleInputContext()
{
	if (BattleContextHandle.IsValid())
	{
		if (UGameInstance* GI = GetGameInstance())
		{
			if (UMelodiaInputContextSubsystem* InputCtx = GI->GetSubsystem<UMelodiaInputContextSubsystem>())
			{
				InputCtx->PopContext(BattleContextHandle);
				BattleContextHandle = FMelodiaInputContextHandle();
			}
		}
	}
}

void UMelodiaAudioReactivePresentationSubsystem::SetBattleActive(bool bActive, float Intensity)
{
	bBattleActive = bActive;
	BattleIntensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
}
