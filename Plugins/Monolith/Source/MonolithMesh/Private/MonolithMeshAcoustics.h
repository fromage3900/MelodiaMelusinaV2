#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "MonolithMeshAcoustics.generated.h"

/**
 * Row struct for the surface acoustics DataTable.
 * Must be at global scope for UHT (USTRUCT cannot live inside a namespace).
 */
USTRUCT()
struct FAcousticSurfaceRow : public FTableRowBase
{
	GENERATED_BODY()

	/** Sound absorption coefficient 0-1 (higher = more absorbed) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Acoustics")
	float AbsorptionCoefficient = 0.02f;

	/** Transmission loss in dB through this material */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Acoustics")
	float TransmissionLossdB = 40.0f;

	/** Footstep loudness factor 0-1 (higher = louder footsteps) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Acoustics")
	float FootstepLoudness = 0.6f;

	/** Display name for this surface */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Acoustics")
	FString DisplayName;
};

/**
 * Acoustic calculation helpers for Phase 8 Audio actions.
 * Surface property lookup, Sabine RT60, attenuation, image-source reflections.
 *
 * Loads acoustic properties from a DataTable (UMonolithSettings::SurfaceAcousticsTablePath).
 * Falls back to hardcoded defaults if no table exists.
 * Coefficients calibrated from Steam Audio reference data (not a runtime dependency).
 */
namespace MonolithMeshAcoustics
{
	// ========================================================================
	// Acoustic Surface Properties
	// ========================================================================

	/** Resolved acoustic properties for a surface */
	struct FAcousticProperties
	{
		float Absorption = 0.02f;       // 0-1
		float TransmissionLossdB = 40.0f;
		float FootstepLoudness = 0.6f;
		FString SurfaceName = TEXT("Default");
	};

	/** Get acoustic properties for a physical surface type. Checks DataTable first, then hardcoded. */
	FAcousticProperties GetPropertiesForSurface(EPhysicalSurface SurfaceType);

	/** Get acoustic properties by surface name string. Checks DataTable first, then hardcoded. */
	FAcousticProperties GetPropertiesForName(const FString& SurfaceName);

	/** Get the default properties (concrete) */
	FAcousticProperties GetDefaultProperties();

	/** Get all hardcoded surface entries (used to bootstrap DataTable) */
	TMap<FString, FAcousticProperties> GetHardcodedDefaults();

	// ========================================================================
	// Sabine RT60
	// ========================================================================

	/** RT60 classification */
	enum class ERoomAcousticType : uint8
	{
		Dead,    // < 0.3s
		Dry,     // 0.3 - 0.6s
		Live,    // 0.6 - 1.5s
		Echo     // > 1.5s
	};

	const TCHAR* AcousticTypeToString(ERoomAcousticType Type);

	/**
	 * Compute Sabine RT60 reverberation time.
	 * RT60 = 0.161 * VolumeM3 / TotalAbsorption
	 * @param VolumeM3          Room volume in cubic meters
	 * @param TotalAbsorption   Sum of (surface_area * absorption_coefficient) for all surfaces, in m^2
	 * @return RT60 in seconds
	 */
	float ComputeSabineRT60(float VolumeM3, float TotalAbsorption);

	/** Classify RT60 into room type */
	ERoomAcousticType ClassifyRT60(float RT60Seconds);

	// ========================================================================
	// Attenuation & Propagation
	// ========================================================================

	/**
	 * Compute distance attenuation factor (inverse-square law).
	 * @param Distance  Distance in cm
	 * @param RefDist   Reference distance (100% loudness) in cm
	 * @return 0-1 attenuation factor
	 */
	float ComputeDistanceAttenuation(float Distance, float RefDist = 100.0f);

	/**
	 * Convert dB reduction to a linear 0-1 factor.
	 * factor = 10^(-dB/20)
	 */
	float DbToLinear(float dB);

	/**
	 * Estimate total transmission loss through walls between two points.
	 * Traces from->to, accumulates transmission loss for each wall hit.
	 * @param World         Editor world
	 * @param From          Source position
	 * @param To            Listener position
	 * @param OutWallCount  Number of walls penetrated
	 * @param OutTotalLossdB Total dB loss through walls
	 * @return Occlusion factor 0-1 (0 = fully occluded, 1 = no occlusion)
	 */
	float TraceOcclusion(UWorld* World, const FVector& From, const FVector& To,
		int32& OutWallCount, float& OutTotalLossdB);

	// ========================================================================
	// Image-Source Reflection
	// ========================================================================

	/** A sound path from source to listener */
	struct FSoundPath
	{
		TArray<FVector> Points;             // Path waypoints (source, reflections..., listener)
		TArray<FString> WallMaterials;      // Material at each reflection point
		float TotalDistance = 0.0f;         // Total path length in cm
		float AttenuationFactor = 1.0f;     // Combined attenuation 0-1
		int32 BounceCount = 0;
		bool bDirect = false;
	};

	/**
	 * Find sound paths using the image-source method.
	 * Direct path + first-order reflections off nearby surfaces.
	 * @param World              Editor world
	 * @param From               Sound source
	 * @param To                 Listener
	 * @param MaxBounces         Max reflection bounces (1-3)
	 * @param CandidateSurfaces  Number of nearby surfaces to test as reflectors
	 * @return Array of viable sound paths, sorted by attenuation (strongest first)
	 */
	TArray<FSoundPath> FindSoundPaths(UWorld* World, const FVector& From, const FVector& To,
		int32 MaxBounces = 2, int32 CandidateSurfaces = 16);

	// ========================================================================
	// Navmesh Indirect Path (doorway propagation)
	// ========================================================================

	/** Result of an indirect navmesh path check */
	struct FIndirectPathResult
	{
		bool bFound = false;                // Was a navmesh path found?
		bool bNavmeshAvailable = false;     // Is navmesh built at all?
		float PathDistance = 0.0f;           // Total navmesh path length in cm
		float AttenuationFactor = 0.0f;     // Distance-only attenuation (no wall occlusion)
		TArray<FVector> PathPoints;         // Navmesh path waypoints
		FString Note;                       // Diagnostic note (e.g. "navmesh not built")
	};

	/**
	 * Find an indirect sound path via navmesh (through doorways/openings).
	 * When direct line trace is blocked by walls, sound can still travel through
	 * open air paths (doorways, corridors) — the navmesh approximates these routes.
	 * Attenuation uses distance only (no wall occlusion — the path goes through open air).
	 *
	 * @param World   Editor world
	 * @param From    Sound source position
	 * @param To      Listener position
	 * @return Indirect path result (check bFound)
	 */
	FIndirectPathResult FindIndirectNavmeshPath(UWorld* World, const FVector& From, const FVector& To);

	// ========================================================================
	// Reverb Suggestion
	// ========================================================================

	/** Suggested reverb settings based on acoustic analysis */
	struct FReverbSuggestion
	{
		float Volume = 0.5f;        // 0-1
		float DecayTime = 1.0f;     // seconds
		float Density = 0.5f;       // 0-1
		float Diffusion = 0.5f;     // 0-1
		float AirAbsorptionHF = 0.99f;
		FString Classification;     // "dead", "dry", "live", "echo"
		FString Notes;
	};

	/** Suggest reverb settings from RT60 and material analysis */
	FReverbSuggestion SuggestReverbSettings(float RT60, const TMap<FString, float>& MaterialAreaFractions);
}
