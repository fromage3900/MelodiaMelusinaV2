// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Selectors/PCGExMicroEntryPickerOperation.h"

#include "Data/PCGExData.h"

bool FPCGExMicroEntryPickerOperation::PrepareForData(FPCGExContext* InContext, const TSharedRef<PCGExData::FFacade>& InDataFacade)
{
	BindContext(InContext);
	PrimaryDataFacade = InDataFacade;
	return true;
}
