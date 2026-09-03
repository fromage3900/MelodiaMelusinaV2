#include "MonolithMeshAcoustics.h"
#include "MonolithSettings.h"

#include "Engine/World.h"
#include "Engine/DataTable.h"
#include "CollisionQueryParams.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "PhysicsEngine/PhysicsSettings.h"
#include "NavigationSystem.h"
#include "NavigationData.h"

// ============================================================================
// Hardcoded acoustic defaults (calibrated from Steam Audio reference)
// ============================================================================

namespace
{
	struct FHardcodedSurface
	{
		const TCHAR* Name;
		EPhysicalSurface SurfaceType;
		float Absorption;
		float TransmissionLossdB;
		float FootstepLoudness;
	};

	// Maps to EPhysicalSurface enum values (SurfaceType1..SurfaceType62).
	// We use Default for unknown, and SurfaceType1-12 for the horror defaults.
	// When no DataTable exists, we match by SurfaceType enum value.
	static const FHardcodedSurface GDefaultSurfaces[] =
	{
		{ TEXT("Concrete"),     SurfaceType_Default,  0.02f, 40.0f, 0.6f  },
		{ TEXT("Metal"),        SurfaceType1,         0.03f, 35.0f, 0.8f  },
		{ TEXT("Tile"),         SurfaceType2,         0.02f, 38.0f, 0.5f  },
		{ TEXT("Carpet"),       SurfaceType3,         0.30f, 20.0f, 0.1f  },
		{ TEXT("Wood"),         SurfaceType4,         0.10f, 25.0f, 0.4f  },
		{ TEXT("Glass"),        SurfaceType5,         0.04f, 28.0f, 0.9f  },
		{ TEXT("Water"),        SurfaceType6,         0.01f, 10.0f, 0.2f  },
		{ TEXT("Dirt"),         SurfaceType7,         0.15f, 15.0f, 0.2f  },
		{ TEXT("Gravel"),       SurfaceType8,         0.25f, 15.0f, 0.7f  },
		{ TEXT("Fabric"),       SurfaceType9,         0.50f, 15.0f, 0.05f },
		{ TEXT("BrokenGlass"),  SurfaceType10,        0.05f, 30.0f, 1.0f  },
		{ TEXT("Flesh"),        SurfaceType11,        0.20f, 20.0f, 0.3f  },
	};

	static const int32 GNumDefaultSurfaces = UE_ARRAY_COUNT(GDefaultSurfaces);

	/** Try to load the DataTable from settings path */
	UDataTable* TryLoadAcousticsTable()
	{
		const FString& TablePath = GetDefault<UMonolithSettings>()->SurfaceAcousticsTablePath;
		if (TablePath.IsEmpty())
		{
			return nullptr;
		}
		return Cast<UDataTable>(StaticLoadObject(UDataTable::StaticClass(), nullptr, *TablePath));
	}

	/** Lookup by row name in the DataTable */
	bool TryGetFromTable(const FString& RowName, MonolithMeshAcoustics::FAcousticProperties& Out)
	{
		UDataTable* Table = TryLoadAcousticsTable();
		if (!Table)
		{
			return false;
		}

		const FAcousticSurfaceRow* Row =
			Table->FindRow<FAcousticSurfaceRow>(FName(*RowName), TEXT("MonolithAcoustics"));
		if (!Row)
		{
			return false;
		}

		Out.Absorption = Row->AbsorptionCoefficient;
		Out.TransmissionLossdB = Row->TransmissionLossdB;
		Out.FootstepLoudness = Row->FootstepLoudness;
		Out.SurfaceName = Row->DisplayName.IsEmpty() ? RowName : Row->DisplayName;
		return true;
	}

	/** Lookup surface type name from UPhysicsSettings */
	FString GetSurfaceTypeName(EPhysicalSurface SurfaceType)
	{
		const UPhysicsSettings* Settings = GetDefault<UPhysicsSettings>();
		for (const FPhysicalSurfaceName& Entry : Settings->PhysicalSurfaces)
		{
			if (Entry.Type == SurfaceType)
			{
				return Entry.Name.ToString();
			}
		}

		// Fallback: check hardcoded names
		for (int32 i = 0; i < GNumDefaultSurfaces; ++i)
		{
			if (GDefaultSurfaces[i].SurfaceType == SurfaceType)
			{
				return GDefaultSurfaces[i].Name;
			}
		}

		return TEXT("Default");
	}
}

// ============================================================================
// Surface property lookup
// ============================================================================

