// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "Core/PCGExAssetCollection.h"

class UPCGExSelectorFactoryData;

namespace PCGExCollections
{
	/**
	 * Opaque base for collection-derived state that's invariant across facades.
	 * Each selector that benefits from sharing subclasses this with its specific cached arrays
	 * (e.g. per-entry volume/extents, per-entry resolved range bounds, sort orders, etc.).
	 *
	 * Instances are constructed by UPCGExSelectorFactoryData::BuildSharedData when a
	 * cache miss occurs. Once returned from the cache, instances are read-only; multiple
	 * ops read them concurrently without synchronization.
	 */
	class PCGEXCOLLECTIONS_API FSelectorSharedData : public TSharedFromThis<FSelectorSharedData>
	{
	public:
		virtual ~FSelectorSharedData() = default;
	};

	/**
	 * Context-scoped cache of FSelectorSharedData instances, keyed by (factory, category).
	 *
	 * Lifetime: owned by a consumer context (e.g. UPCGExStagingDistributeContext) alongside
	 * FPickPacker. Dies with the context -- no staleness across graph runs.
	 *
	 * Thread safety: GetOrBuild locks a critical section for the map insert. Shared data
	 * objects themselves are read-only after construction.
	 */
	class PCGEXCOLLECTIONS_API FSelectorSharedDataCache : public TSharedFromThis<FSelectorSharedDataCache>
	{
	public:
		/**
		 * Return cached shared data for (Factory, Target), building it lazily on first access.
		 * Returns null if the factory declines to produce shared data (its BuildSharedData returns null).
		 */
		TSharedPtr<FSelectorSharedData> GetOrBuild(
			const UPCGExSelectorFactoryData* Factory,
			const UPCGExAssetCollection* Collection,
			const PCGExAssetCollection::FCategory* Target);

#if WITH_EDITOR
		/** Test-only: number of BuildSharedData calls performed by this cache. */
		int32 GetBuildCount() const
		{
			return BuildCount;
		}
#endif

	private:
		using FKey = TPair<const UPCGExSelectorFactoryData*, const PCGExAssetCollection::FCategory*>;

		FCriticalSection Mutex;
		TMap<FKey, TSharedPtr<FSelectorSharedData>> Entries;

#if WITH_EDITOR
		int32 BuildCount = 0;
#endif
	};
}
