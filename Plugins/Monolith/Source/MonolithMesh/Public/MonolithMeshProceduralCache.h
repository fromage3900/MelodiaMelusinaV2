#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

/**
 * Procedural Mesh Cache — hash-based deduplication for procedural geometry.
 *
 * Each procedural mesh is fully determined by its input parameters (type, dimensions,
 * sub-params, seed). This class computes a deterministic MD5 hash from the canonical
 * parameter set, maps it to a saved StaticMesh asset path in a JSON manifest, and
 * provides auto-path generation for organized asset storage.
 *
 * Manifest location: Plugins/Monolith/Saved/Monolith/ProceduralCache/manifest.json
 * Auto-save paths:   /Game/Generated/{Category}/{Type}/SM_{Type}_{WxDxH}[_s{Seed}]_{Hash6}
 *
 * Thread safety: NOT thread-safe. All calls expected on the game thread (editor context).
 */
class FMonolithMeshProceduralCache
{
public:
	/** Singleton accessor */
	static FMonolithMeshProceduralCache& Get();

	/**
	 * Compute a deterministic MD5 hash from action name + generation params.
	 * Excludes transient fields (handle, save_path, location, etc.).
	 * Sorts keys recursively, normalizes floats to 2 decimal places.
	 * @return 32-char lowercase hex MD5 string.
	 */
	FString ComputeHash(const FString& ActionName, const TSharedPtr<FJsonObject>& Params);

	/**
	 * Look up a hash in the manifest and verify the asset still exists on disk.
	 * Removes stale entries automatically if the asset was deleted.
	 * @return true if cache hit (OutAssetPath is set), false if miss.
	 */
	bool TryGetCached(const FString& Hash, FString& OutAssetPath);

	/**
	 * Register a generated mesh in the cache manifest.
	 * Saves the manifest to disk immediately (atomic write).
	 */
	void Register(const FString& Hash, const FString& AssetPath, const FString& ActionName,
		const FString& Type, int32 TriangleCount, const TSharedPtr<FJsonObject>& Params);

	/**
	 * Generate an organized auto-save path for a procedural mesh.
	 * Format: /Game/Generated/{Category}/{Type}/SM_{Type}_{W}x{D}x{H}[_s{Seed}]_{Hash6}
	 * @param Seed Pass -1 to omit seed from the name.
	 */
	FString GenerateAutoPath(const FString& Category, const FString& Type,
		float Width, float Depth, float Height, const FString& Hash, int32 Seed = -1);

	// -- Cache management --

	/** Remove manifest entries whose assets no longer exist on disk. @return count removed. */
	int32 ValidateCache();

	/** Clear all entries, or filter by type (e.g. "chair"). @return count removed. */
	int32 ClearCache(const FString& TypeFilter = TEXT(""));

	/** Get cache stats: counts by type, total entries. */
	TSharedPtr<FJsonObject> GetStats();

	/** List manifest entries with optional type filter and limit. */
	TSharedPtr<FJsonObject> ListEntries(const FString& TypeFilter = TEXT(""), int32 Limit = 100);

private:
	FMonolithMeshProceduralCache() = default;

	void LoadManifest();
	void SaveManifest();

	/** Sorted canonical JSON serializer — recursive key sort, float normalization. */
	FString SortedJsonSerialize(const TSharedPtr<FJsonObject>& Obj);
	FString SortedArraySerialize(const TArray<TSharedPtr<FJsonValue>>& Arr);
	FString SerializeValue(const TSharedPtr<FJsonValue>& Val);

	FString GetManifestPath();
	FString GetCacheDirectory();

	/** Ensure manifest is loaded (lazy init). */
	void EnsureLoaded();

	/** The manifest JSON, loaded lazily. */
	TSharedPtr<FJsonObject> Manifest;
	bool bManifestLoaded = false;

	/** Keys excluded from hash computation (transient / presentation params). */
	static const TSet<FString> ExcludeKeys;
};
