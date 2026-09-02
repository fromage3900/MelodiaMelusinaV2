#include "MelodiaMusicClockSubsystem.h"

#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "HAL/IConsoleManager.h"
#include "HarmonixMetasound/Components/MusicClockComponent.h"
#include "HarmonixMetasound/MusicClock/MusicClockState.h"
#include "HarmonixMidi/MidiFile.h"
#include "HarmonixMidi/SongMaps.h"
#include "MelodiaAudioComponent.h"
#include "Stats/Stats.h"
#include "UObject/UObjectGlobals.h"

namespace
{
	/**
	 * Hard off-switch for the entire rhythm presentation layer.
	 *
	 * Every authored skill must remain fully playable, at full value, with this
	 * set to 1.  That is the acceptance test that stops a presentation layer
	 * from quietly becoming a second combat authority again (see Decision 011).
	 */
	static TAutoConsoleVariable<int32> CVarMelodiaRhythmDisable(
		TEXT("melodia.Rhythm.Disable"),
		0,
		TEXT("1 disables the Melodia rhythm presentation layer. Skills must play identically with it on."),
		ECVF_Default);

	bool IsRhythmLayerDisabled()
	{
		return CVarMelodiaRhythmDisable.GetValueOnGameThread() != 0;
	}

	/**
	 * Reported target tempo, for logging and for callers that want to know what
	 * the project's music is written at (128).
	 *
	 * This does NOT set the clock's tempo: Harmonix takes tempo from a song map,
	 * and the only safe way to supply one is a properly imported UMidiFile. See
	 * EnsureBattleControllerMusicClock for why hand-building one crashed.
	 */
	static TAutoConsoleVariable<float> CVarMelodiaMusicClockBPM(
		TEXT("melodia.MusicClock.BPM"),
		128.0f,
		TEXT("Tempo the project's music is authored at. Informational; assign a real UMidiFile TempoMap to change the clock."),
		ECVF_Default);

	const TCHAR* MelodiaBeatGridAssetPath =
		TEXT("/Game/MelodiaIntegration/MIDI/128BPMarpeggiomelody_beatgrid.128BPMarpeggiomelody_beatgrid");

	/** Signed distance from Value to the nearest whole number, in the range [-0.5, 0.5]. */
	float SignedFractionToNearest(float Value)
	{
		const float Fraction = Value - FMath::FloorToFloat(Value);
		return Fraction > 0.5f ? Fraction - 1.0f : Fraction;
	}
}

UMelodiaMusicClockSubsystem* UMelodiaMusicClockSubsystem::Get(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	return World ? World->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr;
}

float UMelodiaMusicClockSubsystem::GetMusicBeatPhase(const UObject* WorldContextObject)
{
	const UMelodiaMusicClockSubsystem* MusicClock = Get(WorldContextObject);
	return MusicClock ? MusicClock->GetBeatPhase(VisualTimebase) : 0.0f;
}

float UMelodiaMusicClockSubsystem::GetMusicPulse(const UObject* WorldContextObject)
{
	const UMelodiaMusicClockSubsystem* MusicClock = Get(WorldContextObject);
	if (!MusicClock || !MusicClock->HasMusicalTime())
	{
		return 0.0f;
	}

	// cos^2 peaks ON the beat and is continuous across the beat boundary, unlike
	// raw phase which snaps from 1 back to 0.
	//
	// This was sin^2, which has the right frequency but the WRONG PHASE:
	// BeatPhase is TotalBeats - floor(TotalBeats), so it is 0 exactly on the
	// beat, and sin^2(0) = 0 while sin^2(pi/2) = 1 at phase 0.5. That put the
	// peak precisely between beats -- every material bound to BeatPulse flashed
	// on the "and" instead of the downbeat. cos^2 is 1 at phase 0 and 1, 0 at
	// 0.5, which is what "pulses on the beat" actually means.
	const float Phase = MusicClock->GetBeatPhase(VisualTimebase);
	return FMath::Square(FMath::Cos(Phase * PI));
}

void UMelodiaMusicClockSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateUObject(this, &ThisClass::TickClock));
}

void UMelodiaMusicClockSubsystem::Deinitialize()
{
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}

	UnbindHarmonixClock(ActiveMusicClock.Get());
	ActiveMusicClock.Reset();
	RegisteredQuartzAudio.Reset();
	ReportedSource = EMelodiaMusicClockSource::None;

	Super::Deinitialize();
}

