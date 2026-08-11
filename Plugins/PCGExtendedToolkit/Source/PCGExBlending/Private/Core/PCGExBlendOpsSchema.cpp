// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Core/PCGExBlendOpsSchema.h"

#include "Core/PCGExContext.h"
#include "Data/PCGExData.h"
#include "Data/Utils/PCGExDataPreloader.h"

namespace PCGExBlending
{
	bool FBlendOpsSchema::Init(
		FPCGExContext* InContext,
		const TArray<TObjectPtr<const UPCGExBlendOpFactory>>& InFactories,
		const TArray<TSharedRef<PCGExData::FFacade>>& InSources)
	{
		// Mirrors FBlendOpsManager::Init phase 1: explicit (non-monolithic) op output names
		// supersede the matching monolithic-resolved ops.
		TSet<FName> SupersedeNames;
		for (const TObjectPtr<const UPCGExBlendOpFactory>& Factory : InFactories)
		{
			if (Factory->IsMonolithic())
			{
				continue;
			}
			const FName OutputName = UPCGExBlendOpFactory::GetOutputTargetName(Factory->Config);
			if (!OutputName.IsNone())
			{
				SupersedeNames.Add(OutputName);
			}
		}

		EntriesPerSource.Reserve(InSources.Num());

		for (const TSharedRef<PCGExData::FFacade>& Source : InSources)
		{
			TArray<FBlendOpsSchemaEntry>& Entries = EntriesPerSource.Add(Source->GetIn());

			for (const TObjectPtr<const UPCGExBlendOpFactory>& Factory : InFactories)
			{
				TArray<FPCGExAttributeBlendConfig> Configs;
				if (!Factory->ResolveConfigs(InContext, Source, Configs, &SupersedeNames))
				{
					PCGE_LOG_C(Error, GraphAndLog, InContext, FTEXT("A blend op factory failed to resolve its configs."));
					return false;
				}

				const bool bSoftFail = Factory->IsMonolithic();

				Entries.Reserve(Entries.Num() + Configs.Num());
				for (FPCGExAttributeBlendConfig& Config : Configs)
				{
					FBlendOpsSchemaEntry& Entry = Entries.Emplace_GetRef();
					Entry.Factory = Factory;
					Entry.Config = MoveTemp(Config);
					Entry.bSoftFail = bSoftFail;
				}
			}
		}

		return true;
	}

	const TArray<FBlendOpsSchemaEntry>* FBlendOpsSchema::GetEntries(const UPCGData* InSourceData) const
	{
		return EntriesPerSource.Find(InSourceData);
	}

	void FBlendOpsSchema::RegisterBuffersDependencies(FPCGExContext* InContext, PCGExData::FFacadePreloader& FacadePreloader) const
	{
		const TSharedPtr<PCGExData::FFacade> Facade = FacadePreloader.GetDataFacade();
		if (!Facade)
		{
			return;
		}

		const TArray<FBlendOpsSchemaEntry>* Entries = EntriesPerSource.Find(Facade->GetIn());
		if (!Entries)
		{
			return;
		}

		// Register OperandA reads only: in multi-source blending OperandB and outputs resolve
		// against the per-processor target data, not the preloaded source. TryRegister is a
		// no-op for non-attribute selectors (point properties read straight from native ranges).
		for (const FBlendOpsSchemaEntry& Entry : *Entries)
		{
			FacadePreloader.TryRegister(InContext, Entry.Config.OperandA);
		}
	}
}
