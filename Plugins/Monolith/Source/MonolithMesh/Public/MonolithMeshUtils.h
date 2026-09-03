#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "CollisionShape.h"
#include "CollisionQueryParams.h"

class UStaticMesh;
class USkeletalMesh;
class AActor;
class UWorld;

namespace MonolithMeshUtils
{
	/** Load and validate a StaticMesh from asset path */
	UStaticMesh* LoadStaticMesh(const FString& Path, FString& OutError);

	/** Load and validate a SkeletalMesh from asset path */
	USkeletalMesh* LoadSkeletalMesh(const FString& Path, FString& OutError);

	/** Parse a location vector from JSON params (array of 3 floats or {x,y,z} object) */
	bool ParseVector(const TSharedPtr<FJsonObject>& Params, const FString& Key, FVector& Out);

	/** Parse a rotator from JSON params (array of 3 floats or {pitch,yaw,roll} object) */
	bool ParseRotator(const TSharedPtr<FJsonObject>& Params, const FString& Key, FRotator& Out);

	/** Find an actor by name in the current editor world (checks label first, then internal name) */
	AActor* FindActorByName(const FString& Name, FString& OutError);

	/** Get the current editor world */
	UWorld* GetEditorWorld();

	/** Parsed blockout tags from an actor's tag array */
	struct FBlockoutTags
	{
		FString RoomType;
		TArray<FString> Tags;
		FString Density;
		bool bAllowPhysics = false;
		float FloorHeight = 0.0f;
		bool bHasWalls = false;
		bool bHasCeiling = false;
	};

	/** Parse blockout tags from an actor's tag array */
	FBlockoutTags ParseBlockoutTags(const AActor* Actor);

	/** Build a JSON object from FBoxSphereBounds */
	TSharedPtr<FJsonObject> BoundsToJson(const FBoxSphereBounds& Bounds);

	/** Build a JSON object from an FTransform */
	TSharedPtr<FJsonObject> TransformToJson(const FTransform& Transform);

	/** Case-insensitive FName tag matching (handles FName case folding) */
	bool MatchTag(const FName& A, const FName& B);

	// ========================================================================
	// Collision Validation Utilities (for scatter/prop placement)
	// ========================================================================

	/** Result of a prop placement validation check */
	struct FPropPlacementResult
	{
		bool bValid = false;
		FVector FinalLocation = FVector::ZeroVector;
		FString RejectReason;
		TArray<FString> Warnings;
	};

	/**
	 * Validate whether a prop fits at a candidate location without overlapping world geometry.
	 * Optionally attempts iterative push-out using ComputePenetration (MTD) to salvage
	 * near-miss placements.
	 *
	 * @param World                Editor world to query against
	 * @param CandidateLocation    Proposed center of the prop's bounding box
	 * @param CandidateRotation    Orientation of the prop (OBB query, not AABB)
	 * @param PropHalfExtent       Half-extent of the prop's bounding box (already scaled + shrunk)
	 * @param IgnoreActors         Actors to exclude from overlap checks (e.g., the blockout volume, other scattered props)
	 * @param bAllowPushOut        If true, attempt iterative MTD push-out on overlap
	 * @param MaxPushOutDistance   Maximum total push distance in cm before rejecting (default 50)
	 * @return FPropPlacementResult with bValid, FinalLocation, and any warnings/reject reason
	 */
	FPropPlacementResult ValidatePropPlacement(
		UWorld* World,
		const FVector& CandidateLocation,
		const FQuat& CandidateRotation,
		const FVector& PropHalfExtent,
		const TArray<AActor*>& IgnoreActors,
		bool bAllowPushOut = true,
		float MaxPushOutDistance = 50.0f);

	/**
	 * Attempt to push a prop out of overlapping geometry using iterative MTD resolution.
	 * Called internally by ValidatePropPlacement when bAllowPushOut is true.
	 *
	 * @param World             Editor world
	 * @param InOutLocation     Location to adjust (modified in place on success)
	 * @param Rotation          Prop orientation
	 * @param PropHalfExtent    Half-extent of prop bounding box
	 * @param QueryParams       Collision query params (with ignore actors set)
	 * @param MaxPushDistance    Maximum total push budget in cm
	 * @param MaxIterations     Maximum push-out iterations (default 3)
	 * @return true if the prop was successfully pushed clear of all overlaps
	 */
	bool TryPushOutProp(
		UWorld* World,
		FVector& InOutLocation,
		const FQuat& Rotation,
		const FVector& PropHalfExtent,
		const FCollisionQueryParams& QueryParams,
		float MaxPushDistance,
		int32 MaxIterations = 3);

	/**
	 * Create a collision box shape from a static mesh's bounds, applying scale and a 0.9x
	 * shrink factor to avoid false positives from axis-aligned bounding box overestimation.
	 *
	 * @param Mesh   Source static mesh (must be valid)
	 * @param Scale  World scale to apply to mesh extents
	 * @return FCollisionShape box suitable for overlap/sweep queries
	 */
	FCollisionShape MakeCollisionShapeFromMesh(UStaticMesh* Mesh, const FVector& Scale);
}
