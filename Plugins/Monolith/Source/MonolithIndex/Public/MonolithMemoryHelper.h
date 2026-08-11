#pragma once

#include "CoreMinimal.h"
#include "HAL/PlatformMemory.h"

DECLARE_LOG_CATEGORY_EXTERN(LogMonolithMemory, Log, All);

/**
 * Helper utilities for memory management during indexing.
 * Provides memory monitoring, garbage collection, and package unloading.
 */
struct MONOLITHINDEX_API FMonolithMemoryHelper
{
	/**
	 * Get the current process memory usage in megabytes.
	 * Uses physical memory (working set) for accurate pressure detection.
	 */
	static SIZE_T GetCurrentMemoryUsageMB();

	/**
	 * Get available physical memory in megabytes.
	 */
	static SIZE_T GetAvailableMemoryMB();

	/**
	 * Check if memory usage exceeds the given budget and throttling is needed.
	 * @param BudgetMB Maximum memory budget in megabytes
	 * @return true if current usage exceeds budget and we should throttle
	 */
	static bool ShouldThrottle(SIZE_T BudgetMB);

	/**
	 * Force garbage collection to free unreferenced objects.
	 * @param bFullPurge If true, performs a full purge including package unloading.
	 *                   If false, performs incremental GC which is faster but less thorough.
	 */
	static void ForceGarbageCollection(bool bFullPurge = false);

	/**
	 * Attempt to unload the package containing the given asset.
	 * Marks the package for GC - actual unload happens on next GC cycle.
	 * @param Asset The asset whose package should be unloaded
	 * @return true if the package was successfully marked for unload
	 */
	static bool TryUnloadPackage(UObject* Asset);

	/**
	 * Yield to the editor to allow UI updates and prevent freezing.
	 * Pumps Slate messages and allows the editor to process input.
	 * Safe to call from game thread only.
	 */
	static void YieldToEditor();

	/**
	 * Log current memory statistics at the given log verbosity.
	 * @param Context Description of when this log is being made (e.g., "after batch 10")
	 */
	static void LogMemoryStats(const FString& Context);

	/**
	 * Check if we're running low on memory (below 2GB available).
	 * This is a critical threshold that may cause system instability.
	 */
	static bool IsMemoryCritical();

	// ---- RAM tier auto-detect (v0.13.0) ----

	/**
	 * Get installed physical RAM in whole gigabytes. Used to auto-detect the
	 * memory-budget tier for low-spec machines.
	 */
	static int32 GetInstalledRamGB();

	/**
	 * Returns the memory budget in MB, resolving the auto-detect sentinel (0)
	 * via an RAM-based tier:
	 *   64+ GB -> 32768 MB    32+ GB -> 16384 MB
	 *   16+ GB -> 6144 MB     <16 GB -> 3072 MB
	 * Override via Project Settings > Monolith > Indexing > Performance.
	 */
	static int32 GetResolvedMemoryBudgetMB();

	/**
	 * Returns the deep-index batch size, resolving the auto-detect sentinel (0)
	 * via an RAM-based tier (32+ GB -> 8, 16 GB -> 4, <16 -> 2).
	 */
	static int32 GetResolvedDeepIndexBatchSize();

	/**
	 * Returns the post-pass batch size, resolving the auto-detect sentinel (0)
	 * via an RAM-based tier (32+ GB -> 4, 16 GB -> 2, <16 -> 1).
	 */
	static int32 GetResolvedPostPassBatchSize();

	/**
	 * Log the resolved tier info once per editor session. Subsequent calls are no-ops.
	 */
	static void LogTierStartupOnce();
};
