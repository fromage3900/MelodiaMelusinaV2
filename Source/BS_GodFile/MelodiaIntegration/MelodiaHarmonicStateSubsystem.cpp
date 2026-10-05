#include "MelodiaHarmonicStateSubsystem.h"
#include "MelodiaMusicClockSubsystem.h"
#include "MelodiaRhythmReactivitySubsystem.h"
#include "Materials/MaterialParameterCollection.h"
#include "Materials/MaterialParameterCollectionInstance.h"
#include "Containers/Ticker.h"
#include "Engine/World.h"

void UMelodiaHarmonicStateSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	// Sole write surface. The asset may not exist yet at first boot; the tick
	// no-ops until it does (same policy as UMelodiaCymaticsWriterSubsystem).
	StateCollection = LoadObject<UMaterialParameterCollection>(nullptr,
		TEXT("/Game/Melodia/Audio/Mix/MPC_Melodia_HarmonicState.MPC_Melodia_HarmonicState"));

	if (!StateCollection)
	{
		UE_LOG(LogTemp, Warning, TEXT("[HarmonicState] MPC_Melodia_HarmonicState not found -- writer idle until the asset exists."));
	}

	// Note feed: bind to the reactivity subsystem's per-note event rather than
	// re-plumbing every call site that already calls NotifyPlayedNote. WorldSubsystem
	// init order is not guaranteed, so if it is not up yet we retry from the tick.
	TryBindNoteFeed();

	TickerHandle = FTSTicker::GetCoreTicker().AddTicker(
		FTickerDelegate::CreateUObject(this, &UMelodiaHarmonicStateSubsystem::TickState));
}

void UMelodiaHarmonicStateSubsystem::TryBindNoteFeed()
{
	if (bNoteFeedBound)
	{
		return;
	}
	if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
	{
		Reactivity->OnNotePlayed.AddUniqueDynamic(this, &UMelodiaHarmonicStateSubsystem::OnNotePlayed);
		bNoteFeedBound = true;
	}
}

void UMelodiaHarmonicStateSubsystem::Deinitialize()
{
	if (bNoteFeedBound)
	{
		if (UMelodiaRhythmReactivitySubsystem* Reactivity = UMelodiaRhythmReactivitySubsystem::Get(this))
		{
			Reactivity->OnNotePlayed.RemoveDynamic(this, &UMelodiaHarmonicStateSubsystem::OnNotePlayed);
		}
		bNoteFeedBound = false;
	}
	if (TickerHandle.IsValid())
	{
		FTSTicker::GetCoreTicker().RemoveTicker(TickerHandle);
		TickerHandle.Reset();
	}
	Super::Deinitialize();
}

void UMelodiaHarmonicStateSubsystem::NotifyNote(int32 MidiNoteNumber, float Velocity01)
{
	ActiveNotes.Add(FActiveNote{MidiNoteNumber, 4.0f * SecondsPerBeat, FMath::Clamp(Velocity01, 0.1f, 1.0f)});
	if (ActiveNotes.Num() > MaxActiveNotes)
	{
		ActiveNotes.RemoveAt(0);
	}
}

void UMelodiaHarmonicStateSubsystem::OnNotePlayed(int32 MidiNote, EMelodiaRhythmGrade Grade)
{
	// A graded note is what the player actually hears; feed it in. Misses still
	// carry a pitch (the motif the player should have hit) but at low energy so
	// a missed run does not fake a bright chord.
	const float Energy = Grade == EMelodiaRhythmGrade::Miss ? 0.2f : 1.0f;
	NotifyNote(MidiNote, Energy);
}

void UMelodiaHarmonicStateSubsystem::SetPCGResonanceDensity(float Density01)
{
	// The sensor eases on its own cadence; we clamp only, no second easing here,
	// so the published lane is a faithful copy of the measured local density.
	PCGResonanceDensity = FMath::Clamp(Density01, 0.0f, 1.0f);
}

void UMelodiaHarmonicStateSubsystem::SetChord(const TArray<int32>& MidNumbers)
{
	ActiveNotes.Reset();
	for (const int32 Note : MidNumbers)
	{
		ActiveNotes.Add(FActiveNote{Note, 6.0f * SecondsPerBeat, 1.0f});
	}
}

bool UMelodiaHarmonicStateSubsystem::IsTense() const
{
	return Tension >= TensionThreshold;
}

