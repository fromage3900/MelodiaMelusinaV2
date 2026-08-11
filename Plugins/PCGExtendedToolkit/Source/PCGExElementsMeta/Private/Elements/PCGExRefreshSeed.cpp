// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Elements/PCGExRefreshSeed.h"


#include "Data/PCGExData.h"
#include "Data/PCGExPointIO.h"
#include "Helpers/PCGExRandomHelpers.h"


#define LOCTEXT_NAMESPACE "PCGExRefreshSeedElement"
#define PCGEX_NAMESPACE RefreshSeed

PCGExData::EIOInit UPCGExRefreshSeedSettings::GetMainDataInitializationPolicy() const
{
	return WantsDataStealing() ? PCGExData::EIOInit::Forward : PCGExData::EIOInit::Duplicate;
}

PCGEX_INITIALIZE_ELEMENT(RefreshSeed)
PCGEX_ELEMENT_BATCH_POINT_IMPL(RefreshSeed)

bool FPCGExRefreshSeedElement::AdvanceWork(FPCGExContext* InContext, const UPCGExSettings* InSettings) const
{
	TRACE_CPUPROFILER_EVENT_SCOPE(FPCGExRefreshSeedElement::Execute);

	PCGEX_CONTEXT_AND_SETTINGS(RefreshSeed)
	PCGEX_EXECUTION_CHECK
	PCGEX_ON_INITIAL_EXECUTION
	{
		if (!Context->StartBatchProcessingPoints(
			[&](const TSharedPtr<PCGExData::FPointIO>& Entry)
			{
				return true;
			},
			[&](const TSharedPtr<PCGExPointsMT::IBatch>& NewBatch)
			{
				NewBatch->bSkipCompletion = true;
			}))
		{
			return Context->CancelExecution(TEXT("Could not find any data to refresh seed on."));
		}
	}

	PCGEX_POINTS_BATCH_PROCESSING(PCGExCommon::States::State_Done)

	Context->MainPoints->StageOutputs();

	return Context->TryComplete();
}

namespace PCGExRefreshSeed
{
	bool FProcessor::Process(const TSharedPtr<PCGExMT::FTaskManager>& InTaskManager)
	{
		PointDataFacade->bSupportsScopedGet = Context->bScopedAttributeGet;

		if (!IProcessor::Process(InTaskManager))
		{
			return false;
		}

		PCGEX_INIT_IO(PointDataFacade->Source, Settings->GetMainDataInitializationPolicy())

		(void)PointDataFacade->GetOut()->GetSeedValueRange(true);

		StartParallelLoopForPoints();

		return true;
	}

	void FProcessor::ProcessPoints(const PCGExMT::FScope& Scope)
	{
		PointDataFacade->Fetch(Scope);
		FilterScope(Scope);

		TPCGValueRange<int32> Seeds = PointDataFacade->GetOut()->GetSeedValueRange(false);
		TConstPCGValueRange<FTransform> Transforms = PointDataFacade->GetOut()->GetConstTransformValueRange();

		const FVector BaseOffset = FVector(Settings->Base);
		PCGEX_SCOPE_LOOP(Index)
		{
			if (!PointFilterCache[Index])
			{
				continue;
			}
			Seeds[Index] = PCGExRandomHelpers::ComputeSpatialSeed(Transforms[Index].GetLocation(), BaseOffset);
		}
	}
}

#undef LOCTEXT_NAMESPACE
#undef PCGEX_NAMESPACE