MonolithMeshAcoustics::FAcousticProperties MonolithMeshAcoustics::GetPropertiesForSurface(EPhysicalSurface SurfaceType)
{
	// Step 1: Get the name for this surface type
	FString Name = GetSurfaceTypeName(SurfaceType);

	// Step 2: Try DataTable lookup by name
	FAcousticProperties Props;
	if (TryGetFromTable(Name, Props))
	{
		return Props;
	}

	// Step 3: Hardcoded fallback by enum value
	for (int32 i = 0; i < GNumDefaultSurfaces; ++i)
	{
		if (GDefaultSurfaces[i].SurfaceType == SurfaceType)
		{
			Props.Absorption = GDefaultSurfaces[i].Absorption;
			Props.TransmissionLossdB = GDefaultSurfaces[i].TransmissionLossdB;
			Props.FootstepLoudness = GDefaultSurfaces[i].FootstepLoudness;
			Props.SurfaceName = GDefaultSurfaces[i].Name;
			return Props;
		}
	}

	// Unknown surface — return concrete defaults
	return GetDefaultProperties();
}

MonolithMeshAcoustics::FAcousticProperties MonolithMeshAcoustics::GetPropertiesForName(const FString& SurfaceName)
{
	// Try DataTable first
	FAcousticProperties Props;
	if (TryGetFromTable(SurfaceName, Props))
	{
		return Props;
	}

	// Hardcoded fallback by name
	for (int32 i = 0; i < GNumDefaultSurfaces; ++i)
	{
		if (SurfaceName.Equals(GDefaultSurfaces[i].Name, ESearchCase::IgnoreCase))
		{
			Props.Absorption = GDefaultSurfaces[i].Absorption;
			Props.TransmissionLossdB = GDefaultSurfaces[i].TransmissionLossdB;
			Props.FootstepLoudness = GDefaultSurfaces[i].FootstepLoudness;
			Props.SurfaceName = GDefaultSurfaces[i].Name;
			return Props;
		}
	}

	return GetDefaultProperties();
}

MonolithMeshAcoustics::FAcousticProperties MonolithMeshAcoustics::GetDefaultProperties()
{
	FAcousticProperties Props;
	Props.Absorption = 0.02f;
	Props.TransmissionLossdB = 40.0f;
	Props.FootstepLoudness = 0.6f;
	Props.SurfaceName = TEXT("Concrete");
	return Props;
}

TMap<FString, MonolithMeshAcoustics::FAcousticProperties> MonolithMeshAcoustics::GetHardcodedDefaults()
{
	TMap<FString, FAcousticProperties> Out;
	for (int32 i = 0; i < GNumDefaultSurfaces; ++i)
	{
		FAcousticProperties Props;
		Props.Absorption = GDefaultSurfaces[i].Absorption;
		Props.TransmissionLossdB = GDefaultSurfaces[i].TransmissionLossdB;
		Props.FootstepLoudness = GDefaultSurfaces[i].FootstepLoudness;
		Props.SurfaceName = GDefaultSurfaces[i].Name;
		Out.Add(GDefaultSurfaces[i].Name, Props);
	}
	return Out;
}

// ============================================================================
// Sabine RT60
// ============================================================================

const TCHAR* MonolithMeshAcoustics::AcousticTypeToString(ERoomAcousticType Type)
{
	switch (Type)
	{
	case ERoomAcousticType::Dead: return TEXT("dead");
	case ERoomAcousticType::Dry:  return TEXT("dry");
	case ERoomAcousticType::Live: return TEXT("live");
	case ERoomAcousticType::Echo: return TEXT("echo");
	default: return TEXT("unknown");
	}
}

float MonolithMeshAcoustics::ComputeSabineRT60(float VolumeM3, float TotalAbsorption)
{
	if (TotalAbsorption <= SMALL_NUMBER)
	{
		return 999.0f; // Fully reflective room — infinite reverb
	}
	return 0.161f * VolumeM3 / TotalAbsorption;
}

MonolithMeshAcoustics::ERoomAcousticType MonolithMeshAcoustics::ClassifyRT60(float RT60Seconds)
{
	if (RT60Seconds < 0.3f)  return ERoomAcousticType::Dead;
	if (RT60Seconds < 0.6f)  return ERoomAcousticType::Dry;
	if (RT60Seconds < 1.5f)  return ERoomAcousticType::Live;
	return ERoomAcousticType::Echo;
}

// ============================================================================
// Attenuation & Propagation
// ============================================================================

