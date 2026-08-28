#include "MelodiaAudioReactivePresentationSubsystem.h"

#include "Kismet/KismetMaterialLibrary.h"
#include "Engine/GameInstance.h"
#include "GameFramework/Actor.h"
#include "Materials/MaterialParameterCollection.h"
#include "NiagaraParameterCollection.h"
#include "NiagaraFunctionLibrary.h"
#include "MelodiaBattleSession.h"
#include "MelodiaExternalJRPGBridgeSubsystem.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "MelodiaNarrativeSubsystem.h"
#include "MelodiaInputContextSubsystem.h"
#include "Containers/Ticker.h"
#include "Components/MeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "EngineUtils.h"
#include "ProfilingDebugging/CpuProfilerTrace.h"
#include "Stats/Stats.h"

namespace
{
	// Grandmaster MPC: the deck melts into MPC_Melodia_Palette live editor agnostic.
	constexpr TCHAR AudioMpcPath[] = TEXT("/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette.MPC_Melodia_Palette");
	// Niagara cannot sample an MPC. NPC_Melodia_Palette is the Niagara-side twin and is
	// already read by six+ NS_ systems; nothing wrote it before this subsystem did.
	constexpr TCHAR AudioNpcPath[] = TEXT("/Game/EnvSandbox/VFX/MPC/NPC_Melodia_Palette.NPC_Melodia_Palette");

	// --- Oceanology presentation drive ----------------------------------------
	// Oceanology's water surface cannot sample MPC_Melodia_Palette: its master
	// (M_Oceanology) is plugin-owned and must never be edited, and material
	// instances cannot add collection samples. So the beat reaches the ocean the
	// sanctioned way instead: this subsystem (already the single MPC beat writer)
	// creates one dynamic material instance per ocean surface component and writes
	// the verified parameter surface (106 params captured 2026-08-27 via material
	// reflection on M_Oceanology_Inst) by name:
	//   BeatPulse  -> PhaseGLow / HighlightBoost
	//   Bass/Combat-> ScatterBoost
	//   ImpactPulse-> DeepScatteringColor shift
	// No Oceanology headers are included; the actor class is matched by name so
	// this file stays buildable with the plugin disabled. Game-worlds only --
	// the editor viewport must never be mutated by runtime presentation.
	struct FOceanBeatDriveEntry
	{
		TWeakObjectPtr<UMeshComponent> Component;
		TWeakObjectPtr<UMaterialInstanceDynamic> Mid;
	};
	// Keyed by world so PIE and any secondary world never share MIDs.
	static TMap<const UWorld*, TArray<FOceanBeatDriveEntry>> GOceanBeatDrives;
	static double GOceanRescanTime = 0.0;
	constexpr float OceanDriveRescanInterval = 2.0f;
	constexpr TCHAR OceanActorClassNameToken[] = TEXT("Oceanology");

