// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExEntryPickerOperation.h"

#include "Data/PCGExData.h"

bool FPCGExEntryPickerOperation::PrepareForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade, PCGExAssetCollection::FCategory* InTarget, const UPCGExAssetCollection* InOwningCollection)
{
	BindContext(InContext);
	PrimaryDataFacade = InDataFacade;
	Target = InTarget;
	OwningCollection = InOwningCollection;
	// Reject null and empty up-front so the hot path (Pick) can assume Target is valid + non-empty.
	// Empty categories should never reach here in practice (FCache::RegisterEntry only creates
	// categories on first valid entry), but the assertion belongs at the boundary.
	return Target != nullptr && !Target->IsEmpty();
}