void UMelodiaMusicClockSubsystem::OnWorldBeginPlay(UWorld& InWorld)
{
	Super::OnWorldBeginPlay(InWorld);
	EnsureBattleControllerMusicClock();
}

bool UMelodiaMusicClockSubsystem::EnsureBattleControllerMusicClock()
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaMusicClockSubsystem_EnsureBattleControllerMusicClock);
	UWorld* World = GetWorld();
	if (!World || !World->IsGameWorld())
	{
		return false;
	}

	// Respect the off-switch: with the rhythm layer disabled we must not stand up
	// a clock, or `melodia.Rhythm.Disable 1` would stop being a true A/B control.
	if (IsRhythmLayerDisabled())
	{
		return false;
	}

	if (IsHarmonixClockRunning())
	{
		return true;
	}

	AActor* BattleController = nullptr;
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetClass()->GetName().StartsWith(TEXT("BP_BattleController")))
		{
			BattleController = *It;
			break;
		}
	}
	// Battle maps already provide the natural clock owner. Exploration maps such
	// as Sea Above intentionally have no BP_BattleController, but still need the
	// same authoritative musical time for world-key grading and presentation.
	// WorldSettings is a world-lifetime actor, so it is the correct host there;
	// this remains one clock owned by this subsystem, not a fallback time source.
	AActor* ClockOwner = BattleController ? BattleController : World->GetWorldSettings();
	if (!ClockOwner)
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_MUSICCLOCK could not resolve a clock owner in '%s'."), *World->GetName());
		return false;
	}

	UMusicClockComponent* Clock = ClockOwner->FindComponentByClass<UMusicClockComponent>();
	if (!Clock)
	{
		Clock = NewObject<UMusicClockComponent>(ClockOwner,
			BattleController ? TEXT("MelodiaBattleMusicClock") : TEXT("MelodiaWorldMusicClock"));
		if (!Clock)
		{
			UE_LOG(LogTemp, Error, TEXT("MELODIA_MUSICCLOCK failed to create a MusicClockComponent on '%s'."), *ClockOwner->GetName());
			return false;
		}
		// The wall-clock driver supplies transport. The imported MIDI below supplies
		// the complete tempo, bar, and beat maps used by every musical-time query.
		Clock->DriveMethod = EMusicClockDriveMethod::WallClock;
		Clock->RegisterComponent();
	}

	// A Harmonix default song map contains tempo and bar data but no authored beat
	// points. GetBeatInBarAtMs therefore requires a real imported MIDI with a
	// BEAT/PULSE track. Never hand-build or silently fall back from this asset: an
	// incomplete map turns the clock into a per-frame LogMIDI error source.
	UMidiFile* BeatGrid = LoadObject<UMidiFile>(nullptr, MelodiaBeatGridAssetPath);
	if (!IsValid(BeatGrid))
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_MUSICCLOCK required beat-grid MIDI is missing: %s"), MelodiaBeatGridAssetPath);
		return false;
	}

	const FSongMaps* SongMaps = BeatGrid->GetSongMaps();
	if (!SongMaps || SongMaps->TempoMapIsEmpty() || SongMaps->BarMapIsEmpty() || SongMaps->BeatMapIsEmpty())
	{
		UE_LOG(LogTemp, Error,
			TEXT("MELODIA_MUSICCLOCK refusing incomplete beat-grid MIDI '%s' (tempo=%s bar=%s beat=%s)."),
			MelodiaBeatGridAssetPath,
			SongMaps && !SongMaps->TempoMapIsEmpty() ? TEXT("ok") : TEXT("missing"),
			SongMaps && !SongMaps->BarMapIsEmpty() ? TEXT("ok") : TEXT("missing"),
			SongMaps && !SongMaps->BeatMapIsEmpty() ? TEXT("ok") : TEXT("missing"));
		return false;
	}

	Clock->SetTempoMapForWallClock(BeatGrid);
	Clock->SetRunPastMusicEnd(true);

	Clock->Start();
	RegisterMusicClock(Clock);

	// Verify rather than assume -- a registered clock that is not running leaves
	// HasMusicalTime() false and would reproduce the exact silent failure this
	// function exists to end.
	const bool bRunning = IsHarmonixClockRunning();
	if (bRunning)
	{
		UE_LOG(LogTemp, Log,
			TEXT("MELODIA_MUSICCLOCK wall-clock music clock running on '%s'; validated beat-grid MIDI at %.1f BPM 4/4; musical time is live."),
			*ClockOwner->GetName(), CVarMelodiaMusicClockBPM.GetValueOnGameThread());
	}
	else
	{
		UE_LOG(LogTemp, Error, TEXT("MELODIA_MUSICCLOCK clock on '%s' registered but is not running; musical time stays unavailable."),
			*ClockOwner->GetName());
	}
	return bRunning;
}

