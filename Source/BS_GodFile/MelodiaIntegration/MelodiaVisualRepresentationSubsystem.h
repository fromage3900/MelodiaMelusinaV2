#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaVisualRepresentationSubsystem.generated.h"

/**
 * Magpie seam — simulation truth vs visual truth (READ contract only).
 *
 * Promoted from WATCH/RESEARCH to architecture scaffold by owner task 2026-08-31
 * (Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md). It formalizes the
 * seam that a future Magpie-style generative frame renderer would consume:
 * simulation state stays authoritative (JRPG template / UMelodiaNarrativeSubsystem /
 * UMelodiaRhythmCombatSubsystem), and this subsystem exposes STABLE READ accessors
 * onto it as "visual truth" inputs for presentation.
 *
 * This is NOT a renderer and NOT a second writer. It generates no frames, mutates
 * no gameplay, and owns no HUD. It exists so a generative renderer can be swapped
 * under the presentation layer without touching simulation.
 *
 * Guardrails: AGENTS.md convergence rule; MelodiaCore presentation-only doctrine.
 */
UCLASS()
class BS_GODFILE_API UMelodiaVisualRepresentationSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Current rhythm grade visual key (Perfect/Great/Good/Miss) as an FName for presentation. */
	UFUNCTION(BlueprintPure, Category = "Melodia|VisualTruth")
	FName GetCurrentRhythmGradeKey() const;

	/** Beat phase in [0,1) for frame-level visual sync (mirrors MPC_Melodia_Palette BeatPulse). */
	UFUNCTION(BlueprintPure, Category = "Melodia|VisualTruth")
	float GetBeatPhaseNormalized() const;

	/** Whether a battle is currently active (visual truth reflects battle state). */
	UFUNCTION(BlueprintPure, Category = "Melodia|VisualTruth")
	bool IsBattleActive() const;

	/** Presentation-affecting narrative flags snapshot (read-only). */
	UFUNCTION(BlueprintPure, Category = "Melodia|VisualTruth")
	TArray<FName> GetActiveNarrativeVisualFlags() const;

	/** Determinism assertion: this subsystem performs NO writes to simulation state. */
	UFUNCTION(BlueprintPure, Category = "Melodia|VisualTruth")
	bool IsReadOnlyByContract() const { return true; }

private:
	// No mutable simulation state is held here by design — reads are forwarded to
	// the owning authorities (UMelodiaRhythmCombatSubsystem, UMelodiaNarrativeSubsystem,
	// MPC_Melodia_Palette) at call time. A future Magpie renderer consumes these reads.
};