#pragma once

#include "CoreMinimal.h"

/**
 * Static data definitions for horror storytelling scene patterns.
 * Used by FMonolithMeshDecalActions::PlaceStorytellingScene.
 *
 * Each pattern defines placement rules for decals and props that
 * compose a recognizable horror vignette. Intensity (0-1) scales
 * counts, radii, and variation.
 */

/** A single element within a storytelling pattern */
struct FStorytellingElement
{
	/** Descriptive label for JSON output */
	FString Label;

	/** "decal" or "prop" */
	FString Type;

	/** Relative offset from scene center (scaled by intensity) */
	FVector RelativeOffset;

	/** Decal size (Depth, Width, Height) or prop scale */
	FVector Size;

	/** If true, offset is radial (distance from center, random angle) */
	bool bRadial = false;

	/** Radial distance range [min, max] in cm (used when bRadial) */
	float RadialMin = 0.0f;
	float RadialMax = 100.0f;

	/** Count range [min at intensity=0, max at intensity=1] */
	int32 CountMin = 1;
	int32 CountMax = 1;

	/** Random rotation range (degrees) */
	float RotationVariance = 360.0f;

	/** Scale variance (multiplied: 1.0 +/- this value) */
	float ScaleVariance = 0.1f;

	/** If true, this element should be placed on walls (horizontal trace outward) rather than floors (vertical trace down) */
	bool bWallElement = false;
};

/** A complete storytelling pattern */
struct FStorytellingPattern
{
	FString Name;
	FString Description;
	TArray<FStorytellingElement> Elements;
};

/**
 * Static pattern definitions.
 * These are intentionally generic — they place decals at computed positions.
 * Actual decal materials are chosen by the AI agent from the project's asset library.
 * The patterns define spatial relationships and density, not specific art assets.
 */
namespace StorytellingPatterns
{
	inline FStorytellingPattern GetViolencePattern()
	{
		FStorytellingPattern P;
		P.Name = TEXT("violence");
		P.Description = TEXT("Blood splatter radiating from a central impact point with scattered debris");
		P.Elements = {
			// Central blood pool
			{ TEXT("blood_pool_center"), TEXT("decal"), FVector(0, 0, 0), FVector(20, 120, 120),
			  false, 0, 0, 1, 1, 360.0f, 0.2f },
			// Radial blood splatters
			{ TEXT("blood_splatter"), TEXT("decal"), FVector::ZeroVector, FVector(15, 60, 60),
			  true, 80.0f, 250.0f, 2, 8, 360.0f, 0.3f },
			// Fine spray decals (further out)
			{ TEXT("blood_spray"), TEXT("decal"), FVector::ZeroVector, FVector(10, 30, 30),
			  true, 150.0f, 400.0f, 3, 12, 360.0f, 0.4f },
			// Impact marks on nearby surfaces
			{ TEXT("impact_mark"), TEXT("decal"), FVector::ZeroVector, FVector(10, 25, 25),
			  true, 50.0f, 200.0f, 1, 4, 360.0f, 0.15f },
		};
		return P;
	}

	inline FStorytellingPattern GetAbandonedInHastePattern()
	{
		FStorytellingPattern P;
		P.Name = TEXT("abandoned_in_haste");
		P.Description = TEXT("Scene of sudden departure — scattered personal items, open containers, dropped objects");
		P.Elements = {
			// Scuff marks (signs of rapid movement)
			{ TEXT("scuff_mark"), TEXT("decal"), FVector::ZeroVector, FVector(8, 40, 20),
			  true, 30.0f, 200.0f, 2, 6, 45.0f, 0.2f },
			// Spill stains (knocked-over drinks, chemicals)
			{ TEXT("spill_stain"), TEXT("decal"), FVector::ZeroVector, FVector(12, 80, 80),
			  true, 50.0f, 180.0f, 1, 3, 360.0f, 0.3f },
			// Dirt/dust disturbance
			{ TEXT("dust_disturbance"), TEXT("decal"), FVector::ZeroVector, FVector(10, 100, 60),
			  true, 0.0f, 250.0f, 1, 4, 360.0f, 0.2f },
		};
		return P;
	}