float MonolithMeshAcoustics::ComputeDistanceAttenuation(float Distance, float RefDist)
{
	if (Distance <= RefDist)
	{
		return 1.0f;
	}
	// Inverse square law
	return FMath::Clamp((RefDist * RefDist) / (Distance * Distance), 0.0f, 1.0f);
}

float MonolithMeshAcoustics::DbToLinear(float dB)
{
	// factor = 10^(-dB/20)
	return FMath::Pow(10.0f, -dB / 20.0f);
}

float MonolithMeshAcoustics::TraceOcclusion(UWorld* World, const FVector& From, const FVector& To,
	int32& OutWallCount, float& OutTotalLossdB)
{
	OutWallCount = 0;
	OutTotalLossdB = 0.0f;

	if (!World)
	{
		return 1.0f;
	}

	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithOcclusion), true);
	QueryParams.bReturnPhysicalMaterial = true;

	TArray<FHitResult> Hits;
	World->LineTraceMultiByChannel(Hits, From, To, ECC_Visibility, QueryParams);

	for (const FHitResult& Hit : Hits)
	{
		EPhysicalSurface Surface = SurfaceType_Default;
		if (Hit.PhysMaterial.IsValid())
		{
			Surface = Hit.PhysMaterial->SurfaceType;
		}

		FAcousticProperties Props = GetPropertiesForSurface(Surface);
		OutTotalLossdB += Props.TransmissionLossdB;
		OutWallCount++;
	}

	if (OutTotalLossdB <= 0.0f)
	{
		return 1.0f;
	}

	return DbToLinear(OutTotalLossdB);
}

// ============================================================================
// Image-Source Reflection
// ============================================================================