void UMelodiaMusicClockSubsystem::RegisterMusicClock(UMusicClockComponent* InClock)
{
	if (!InClock || ActiveMusicClock.Get() == InClock)
	{
		return;
	}

	UnbindHarmonixClock(ActiveMusicClock.Get());
	ActiveMusicClock = InClock;
	BindHarmonixClock(InClock);
}

void UMelodiaMusicClockSubsystem::UnregisterMusicClock(UMusicClockComponent* InClock)
{
	if (!InClock || ActiveMusicClock.Get() != InClock)
	{
		return;
	}

	UnbindHarmonixClock(InClock);
	ActiveMusicClock.Reset();
}

UMusicClockComponent* UMelodiaMusicClockSubsystem::GetActiveMusicClock() const
{
	return ActiveMusicClock.Get();
}

void UMelodiaMusicClockSubsystem::RegisterQuartzAudioComponent(UMelodiaAudioComponent* InAudioComponent)
{
	if (InAudioComponent)
	{
		RegisteredQuartzAudio = InAudioComponent;
	}
}

void UMelodiaMusicClockSubsystem::UnregisterQuartzAudioComponent(UMelodiaAudioComponent* InAudioComponent)
{
	if (InAudioComponent && RegisteredQuartzAudio.Get() == InAudioComponent)
	{
		RegisteredQuartzAudio.Reset();
	}
}

void UMelodiaMusicClockSubsystem::BindHarmonixClock(UMusicClockComponent* InClock)
{
	if (!InClock)
	{
		return;
	}

	// Beat and bar events follow TimebaseForBarAndBeatEvents on the component,
	// which Harmonix defaults to VideoRenderTime -- correct for the visual
	// pulses these events drive.  Input scoring does not use these events; it
	// samples the input timebase directly in GetTimingErrorMsToNearestBeat.
	InClock->BeatEvent.AddUniqueDynamic(this, &ThisClass::HandleHarmonixBeat);
	InClock->BarEvent.AddUniqueDynamic(this, &ThisClass::HandleHarmonixBar);
}

void UMelodiaMusicClockSubsystem::UnbindHarmonixClock(UMusicClockComponent* InClock)
{
	if (!InClock)
	{
		return;
	}

	InClock->BeatEvent.RemoveDynamic(this, &ThisClass::HandleHarmonixBeat);
	InClock->BarEvent.RemoveDynamic(this, &ThisClass::HandleHarmonixBar);
}

void UMelodiaMusicClockSubsystem::HandleHarmonixBeat(int BeatNumber, int BeatInBar)
{
	if (IsRhythmLayerDisabled())
	{
		return;
	}
	OnMelodiaBeat.Broadcast(BeatNumber, BeatInBar);
}

void UMelodiaMusicClockSubsystem::HandleHarmonixBar(int BarNumber)
{
	if (IsRhythmLayerDisabled())
	{
		return;
	}
	OnMelodiaBar.Broadcast(BarNumber);
}

bool UMelodiaMusicClockSubsystem::IsHarmonixClockRunning() const
{
	const UMusicClockComponent* Clock = ActiveMusicClock.Get();
	return Clock && Clock->GetState() == EMusicClockState::Running;
}

UMelodiaAudioComponent* UMelodiaMusicClockSubsystem::ResolveQuartzAudioComponent() const
{
	return RegisteredQuartzAudio.Get();
}

bool UMelodiaMusicClockSubsystem::IsQuartzClockRunning() const
{
	const UMelodiaAudioComponent* Audio = ResolveQuartzAudioComponent();
	return Audio && Audio->IsBattleClockRunning();
}

bool UMelodiaMusicClockSubsystem::HasMusicalTime() const
{
	if (IsRhythmLayerDisabled())
	{
		return false;
	}
	return IsHarmonixClockRunning() || IsQuartzClockRunning();
}

