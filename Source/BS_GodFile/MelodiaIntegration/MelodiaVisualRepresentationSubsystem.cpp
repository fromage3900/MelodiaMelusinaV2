#include "MelodiaVisualRepresentationSubsystem.h"

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