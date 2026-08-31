#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaVegetationGrowthSubsystem.generated.h"

class AActor;

/**
 * UE Procedural Vegetation / PCG growth R&D — NOT a SpeedTree replacement.
 *
 * Implements the C-R&D row of the emerging-toolchain research
 * (Docs/Research/EMERGING_3D_RENDERING_TOOLCHAIN_RESEARCH_2026-08-30.md):
 * experimental Unreal-side procedural growth — secondary bizarre growth,
 * local grafting/mutation, growth around geometry — using PCG.
 *
 * SpeedTree remains the production plant authoring system. This subsystem only
 * tests whether PVE-style mutation can supplement a SpeedTree-driven biome
 * cheaper than building secondary growth in Houdini/SpeedTree. If not, discard.
 *
 * Guardrails: sandbox-only (PlaceSpeedTreeBiomeTest), no new material master,
 * no Content/_PROJECT/ writes. Convergence: PCG is the distribution authority.
 */
UCLASS()
class BS_GODFILE_API UMelodiaVegetationGrowthSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Research-named tool: PCG-driven biome test in a sandbox region. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|VegetationRND")
	bool PlaceSpeedTreeBiomeTest(AActor* RegionAnchor, const FName& BiomeFamily);

	/** Procedural secondary growth around geometry (mutate, not replace). */
	UFUNCTION(BlueprintCallable, Category = "Melodia|VegetationRND")
	bool MutateSecondaryGrowth(AActor* HostMesh, int32 Seed, float Density);

	/** Local grafting/mutation experiment on a branch host. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|VegetationRND")
	bool GraftBranch(AActor* HostBranch, int32 VariantIndex, bool bDryRun);

	/** Whether this R&D is sandbox-only (guards against touching chapter maps). */
	UFUNCTION(BlueprintPure, Category = "Melodia|VegetationRND")
	bool IsSandboxOnly() const { return bSandboxOnly; }

private:
	bool bSandboxOnly = true; // research hard guardrail
};