EMelodiaMusicClockSource UMelodiaMusicClockSubsystem::GetClockSource() const
{
	if (IsRhythmLayerDisabled())
	{
		return EMelodiaMusicClockSource::None;
	}
	if (IsHarmonixClockRunning())
	{
		return EMelodiaMusicClockSource::Harmonix;
	}
	if (IsQuartzClockRunning())
	{
		return EMelodiaMusicClockSource::Quartz;
	}
	return EMelodiaMusicClockSource::None;
}

FMelodiaMusicTime UMelodiaMusicClockSubsystem::GetMusicTime(ECalibratedMusicTimebase Timebase) const
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaMusicClockSubsystem_GetMusicTime);
	FMelodiaMusicTime Result;
	Result.Source = GetClockSource();

	switch (Result.Source)
	{
	case EMelodiaMusicClockSource::Harmonix:
	{
		const UMusicClockComponent* Clock = ActiveMusicClock.Get();
		if (!Clock)
		{
			// GetClockSource() already proved this non-null; degrade rather than
			// crash if that ever stops holding.
			Result.Source = EMelodiaMusicClockSource::None;
			break;
		}

		const float TotalBeats = Clock->GetBeatsIncludingCountIn(Timebase);
		const float TotalBars = Clock->GetBarsIncludingCountIn(Timebase);
		const float CurrentMs = Clock->GetSecondsIncludingCountIn(Timebase) * 1000.0f;
		const float MsPerBeat = Clock->GetMsPerBeatAtMs(CurrentMs);

		// Harmonix reports beat-in-bar 1-based (BeatMap.cpp: "beats relative to a
		// bar are always 1 based"), Quartz reports it 0-based.  Normalize to
		// 0-based here so consumers never have to know which source is live.
		const float HarmonixBeatInBar = Clock->GetBeatInBarAtMs(CurrentMs);

		Result.bValid = true;
		Result.TotalBeats = TotalBeats;
		Result.BeatPhase = TotalBeats - FMath::FloorToFloat(TotalBeats);
		Result.BeatInBar = FMath::Max(0.0f, HarmonixBeatInBar - 1.0f);
		Result.Bar = FMath::FloorToInt(TotalBars) + 1;
		Result.SecondsPerBeat = MsPerBeat > 0.0f ? MsPerBeat / 1000.0f : 0.0f;
		Result.TempoBPM = MsPerBeat > 0.0f ? 60000.0f / MsPerBeat : 0.0f;
		break;
	}

	case EMelodiaMusicClockSource::Quartz:
	{
		// Quartz reports a fractional beat within the bar and the tempo it was
		// started at.  It has no authored tempo map, so Bar and TotalBeats stay
		// 0 -- consumers that need them must branch on Source.
		const UMelodiaAudioComponent* Audio = ResolveQuartzAudioComponent();
		if (!Audio)
		{
			Result.Source = EMelodiaMusicClockSource::None;
			break;
		}

		const float BeatInBar = Audio->GetSongBeatPosition();
		const float BPM = Audio->GetBattleClockBPM();

		Result.bValid = true;
		Result.BeatInBar = BeatInBar;
		Result.BeatPhase = BeatInBar - FMath::FloorToFloat(BeatInBar);
		Result.TempoBPM = BPM;
		Result.SecondsPerBeat = BPM > 0.0f ? 60.0f / BPM : 0.0f;
		break;
	}

	case EMelodiaMusicClockSource::None:
	default:
		// No musical time.  Everything stays zeroed and bValid stays false so
		// presentation degrades instead of pulsing to a fabricated beat.
		break;
	}

	return Result;
}

float UMelodiaMusicClockSubsystem::GetBeatPhase(ECalibratedMusicTimebase Timebase) const
{
	return GetMusicTime(Timebase).BeatPhase;
}

float UMelodiaMusicClockSubsystem::GetTempoBPM() const
{
	return GetMusicTime(VisualTimebase).TempoBPM;
}

float UMelodiaMusicClockSubsystem::GetSecondsToNextBeat() const
{
	const FMelodiaMusicTime Time = GetMusicTime(VisualTimebase);
	if (!Time.bValid || Time.SecondsPerBeat <= 0.0f)
	{
		return 0.0f;
	}

	return (1.0f - Time.BeatPhase) * Time.SecondsPerBeat;
}