	void DriveOceanBeatValues(UWorld* World, float BeatPulse, float CombatEnergy, float ImpactPulse)
	{
		TRACE_CPUPROFILER_EVENT_SCOPE(Melodia_DriveOceanBeatValues);
		const double Now = FPlatformTime::Seconds();
		TArray<FOceanBeatDriveEntry>& Entries = GOceanBeatDrives.FindOrAdd(World);
		bool bRescan = (Now - GOceanRescanTime) > OceanDriveRescanInterval;
		if (bRescan)
		{
			GOceanRescanTime = Now;
			Entries.RemoveAll([](const FOceanBeatDriveEntry& Entry)
			{
				return !Entry.Component.IsValid() || !Entry.Mid.IsValid();
			});
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				AActor* Actor = *It;
				if (!Actor || !Actor->GetClass()->GetName().Contains(OceanActorClassNameToken))
				{
					continue;
				}
				// One drive per mesh component; skip components already driven.
				bool bDriven = false;
				for (const FOceanBeatDriveEntry& Entry : Entries)
				{
					if (Entry.Component.Get() == Actor->FindComponentByClass<UMeshComponent>() ||
					    (Entry.Component.IsValid() && Entry.Component->GetOwner() == Actor))
					{
						bDriven = true;
						break;
					}
				}
				if (bDriven)
				{
					continue;
				}
				if (UMeshComponent* Mesh = Actor->FindComponentByClass<UMeshComponent>())
				{
					if (UMaterialInterface* BaseMaterial = Mesh->GetMaterial(0))
					{
						if (UMaterialInstanceDynamic* Mid = UMaterialInstanceDynamic::Create(BaseMaterial, Actor))
						{
							Mesh->SetMaterial(0, Mid);
							FOceanBeatDriveEntry Entry;
							Entry.Component = Mesh;
							Entry.Mid = Mid;
							Entries.Add(Entry);
							UE_LOG(LogTemp, Log, TEXT("MELODIA_OCEAN_BEAT_DRIVE: bound MID on %s (base %s)"), *Actor->GetName(), *BaseMaterial->GetName());
						}
					}
				}
			}
		}
		for (const FOceanBeatDriveEntry& Entry : Entries)
		{
			UMaterialInstanceDynamic* Mid = Entry.Mid.Get();
			if (!Mid)
			{
				continue;
			}
			// Baselines are the M_Oceanology_Inst defaults; deltas lift on the beat.
			Mid->SetScalarParameterValue(TEXT("PhaseGLow"), 0.75f + BeatPulse * 0.75f);
			Mid->SetScalarParameterValue(TEXT("HighlightBoost"), 10.0f + BeatPulse * 10.0f);
			Mid->SetScalarParameterValue(TEXT("ScatterBoost"), 10.0f + CombatEnergy * 5.0f);
			// DeepScatteringColor base (0.05, 0.25, 0.30); ImpactPulse pulls it toward
			// violet/emissive on impacts. Alpha untouched (0.15 absorption stays base).
			Mid->SetVectorParameterValue(TEXT("DeepScatteringColor"),
				FLinearColor(0.05f + ImpactPulse * 0.10f, 0.25f - ImpactPulse * 0.05f, 0.30f + ImpactPulse * 0.20f, 0.15f));
		}
	}
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
	// Missing NPC is not fatal: materials still pulse, FX simply stay unreactive. Warn
	// loudly though -- a silent zero here is exactly how this went unnoticed until now.
	NiagaraAudioParameterCollection = LoadObject<UNiagaraParameterCollection>(nullptr, AudioNpcPath);
	if (!NiagaraAudioParameterCollection)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("Melodia Niagara audio-reactivity disabled: missing %s (materials unaffected)"), AudioNpcPath);
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
	TRACE_CPUPROFILER_EVENT_SCOPE(UMelodiaAudioReactivePresentationSubsystem_TickPresentation);
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

	// --- Oceanology surface drive ------------------------------------------------
	// Same values as the MPC publish above, written as MI parameters because the
	// plugin master cannot sample the collection (see DriveOceanBeatValues header).
	// Game-worlds only: the drive must never mutate editor-viewport materials.
	if (World->IsGameWorld())
	{
		DriveOceanBeatValues(World, BeatPulseValue, bBattleActive ? BattleIntensity : 0.0f, ImpactPulse);
	}

	// --- Niagara mirror -------------------------------------------------------------
	// Same values, second collection. SetFloatParameter takes the FRIENDLY name, which
	// ParameterNameFromFriendlyString expands to NPC.MelodiaPalette.<Name> -- passing the
	// fully-qualified name here would silently write a parameter nobody reads.
	if (NiagaraAudioParameterCollection)
	{
		if (UNiagaraParameterCollectionInstance* NiagaraInstance =
				UNiagaraFunctionLibrary::GetNiagaraParameterCollection(World, NiagaraAudioParameterCollection))
		{
			const float Reactivity = bBattleActive ? BattleIntensity : 0.0f;
			NiagaraInstance->SetFloatParameter(TEXT("GlobalReactivity"), Reactivity);
			NiagaraInstance->SetFloatParameter(TEXT("Bass"), Reactivity);
			NiagaraInstance->SetFloatParameter(TEXT("Mid"), ImpactPulse);
			NiagaraInstance->SetFloatParameter(TEXT("Treble"), BeatPulseValue);
			NiagaraInstance->SetFloatParameter(TEXT("BeatPhase"), BeatPhase);
			NiagaraInstance->SetFloatParameter(TEXT("BeatPulse"), BeatPulseValue);
			NiagaraInstance->SetFloatParameter(TEXT("BeatIntensity"), BeatPulseValue);

			// --- Battle variation ---------------------------------------------------
			// Read from UMelodiaRhythmReactivitySubsystem::GetSignal(), which is the OWNER
			// of these values. An earlier version of this block recomputed
			// ComboNormalized/VictoryPulse/EnemyTension from UMelodiaBattleSession, which
			// created a second, subtly different definition of numbers this subsystem
			// already maintains -- the same two-sources-of-truth problem that produced the
			// duplicate wallet class and the duplicate palette asset. Reading the signal
			// also gets Crescendo/CommandEnergy/BreakPulse/RhythmPulse for free.
			if (const UMelodiaRhythmReactivitySubsystem* ReactivitySource =
					UMelodiaRhythmReactivitySubsystem::Get(World))
			{
				const FMelodiaRhythmReactivitySignal& Signal = ReactivitySource->GetSignal();
				NiagaraInstance->SetFloatParameter(TEXT("ComboNormalized"), Signal.ComboNormalized);
				NiagaraInstance->SetFloatParameter(TEXT("CrescendoNormalized"), Signal.CrescendoNormalized);
				NiagaraInstance->SetFloatParameter(TEXT("CommandEnergy"), Signal.CommandEnergy);
				NiagaraInstance->SetFloatParameter(TEXT("RhythmPulse"), Signal.CommandPulse);
				NiagaraInstance->SetFloatParameter(TEXT("BreakPulse"), Signal.BreakPulse);
				NiagaraInstance->SetFloatParameter(TEXT("VictoryPulse"), Signal.VictoryPulse);
				NiagaraInstance->SetFloatParameter(TEXT("EnemyTension"), Signal.EnemyTension);
			}
		}
	}
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