TArray<MonolithMeshAcoustics::FSoundPath> MonolithMeshAcoustics::FindSoundPaths(
	UWorld* World, const FVector& From, const FVector& To,
	int32 MaxBounces, int32 CandidateSurfaces)
{
	TArray<FSoundPath> Paths;
	if (!World)
	{
		return Paths;
	}

	MaxBounces = FMath::Clamp(MaxBounces, 0, 3);
	CandidateSurfaces = FMath::Clamp(CandidateSurfaces, 4, 64);

	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(MonolithSoundPath), true);
	QueryParams.bReturnPhysicalMaterial = true;

	// === Direct path ===
	{
		FSoundPath DirectPath;
		DirectPath.Points.Add(From);
		DirectPath.Points.Add(To);
		DirectPath.TotalDistance = FVector::Dist(From, To);
		DirectPath.bDirect = true;
		DirectPath.BounceCount = 0;

		// Check for occlusion on direct path
		int32 WallCount;
		float LossdB;
		float OcclusionFactor = TraceOcclusion(World, From, To, WallCount, LossdB);
		float DistAtten = ComputeDistanceAttenuation(DirectPath.TotalDistance);
		DirectPath.AttenuationFactor = DistAtten * OcclusionFactor;

		Paths.Add(MoveTemp(DirectPath));
	}

	if (MaxBounces == 0)
	{
		return Paths;
	}

	// === Find candidate reflection surfaces via radial sweep from midpoint ===
	struct FReflectionCandidate
	{
		FVector Point;
		FVector Normal;
		FString Material;
	};

	TArray<FReflectionCandidate> Candidates;
	const FVector Midpoint = (From + To) * 0.5f;
	const float SearchRadius = FVector::Dist(From, To) * 1.5f;

	// Sweep rays in a hemisphere around the source-to-listener axis
	const int32 AzimuthalRays = FMath::Min(CandidateSurfaces, 32);
	const int32 ElevationSteps = FMath::Max(CandidateSurfaces / AzimuthalRays, 1);

	for (int32 Elev = 0; Elev < ElevationSteps; ++Elev)
	{
		const float Phi = (ElevationSteps == 1) ? 0.0f
			: FMath::DegreesToRadians(-45.0f + 90.0f * Elev / (ElevationSteps - 1));

		for (int32 Az = 0; Az < AzimuthalRays; ++Az)
		{
			const float Theta = FMath::DegreesToRadians(360.0f * Az / AzimuthalRays);
			FVector Dir(
				FMath::Cos(Phi) * FMath::Cos(Theta),
				FMath::Cos(Phi) * FMath::Sin(Theta),
				FMath::Sin(Phi)
			);

			FHitResult Hit;
			if (World->LineTraceSingleByChannel(Hit, Midpoint, Midpoint + Dir * SearchRadius, ECC_Visibility, QueryParams))
			{
				FReflectionCandidate Cand;
				Cand.Point = Hit.ImpactPoint;
				Cand.Normal = Hit.ImpactNormal;
				Cand.Material = TEXT("Default");

				if (Hit.PhysMaterial.IsValid())
				{
					Cand.Material = GetSurfaceTypeName(Hit.PhysMaterial->SurfaceType);
				}

				Candidates.Add(MoveTemp(Cand));
			}
		}
	}

	// === First-order reflections ===
	for (const FReflectionCandidate& Cand : Candidates)
	{
		// Check: can sound reach the reflection point from source?
		FHitResult HitToReflector;
		bool bSourceToReflector = !World->LineTraceSingleByChannel(
			HitToReflector, From, Cand.Point, ECC_Visibility, QueryParams)
			|| FVector::DistSquared(HitToReflector.ImpactPoint, Cand.Point) < 100.0f;

		if (!bSourceToReflector) continue;

		// Reflect direction
		FVector InDir = (Cand.Point - From).GetSafeNormal();
		FVector Reflected = InDir - 2.0f * FVector::DotProduct(InDir, Cand.Normal) * Cand.Normal;

		// Check: does reflected ray reach near the listener?
		FHitResult HitFromReflector;
		FVector ReflectedEnd = Cand.Point + Reflected * SearchRadius;
		World->LineTraceSingleByChannel(HitFromReflector, Cand.Point + Cand.Normal * 1.0f, To, ECC_Visibility, QueryParams);

		// Accept if reflected path gets close enough to the listener (within 10% of total distance)
		float DistToListener = FVector::Dist(Cand.Point, To);
		bool bReachesListener = !HitFromReflector.bBlockingHit
			|| FVector::DistSquared(HitFromReflector.ImpactPoint, To) < FMath::Square(DistToListener * 0.1f + 50.0f);

		if (!bReachesListener) continue;

		float Leg1 = FVector::Dist(From, Cand.Point);
		float Leg2 = FVector::Dist(Cand.Point, To);
		float TotalDist = Leg1 + Leg2;

		// Attenuation: distance + reflection loss (~3dB per bounce on hard surfaces)
		FAcousticProperties SurfProps = GetPropertiesForName(Cand.Material);
		float ReflectionLoss = 1.0f - SurfProps.Absorption; // Energy retained after reflection
		float Atten = ComputeDistanceAttenuation(TotalDist) * ReflectionLoss;

		FSoundPath Path;
		Path.Points.Add(From);
		Path.Points.Add(Cand.Point);
		Path.Points.Add(To);
		Path.WallMaterials.Add(Cand.Material);
		Path.TotalDistance = TotalDist;
		Path.AttenuationFactor = Atten;
		Path.BounceCount = 1;
		Path.bDirect = false;
		Paths.Add(MoveTemp(Path));
	}

	// Sort by attenuation factor (strongest first)
	Paths.Sort([](const FSoundPath& A, const FSoundPath& B)
	{
		return A.AttenuationFactor > B.AttenuationFactor;
	});

	return Paths;
}

// ============================================================================
// Reverb Suggestion
// ============================================================================

