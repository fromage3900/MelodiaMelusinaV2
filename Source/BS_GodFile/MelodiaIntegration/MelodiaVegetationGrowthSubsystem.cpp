#include "MelodiaVegetationGrowthSubsystem.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"

bool UMelodiaVegetationGrowthSubsystem::PlaceSpeedTreeBiomeTest(AActor* RegionAnchor, const FName& BiomeFamily)
{
	if (!RegionAnchor)
	{
		return false;
	}
	// Scaffold: validates the research-named tool and logs intent. Live: a PCG
	// graph spawns SpeedTree-family plants in the sandbox region around RegionAnchor,
	// asserting it supplements (never replaces) the SpeedTree biome. Requires a
	// live editor + Monolith :9316 + sandbox map only.
	UE_LOG(LogTemp, Log, TEXT("[VegRND] PlaceSpeedTreeBiomeTest family=%s anchor=%s"),
		*BiomeFamily.ToString(), *RegionAnchor->GetName());
	return true;
}

bool UMelodiaVegetationGrowthSubsystem::MutateSecondaryGrowth(AActor* HostMesh, const int32 Seed, const float Density)
{
	if (!HostMesh || Density <= 0.f)
	{
		return false;
	}
	// Scaffold: PCG secondary-growth mutation seeded for determinism. Not a
	// SpeedTree replacement; supplements a SpeedTree-driven biome.
	UE_LOG(LogTemp, Log, TEXT("[VegRND] MutateSecondaryGrowth host=%s seed=%d density=%.2f"),
		*HostMesh->GetName(), Seed, Density);
	return true;
}

bool UMelodiaVegetationGrowthSubsystem::GraftBranch(AActor* HostBranch, const int32 VariantIndex, const bool bDryRun)
{
	if (!HostBranch)
	{
		return false;
	}
	UE_LOG(LogTemp, Log, TEXT("[VegRND] GraftBranch host=%s variant=%d dry=%d"),
		*HostBranch->GetName(), VariantIndex, bDryRun ? 1 : 0);
	return true;
}