bool UMelodiaHarmonicStateSubsystem::TickState(float DeltaTime)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return true;
	}

	// Defer the note-feed bind until the reactivity subsystem is actually up
	// (it initializes as a separate WorldSubsystem with no ordering guarantee).
	TryBindNoteFeed();

	UMelodiaMusicClockSubsystem* Clock = UMelodiaMusicClockSubsystem::Get(this);
	if (!Clock)
	{
		return true;
	}
	const FMelodiaMusicTime Time = Clock->GetMusicTime(UMelodiaMusicClockSubsystem::VisualTimebase);

	// Track the real tempo even when no clock is running the beat (the clock
	// reports 0 then); decay timers must use the actual seconds-per-beat.
	if (Time.bValid && Time.TempoBPM > 20.0f && Time.TempoBPM < 300.0f)
	{
		SecondsPerBeat = 60.0f / Time.TempoBPM;
	}

	DecayNotes(DeltaTime);
	Evaluate(Time, DeltaTime);

	if (StateCollection)
	{
		if (UMaterialParameterCollectionInstance* Instance = World->GetParameterCollectionInstance(StateCollection))
		{
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_Tension")), Tension);
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_Consonance")), Consonance);
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_Dissonance")), Dissonance);
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_Mode")), static_cast<float>(Mode));
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_Resolution")), ResolutionPulse);
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_BarPhase")), BarPhase01);
			Instance->SetScalarParameterValue(FName(TEXT("Harmonic_Tempo")), Time.TempoBPM > 0.0f ? Time.TempoBPM : 128.0f);
			Instance->SetScalarParameterValue(FName(TEXT("PCG_ResonanceDensity")), PCGResonanceDensity);
		}
	}
	return true;
}

void UMelodiaHarmonicStateSubsystem::DecayNotes(float DeltaTime)
{
	for (int32 i = ActiveNotes.Num() - 1; i >= 0; --i)
	{
		FActiveNote& Note = ActiveNotes[i];
		Note.Lifetime -= DeltaTime;
		Note.Energy = FMath::Lerp(0.25f, Note.Energy, 0.5f); // fade toward a floor so chord roots linger
		if (Note.Lifetime <= 0.0f)
		{
			ActiveNotes.RemoveAt(i);
		}
	}
}

