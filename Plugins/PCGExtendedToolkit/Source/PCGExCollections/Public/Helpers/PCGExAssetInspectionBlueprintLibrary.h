// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "UObject/SoftObjectPath.h"

#include "PCGExAssetInspectionBlueprintLibrary.generated.h"

class UMaterialInterface;
class UPCGExAssetCollection;
class UStaticMesh;

/**
 * Asset inspection helpers for collection tooling (staging pipelines, editor utility
 * widgets) -- the computed data reflection can't answer, e.g. mesh complexity stats.
 *
 * All functions are null-safe (0 / false / degenerate box) and LOD-clamped. Stats are
 * RenderData-based (UStaticMesh::GetNumTriangles etc.), so they work on loaded meshes in
 * any target that has render data; some engine accessors overlap BlueprintPure members on
 * UStaticMesh -- the value-add here is null-safety, clamping, and the non-exposed APIs
 * (material slot count, Nanite flag).
 */
UCLASS()
class PCGEXCOLLECTIONS_API UPCGExAssetInspectionBlueprintLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Number of LODs (0 when null or no render data). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshLODCount(const UStaticMesh* Mesh);

	/** Triangle count for the given LOD (clamped to the valid LOD range). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshTriCount(const UStaticMesh* Mesh, int32 LOD = 0);

	/** Vertex count for the given LOD (clamped to the valid LOD range). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshVertexCount(const UStaticMesh* Mesh, int32 LOD = 0);

	/** Number of material slots on the mesh. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshMaterialSlotCount(const UStaticMesh* Mesh);

	/** True when the mesh carries valid Nanite data. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static bool HasNaniteData(const UStaticMesh* Mesh);

	/** Triangle count of the mesh's Nanite representation (0 when not Nanite). Note that for
	 *  Nanite meshes, GetStaticMeshTriCount reports the FALLBACK mesh's LODs -- use this for
	 *  the real source density. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshNaniteTriCount(const UStaticMesh* Mesh);

	/** Vertex count of the mesh's Nanite representation (0 when not Nanite). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshNaniteVertexCount(const UStaticMesh* Mesh);

	/** The mesh's local bounding box (matches the conventions of entry Staging.Bounds). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static FBox GetStaticMeshBounds(const UStaticMesh* Mesh);

	/** Number of render sections (roughly: draw calls) for the given LOD. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshSectionCount(const UStaticMesh* Mesh, int32 LOD = 0);

	/** Screen size at which the given LOD becomes active (0 when unavailable). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static float GetStaticMeshLODScreenSize(const UStaticMesh* Mesh, int32 LOD = 0);

	/** Number of UV channels at the given LOD. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetStaticMeshUVChannelCount(const UStaticMesh* Mesh, int32 LOD = 0);

	/** True when LOD 0 carries a vertex color buffer. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static bool HasVertexColors(const UStaticMesh* Mesh);

	/** True when the mesh has distance field data built (LOD 0). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static bool HasDistanceField(const UStaticMesh* Mesh);

	/** All material slot names, in slot order. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static TArray<FName> GetStaticMeshMaterialSlotNames(const UStaticMesh* Mesh);

	/** Slot index for a material slot name; -1 when not found. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 FindStaticMeshMaterialSlotIndex(const UStaticMesh* Mesh, FName SlotName);

	/** Material assigned to the given slot (null when out of range). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static UMaterialInterface* GetStaticMeshMaterial(const UStaticMesh* Mesh, int32 SlotIndex);

	/** True when the mesh has at least one simple collision primitive. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static bool HasSimpleCollision(const UStaticMesh* Mesh);

	/** Number of simple collision primitives (boxes, spheres, capsules, convexes...). */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int32 GetCollisionPrimitiveCount(const UStaticMesh* Mesh);

	/** True when the mesh's collision is set to Use Complex as Simple. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static bool UsesComplexAsSimple(const UStaticMesh* Mesh);

	/** Estimated total memory footprint of any asset, in bytes. Works for meshes, textures,
	 *  data assets... the broadest single number for budget-driven pipelines. */
	UFUNCTION(BlueprintPure, Category = "PCGEx|Inspection")
	static int64 GetAssetResourceSizeBytes(UObject* Asset);

	/**
	 * Read an Asset Registry tag value WITHOUT loading the asset (e.g. "Triangles",
	 * "NaniteTriangles", "Materials", "ApproxSize" on static meshes). Orders of magnitude
	 * faster than load-based inspection for classifying large collections.
	 * Editor only: always false in cooked targets.
	 */
	UFUNCTION(BlueprintCallable, Category = "PCGEx|Inspection")
	static bool GetAssetRegistryTag(const FSoftObjectPath& AssetPath, FName TagName, FString& OutValue);

	/** Asset Registry tag for an entry's staged asset (Staging.Path), without loading it. */
	UFUNCTION(BlueprintCallable, Category = "PCGEx|Inspection")
	static bool GetEntryAssetRegistryTag(const UPCGExAssetCollection* Collection, int32 EntryIndex, FName TagName, FString& OutValue);
};