MonolithMeshAcoustics::FReverbSuggestion MonolithMeshAcoustics::SuggestReverbSettings(
	float RT60, const TMap<FString, float>& MaterialAreaFractions)
{
	FReverbSuggestion Suggestion;
	ERoomAcousticType Type = ClassifyRT60(RT60);
	Suggestion.Classification = AcousticTypeToString(Type);
	Suggestion.DecayTime = RT60;

	switch (Type)
	{
	case ERoomAcousticType::Dead:
		Suggestion.Volume = 0.15f;
		Suggestion.Density = 0.2f;
		Suggestion.Diffusion = 0.3f;
		Suggestion.AirAbsorptionHF = 0.995f;
		Suggestion.Notes = TEXT("Very absorptive room. Minimal reverb. Good for dialogue clarity.");
		break;

	case ERoomAcousticType::Dry:
		Suggestion.Volume = 0.35f;
		Suggestion.Density = 0.4f;
		Suggestion.Diffusion = 0.5f;
		Suggestion.AirAbsorptionHF = 0.99f;
		Suggestion.Notes = TEXT("Moderately absorptive. Short reverb tail. Natural indoor sound.");
		break;

	case ERoomAcousticType::Live:
		Suggestion.Volume = 0.55f;
		Suggestion.Density = 0.6f;
		Suggestion.Diffusion = 0.7f;
		Suggestion.AirAbsorptionHF = 0.985f;
		Suggestion.Notes = TEXT("Reflective surfaces. Noticeable reverb. Good for horror atmosphere.");
		break;

	case ERoomAcousticType::Echo:
		Suggestion.Volume = 0.75f;
		Suggestion.Density = 0.8f;
		Suggestion.Diffusion = 0.85f;
		Suggestion.AirAbsorptionHF = 0.98f;
		Suggestion.Notes = TEXT("Highly reflective. Long reverb tail. Sounds carry far — horror amplifier.");
		break;
	}

	// Adjust based on dominant material
	float MaxFraction = 0.0f;
	FString DominantMaterial;
	for (const auto& Pair : MaterialAreaFractions)
	{
		if (Pair.Value > MaxFraction)
		{
			MaxFraction = Pair.Value;
			DominantMaterial = Pair.Key;
		}
	}

	if (DominantMaterial.Equals(TEXT("Metal"), ESearchCase::IgnoreCase))
	{
		Suggestion.Diffusion = FMath::Min(Suggestion.Diffusion + 0.15f, 1.0f);
		Suggestion.Notes += TEXT(" Metal-dominant: boosted diffusion for metallic shimmer.");
	}
	else if (DominantMaterial.Equals(TEXT("Carpet"), ESearchCase::IgnoreCase)
		|| DominantMaterial.Equals(TEXT("Fabric"), ESearchCase::IgnoreCase))
	{
		Suggestion.AirAbsorptionHF = FMath::Min(Suggestion.AirAbsorptionHF + 0.005f, 1.0f);
		Suggestion.Notes += TEXT(" Soft-dominant: increased HF absorption for muffled quality.");
	}
	else if (DominantMaterial.Equals(TEXT("Tile"), ESearchCase::IgnoreCase)
		|| DominantMaterial.Equals(TEXT("Concrete"), ESearchCase::IgnoreCase))
	{
		Suggestion.Density = FMath::Min(Suggestion.Density + 0.1f, 1.0f);
		Suggestion.Notes += TEXT(" Hard-surface dominant: boosted density for cold, clinical feel.");
	}

	return Suggestion;
}

// ============================================================================
// Navmesh Indirect Path (doorway propagation)
// ============================================================================

MonolithMeshAcoustics::FIndirectPathResult MonolithMeshAcoustics::FindIndirectNavmeshPath(
	UWorld* World, const FVector& From, const FVector& To)
{
	FIndirectPathResult Result;

	if (!World)
	{
		Result.Note = TEXT("No world available");
		return Result;
	}

	UNavigationSystemV1* NavSys = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!NavSys)
	{
		Result.Note = TEXT("Navigation system not available");
		return Result;
	}

	ANavigationData* NavData = NavSys->GetDefaultNavDataInstance(FNavigationSystem::DontCreate);
	if (!NavData)
	{
		Result.Note = TEXT("Navmesh not built — indirect path check skipped");
		return Result;
	}

	Result.bNavmeshAvailable = true;

	// Use default agent properties
	FNavAgentProperties AgentProps;
	AgentProps.AgentRadius = 42.0f;
	AgentProps.AgentHeight = 192.0f;

	FPathFindingQuery Query(nullptr, *NavData, From, To);
	Query.SetAllowPartialPaths(false); // We need a complete path to be useful

	FPathFindingResult PathResult = NavSys->FindPathSync(AgentProps, Query);

	if (!PathResult.IsSuccessful() || !PathResult.Path.IsValid() || PathResult.Path->IsPartial())
	{
		Result.Note = TEXT("No complete navmesh path between points");
		return Result;
	}

	const TArray<FNavPathPoint>& NavPoints = PathResult.Path->GetPathPoints();
	if (NavPoints.Num() < 2)
	{
		Result.Note = TEXT("Degenerate navmesh path");
		return Result;
	}

	// Compute total path distance
	float TotalDist = 0.0f;
	for (int32 i = 1; i < NavPoints.Num(); ++i)
	{
		TotalDist += FVector::Dist(NavPoints[i - 1].Location, NavPoints[i].Location);
		Result.PathPoints.Add(NavPoints[i - 1].Location);
	}
	Result.PathPoints.Add(NavPoints.Last().Location);
	Result.PathDistance = TotalDist;

	// Distance-only attenuation (no wall occlusion — sound travels through open air)
	Result.AttenuationFactor = ComputeDistanceAttenuation(TotalDist);
	Result.bFound = true;

	return Result;
}
