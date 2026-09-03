// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#pragma once

#include "CoreMinimal.h"
#include "PCGExBlendOpFactory.h"

struct FPCGExContext;

namespace PCGExData
{
	class FFacade;
	class FFacadePreloader;
}

namespace PCGExBlending
{
	struct FBlendOpsSchemaEntry
	{
		TObjectPtr<const UPCGExBlendOpFactory> Factory;
		FPCGExAttributeBlendConfig Config;

		// Resolved from a monolithic factory: PrepareForData failures skip the op
		// (the attribute may be absent or type-mismatched on a given target)
		// instead of failing the whole blender init.
		bool bSoftFail = false;
	};

	/**
	 * Pre-resolved blend operation configs for a fixed set of factories x source facades.
	 *
	 * Monolithic factories resolve their configs from source metadata; doing so per-processor
	 * at batch time means concurrent metadata enumeration and cold attribute reads on shared
	 * facades. Resolve once instead -- single-threaded, e.g. during Boot -- and share const
	 * across processors: per-processor blender init then only instantiates operations.
	 * The schema also drives preloader registration, so the warmed buffer set exactly matches
	 * what the operations will read.
	 */
	class PCGEXBLENDING_API FBlendOpsSchema : public TSharedFromThis<FBlendOpsSchema>
	{
	public:
		bool Init(
			FPCGExContext* InContext,
			const TArray<TObjectPtr<const UPCGExBlendOpFactory>>& InFactories,
			const TArray<TSharedRef<PCGExData::FFacade>>& InSources);

		/** Resolved entries for a source, keyed by its In data. Null if the data wasn't part of Init. */
		const TArray<FBlendOpsSchemaEntry>* GetEntries(const UPCGData* InSourceData) const;

		/** Registers the resolved OperandA reads with the preloader of a matching source facade. */
		void RegisterBuffersDependencies(FPCGExContext* InContext, PCGExData::FFacadePreloader& FacadePreloader) const;

		bool IsEmpty() const
		{
			return EntriesPerSource.IsEmpty();
		}

	protected:
		TMap<const UPCGData*, TArray<FBlendOpsSchemaEntry>> EntriesPerSource;
	};
}