float UMelodiaMusicClockSubsystem::GetSecondsToNextBar() const
{
	const FMelodiaMusicTime Time = GetMusicTime(VisualTimebase);
	if (!Time.bValid || Time.SecondsPerBeat <= 0.0f)
	{
		return 0.0f;
	}

	const UMusicClockComponent* Clock = ActiveMusicClock.Get();
	if (Time.Source != EMelodiaMusicClockSource::Harmonix || !Clock)
	{
		// Quartz exposes no bar length; the next beat is the honest answer.
		return GetSecondsToNextBeat();
	}

	const float CurrentMs = Clock->GetSecondsIncludingCountIn(VisualTimebase) * 1000.0f;
	const float BeatsInBar = Clock->GetNumBeatsInBarAtMs(CurrentMs);
	if (BeatsInBar <= 0.0f)
	{
		return GetSecondsToNextBeat();
	}

	const float BeatsRemaining = BeatsInBar - FMath::Fmod(Time.BeatInBar, BeatsInBar);
	return BeatsRemaining * Time.SecondsPerBeat;
}

float UMelodiaMusicClockSubsystem::GetSubdivisionSeconds(const int32 Divisions) const
{
	if (Divisions <= 0)
	{
		return 0.0f;
	}

	const FMelodiaMusicTime Time = GetMusicTime(VisualTimebase);
	return Time.bValid ? Time.SecondsPerBeat / static_cast<float>(Divisions) : 0.0f;
}

float UMelodiaMusicClockSubsystem::GetTimingErrorMsToNearestBeat() const
{
	// Sampled on the input timebase: what the player is actually experiencing,
	// not where the audio renderer or the video frame happens to be.
	const FMelodiaMusicTime Time = GetMusicTime(InputTimebase);
	if (!Time.bValid || Time.SecondsPerBeat <= 0.0f)
	{
		return 0.0f;
	}

	const float BeatPosition = Time.Source == EMelodiaMusicClockSource::Harmonix ? Time.TotalBeats : Time.BeatInBar;
	const float ErrorInBeats = SignedFractionToNearest(BeatPosition);
	return ErrorInBeats * Time.SecondsPerBeat * 1000.0f - CalibrationOffsetMs;
}

void UMelodiaMusicClockSubsystem::SetCalibrationOffsetMs(float InOffsetMs)
{
	CalibrationOffsetMs = FMath::Clamp(InOffsetMs, -500.0f, 500.0f);
}

bool UMelodiaMusicClockSubsystem::TickClock(float DeltaTime)
{
	TRACE_CPUPROFILER_EVENT_SCOPE(MelodiaMusicClockSubsystem_TickClock);
	const EMelodiaMusicClockSource CurrentSource = GetClockSource();
	if (CurrentSource != ReportedSource)
	{
		ReportedSource = CurrentSource;
		LastQuartzBeatIndex = -1;
		QuartzRunningBeat = 0;
		OnClockSourceChanged.Broadcast(CurrentSource);
	}

	// Harmonix broadcasts its own beat/bar events, so only the Quartz path needs
	// edge detection here.
	if (CurrentSource != EMelodiaMusicClockSource::Quartz)
	{
		return true;
	}

	const FMelodiaMusicTime Time = GetMusicTime(InputTimebase);
	if (!Time.bValid)
	{
		return true;
	}

	const int32 BeatIndex = FMath::FloorToInt(Time.BeatInBar);
	if (BeatIndex != LastQuartzBeatIndex)
	{
		LastQuartzBeatIndex = BeatIndex;
		++QuartzRunningBeat;
		OnMelodiaBeat.Broadcast(QuartzRunningBeat, BeatIndex);
	}

	return true;
}

// Lets the clock be stood up and inspected from a live PIE session. Reports BPM
// on success so "is musical time actually live?" is answerable in one command
// rather than inferred from whether materials look like they are moving.
static FAutoConsoleCommandWithWorld GMelodiaStartMusicClock(
	TEXT("melodia.MusicClock.Ensure"),
	TEXT("Put a running wall-clock Harmonix music clock on the battle controller and report whether musical time is live."),
	FConsoleCommandWithWorldDelegate::CreateLambda([](UWorld* World)
	{
		if (UMelodiaMusicClockSubsystem* MusicClock = World ? World->GetSubsystem<UMelodiaMusicClockSubsystem>() : nullptr)
		{
			MusicClock->EnsureBattleControllerMusicClock();
		}
	}));
