#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

class FMonolithIndexDatabase;
class FSQLiteDatabase;

/**
 * Static helpers for mesh catalog SQL operations.
 * The mesh_catalog table is created and populated by MeshCatalogIndexer;
 * this class provides query wrappers used by inspection actions.
 */
class FMonolithMeshCatalog
{
public:
	/** Ensure the mesh_catalog table and indices exist */
	static bool CreateTable(FSQLiteDatabase& DB);

	/** Insert or replace a mesh catalog entry */
	static bool InsertEntry(
		FSQLiteDatabase& DB,
		const FString& AssetPath,
		float BoundsX, float BoundsY, float BoundsZ,
		float BoundsMin, float BoundsMid, float BoundsMax,
		float Volume,
		const FString& SizeClass,
		const FString& Category,
		int32 TriCount,
		bool bHasCollision,
		int32 LodCount,
		float PivotOffsetZ,
		bool bDegenerate);

	/** Search meshes by sorted dimension range */
	static TSharedPtr<FJsonObject> SearchBySize(
		FSQLiteDatabase& DB,
		const TArray<float>& MinBounds,
		const TArray<float>& MaxBounds,
		const FString& Category,
		const FString& ExcludeSizeClass,
		int32 Limit);

	/** Get aggregate statistics from the catalog */
	static TSharedPtr<FJsonObject> GetStats(FSQLiteDatabase& DB);

	/** Classify bounds into a size class: tiny, small, medium, large, huge */
	static FString ClassifySizeClass(float BoundsMax);

	/** Infer a category from the asset's folder path */
	static FString InferCategory(const FString& AssetPath);
};
