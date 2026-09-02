#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "MelodiaDressingSubsystem.generated.h"

class AActor;

/**
 * Dash-capability — native environment dressing / art-pass subsystem.
 *
 * Implements the SSOT "Dash" role (Docs/Research/AGENT_TOOLCHAIN_DISCOVERY_INDEX:
 * "fast final human composition pass") using the assets and PCG families we
 * already have — hero prop placement, physically-dropped debris, and composition
 * cleanup around camera-critical areas. It is NOT the commercial Polygonflow
 * plugin (absent), does NOT create a new procedural/master authority, and writes
 * no Content/_PROJECT/.
 *
 * Editorial / presentation-only. Editor trial priority; no shipping dependency.
 * Plan: Docs/Research/DASH_MAGPIE_NATIVE_INTEGRATION_2026-08-31.md
 */
UCLASS()
class BS_GODFILE_API UMelodiaDressingSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	/** Place Count tagged hero props from the dressing catalog around CameraFocus. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Dressing")
	bool DressHeroClutter(AActor* CameraFocus, const FName& FamilyTag, int32 Count);

	/** Drop loose debris (logs/rocks/field gear) under gravity from a spawn offset. */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Dressing")
	bool PhysicallyDrop(const TArray<AActor*>& Actors, FVector DropOffset, float Restitution);

	/**
	 * Report (never delete) props occluding camera-critical framing within Radius.
	 * Returns a warning list to the owner; foreign assets are never removed.
	 */
	UFUNCTION(BlueprintCallable, Category = "Melodia|Dressing")
	TArray<AActor*> FindCompositionOccluders(AActor* CameraFocus, float Radius, int32 MaxReports);

	/** Catalog asset path for the dressing hero-prop families. */
	UFUNCTION(BlueprintPure, Category = "Melodia|Dressing")
	FSoftObjectPath GetDressingCatalogPath() const;

private:
	FName ActiveFamily = NAME_None;
};