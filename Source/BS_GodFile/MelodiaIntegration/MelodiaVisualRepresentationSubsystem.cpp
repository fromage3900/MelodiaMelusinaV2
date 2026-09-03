#include "MelodiaVisualRepresentationSubsystem.h"
#include "MelodiaCymaticsSubsystem.h"
#include "Engine/Engine.h"

FName UMelodiaVisualRepresentationSubsystem::GetCurrentRhythmGradeKey() const
{
	// Scaffold: read-only. Live implementation forwards to
	// UMelodiaRhythmCombatSubsystem's current grade (Perfect/Great/Good/Miss) as
	// the visual-truth key. Offline returns the neutral default so the contract
	// is exercisable without a live session.
	return NAME_None;
}

float UMelodiaVisualRepresentationSubsystem::GetBeatPhaseNormalized() const
{
	// Scaffold: mirrors MPC_Melodia_Palette "BeatPhase" (0..1) written each frame
	// by UMelodiaAudioReactivePresentationSubsystem. Read-only — never writes the MPC.
	return 0.f;
}

bool UMelodiaVisualRepresentationSubsystem::IsBattleActive() const
{
	// Scaffold: forwards to the battle-session authority. No state held here.
	return false;
}

TArray<FName> UMelodiaVisualRepresentationSubsystem::GetActiveNarrativeVisualFlags() const
{
	// Scaffold: forwards to UMelodiaNarrativeSubsystem presentation-affecting
	// flags. Empty offline. Read-only by contract (IsReadOnlyByContract == true).
	return TArray<FName>{};
}

float UMelodiaVisualRepresentationSubsystem::GetWorldFieldTension(float U, float V) const
{
	// Faraway Mother seam: WorldField.Tension = |grad Z|/8 derived from Chladni (3,5).
	// READ-ONLY: forwards to UMelodiaCymaticsSubsystem::SampleCymaticAmplitude and computes
	// tension via gradient magnitude so visual truth never mutates simulation.
	if (const UGameInstance* GI = GetGameInstance())
	{
		if (const UMelodiaCymaticsSubsystem* Cym = GI->GetSubsystem<UMelodiaCymaticsSubsystem>())
		{
			const float Eps = 0.001f;
			const float A00 = Cym->SampleCymaticAmplitude(U, V);
			const float Ax = Cym->SampleCymaticAmplitude(U + Eps, V);
			const float Ay = Cym->SampleCymaticAmplitude(U, V + Eps);
			const float Gx = (Ax - A00) / Eps;
			const float Gy = (Ay - A00) / Eps;
			const float Mag = FMath::Sqrt(Gx * Gx + Gy * Gy);
			return FMath::Clamp(Mag / 8.0f, 0.0f, 1.0f);
		}
	}
	return 0.f;
}

float UMelodiaVisualRepresentationSubsystem::GetCymaticAmplitude(float U, float V) const
{
	if (const UGameInstance* GI = GetGameInstance())
	{
		if (const UMelodiaCymaticsSubsystem* Cym = GI->GetSubsystem<UMelodiaCymaticsSubsystem>())
		{
			return Cym->SampleCymaticAmplitude(U, V);
		}
	}
	return 0.f;
}

void UMelodiaVisualRepresentationSubsystem::GetCelestialSilkWeaveState(int32& OutModeN, int32& OutModeM, float& OutBeatPulse) const
{
	OutModeN = 3;
	OutModeM = 5;
	OutBeatPulse = 0.f;
	if (const UGameInstance* GI = GetGameInstance())
	{
		if (const UMelodiaCymaticsSubsystem* Cym = GI->GetSubsystem<UMelodiaCymaticsSubsystem>())
		{
			Cym->GetCymaticMode(OutModeN, OutModeM);
			OutBeatPulse = Cym->GetBeatPulse();
		}
	}
}