	inline FStorytellingPattern GetDraggedPattern()
	{
		FStorytellingPattern P;
		P.Name = TEXT("dragged");
		P.Description = TEXT("Linear drag trail with blood smears and disturbed floor markings");
		P.Elements = {
			// Central blood smear (elongated along a direction)
			{ TEXT("drag_smear_center"), TEXT("decal"), FVector(0, 0, 0), FVector(15, 200, 40),
			  false, 0, 0, 1, 1, 15.0f, 0.15f },
			// Handprint/grab marks along the trail
			{ TEXT("handprint"), TEXT("decal"), FVector::ZeroVector, FVector(10, 20, 25),
			  true, 20.0f, 60.0f, 2, 6, 30.0f, 0.1f },
			// Blood drips alongside
			{ TEXT("blood_drip"), TEXT("decal"), FVector::ZeroVector, FVector(8, 15, 15),
			  true, 30.0f, 80.0f, 3, 10, 360.0f, 0.3f },
			// Scratch/scuff marks
			{ TEXT("scratch_mark"), TEXT("decal"), FVector::ZeroVector, FVector(6, 60, 8),
			  true, 10.0f, 50.0f, 1, 4, 20.0f, 0.1f },
		};
		return P;
	}

	inline FStorytellingPattern GetMedicalEmergencyPattern()
	{
		FStorytellingPattern P;
		P.Name = TEXT("medical_emergency");
		P.Description = TEXT("Triage scene with fluid spills, staining, and medical waste indicators");
		P.Elements = {
			// Central fluid pool (larger, irregular)
			{ TEXT("fluid_pool"), TEXT("decal"), FVector(0, 0, 0), FVector(18, 150, 150),
			  false, 0, 0, 1, 1, 360.0f, 0.2f },
			// Smaller fluid stains (radiating)
			{ TEXT("fluid_stain"), TEXT("decal"), FVector::ZeroVector, FVector(12, 50, 50),
			  true, 60.0f, 200.0f, 2, 5, 360.0f, 0.3f },
			// Boot prints (through fluid)
			{ TEXT("boot_print"), TEXT("decal"), FVector::ZeroVector, FVector(8, 20, 30),
			  true, 80.0f, 300.0f, 2, 8, 30.0f, 0.1f },
			// Chemical/iodine stain
			{ TEXT("chemical_stain"), TEXT("decal"), FVector::ZeroVector, FVector(10, 40, 40),
			  true, 30.0f, 150.0f, 1, 3, 360.0f, 0.25f },
		};
		return P;
	}

	inline FStorytellingPattern GetCorruptionPattern()
	{
		FStorytellingPattern P;
		P.Name = TEXT("corruption");
		P.Description = TEXT("Organic corruption spreading from a focal point — dark growths, discoloration, creeping tendrils");
		P.Elements = {
			// Central corruption mass
			{ TEXT("corruption_core"), TEXT("decal"), FVector(0, 0, 0), FVector(25, 180, 180),
			  false, 0, 0, 1, 1, 360.0f, 0.15f },
			// Spreading tendrils (radial, elongated)
			{ TEXT("corruption_tendril"), TEXT("decal"), FVector::ZeroVector, FVector(15, 120, 30),
			  true, 50.0f, 300.0f, 3, 10, 360.0f, 0.2f },
			// Wall discoloration (higher on Z)
			{ TEXT("wall_discolor"), TEXT("decal"), FVector(0, 0, 80), FVector(20, 100, 100),
			  true, 30.0f, 200.0f, 1, 5, 360.0f, 0.3f, /*bWallElement=*/ true },
			// Small organic spots
			{ TEXT("organic_spot"), TEXT("decal"), FVector::ZeroVector, FVector(10, 25, 25),
			  true, 20.0f, 350.0f, 4, 15, 360.0f, 0.35f },
		};
		return P;
	}

	/** Get pattern by name. Returns nullptr if not found. */
	inline const FStorytellingPattern* GetPattern(const FString& Name)
	{
		// Static storage so we can return pointers
		static TMap<FString, FStorytellingPattern> Patterns;
		if (Patterns.Num() == 0)
		{
			auto Add = [&](FStorytellingPattern&& P) { Patterns.Add(P.Name, MoveTemp(P)); };
			Add(GetViolencePattern());
			Add(GetAbandonedInHastePattern());
			Add(GetDraggedPattern());
			Add(GetMedicalEmergencyPattern());
			Add(GetCorruptionPattern());
		}

		return Patterns.Find(Name);
	}

	/** Get all pattern names for error messages */
	inline FString GetPatternNames()
	{
		return TEXT("violence, abandoned_in_haste, dragged, medical_emergency, corruption");
	}
}