void UMelodiaHarmonicStateSubsystem::Evaluate(const FMelodiaMusicTime& Time, float DeltaTime)
{
	// ── 1. Pitch content -> interval roughness ─────────────────────────────
	const int32 PitchCount = ActiveNotes.Num();
	float DissonanceRaw = 0.0f;
	if (PitchCount > 1)
	{
		int32 Pairs = 0;
		for (int32 i = 0; i < PitchCount; ++i)
		{
			for (int32 j = i + 1; j < PitchCount; ++j)
			{
				const int32 Dist = FMath::Abs(ActiveNotes[i].Midi - ActiveNotes[j].Midi);
				const int32 Pcs = FMath::Min(Dist % 12, 12 - (Dist % 12)); // 0..6 symmetric
				DissonanceRaw += IntervalRoughness(Pcs) * 0.5f * (ActiveNotes[i].Energy + ActiveNotes[j].Energy);
				++Pairs;
			}
		}
		DissonanceRaw /= static_cast<float>(Pairs);
	}
	// Unpitched silence is consonant, not dissonant.
	DissonanceRaw = PitchCount == 0 ? 0.0f : DissonanceRaw;

	// ── 2. Mode from the most stable 3-note subset of the window ───────────
	// Score each root + each of the 5 triad qualities against the active pitch
	// set; the highest-scoring stable assignment wins. Bias toward the lowest
	// root in the window (Melusina's piano work is root-position centric).
	uint8 BestMode = 0;
	float BestScore = 0.0f;
	if (PitchCount > 0)
	{
		const int32 Root = ActiveNotes[0].Midi;
		const int32 RootPc = ((Root % 12) + 12) % 12;
		const TArray<int32> Qualities[] = {
			TArray<int32>{ 0, 4, 7 }, // major
			TArray<int32>{ 0, 3, 7 }, // minor
			TArray<int32>{ 0, 4, 10 }, // dominant
			TArray<int32>{ 0, 3, 6 },  // diminished
			TArray<int32>{ 0, 4, 8 },  // augmented
		};
		for (int32 q = 0; q < 5; ++q)
		{
			float Coverage = 0.0f;
			for (const int32 Offset : Qualities[q])
			{
				const int32 TargetPc = (RootPc + Offset) % 12;
				bool Found = false;
				for (const FActiveNote& Note : ActiveNotes)
				{
					if (((Note.Midi % 12) + 12) % 12 == TargetPc) { Found = true; break; }
				}
				if (Found) { Coverage += 1.0f; }
			}
			const float Score = (Coverage / 3.0f) * (q == 0 || q == 1 ? 1.0f : 0.9f);
			if (Score > BestScore)
			{
				BestScore = Score;
				BestMode = static_cast<uint8>(q + 1);
			}
		}
	}

	// ── 3. Tension composite ───────────────────────────────────────────────
	// Dissonance base, plus a rhythmic anticipation curve that peaks just
	// before the downbeat of each beat (players feel the "pull" into the beat),
	// plus a slow bar-arc that raises tension through the back half of the
	// 8-beat harmonic cycle (authored content phrases over ~2 bars).
	const float BeatAnticipation = 0.15f * FMath::Square(1.0f - FMath::Abs(Time.BeatPhase - 1.0f));
	const float BarArc = Time.bValid ? 0.25f * FMath::Clamp(FMath::Fmod(Time.TotalBeats, 8.0f) / 8.0f, 0.0f, 1.0f) : 0.0f;
	const float TensionTarget = FMath::Clamp(DissonanceRaw * 0.8f + BeatAnticipation + BarArc, 0.0f, 1.0f);

	// Tension eases up slowly (dread builds), down faster (resolution is felt).
	const float UpRate = 1.2f;    // ~0.8s to rise a unit
	const float DownRate = 2.8f;  // ~0.4s to fall a unit
	const float Rate = TensionTarget > Tension ? UpRate : DownRate;
	Tension = EaseFloat(Tension, TensionTarget, Rate, DeltaTime);

	// Resolution pulse: only when tension is actually dropping, so a held
	// chord does not breathe. Positive-only, fast attack, fast decay.
	const float TensionDelta = Tension - LastTensionForResolution;
	LastTensionForResolution = Tension;
	const float ReleasePulse = FMath::Clamp(-TensionDelta * 20.0f, 0.0f, 1.0f);
	ResolutionPulse = FMath::Max(ReleasePulse, ResolutionPulse * FMath::Exp(-4.0f * DeltaTime));

	// ── 4. Consonance = stability complement ───────────────────────────────
	// Consonant when the pitch set is quiet AND in a stable mode.
	const float ModeStability = (BestMode == 0 || BestMode == 1 || BestMode == 2) ? 1.0f : (BestMode == 3 ? 0.5f : 0.25f);
	const float ConsonanceTarget = FMath::Clamp((1.0f - DissonanceRaw) * ModeStability, 0.0f, 1.0f);
	Consonance = EaseFloat(Consonance, ConsonanceTarget, 1.5f, DeltaTime);

	// ── 5. Publish the eased registers ─────────────────────────────────────
	Dissonance = EaseFloat(Dissonance, DissonanceRaw, 2.0f, DeltaTime);
	Mode = BestScore > 0.5f ? BestMode : 0; // require a majority of the triad present
	BarPhase01 = Time.bValid ? FMath::Clamp(FMath::Fmod(Time.TotalBeats, 8.0f) / 8.0f, 0.0f, 1.0f) : 0.0f;
}

float UMelodiaHarmonicStateSubsystem::IntervalRoughness(int32 Semitones)
{
	// Sensory-dissonance curve for discrete semitone intervals (0 = unison/octave,
	// 1 = minor 2nd ... 6 = tritone). Modeled on Plomp & Levelt's roughness:
	// peaks at minor 2nd and tritone, deep wells at major 3rd / perfect 5th.
	switch (Semitones)
	{
	case 0:  return 0.00f; // unison / octave
	case 1:  return 0.92f; // minor 2nd
	case 2:  return 0.65f; // major 2nd
	case 3:  return 0.30f; // minor 3rd
	case 4:  return 0.22f; // major 3rd
	case 5:  return 0.42f; // perfect 4th
	case 6:  return 0.88f; // tritone
	default: return 0.50f;
	}
}

float UMelodiaHarmonicStateSubsystem::EaseFloat(float Current, float Target, float Rate, float DeltaTime)
{
	// Exponential approach: Current + (Target-Current) * (1 - e^(-Rate*Dt)).
	return Current + (Target - Current) * (1.0f - FMath::Exp(-Rate * DeltaTime));
}
