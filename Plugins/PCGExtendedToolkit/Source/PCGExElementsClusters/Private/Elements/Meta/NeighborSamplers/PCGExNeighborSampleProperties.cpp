// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Elements/Meta/NeighborSamplers/PCGExNeighborSampleProperties.h"

#define LOCTEXT_NAMESPACE "PCGExCreateNeighborSample"
#define PCGEX_NAMESPACE PCGExCreateNeighborSample

TSharedPtr<FPCGExNeighborSampleOperation> UPCGExNeighborSamplerFactoryProperties::CreateOperation(FPCGExContext* InContext) const
{
	return nullptr;
}

#undef LOCTEXT_NAMESPACE
#undef PCGEX_NAMESPACE
