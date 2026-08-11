// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExElementsMeta.h"


#if WITH_EDITOR
#include "Data/Registry/PCGDataTypeRegistry.h" // PCGEX_PCG_DATA_REGISTRY
#include "Elements/Partition/PCGExModularPartitionByValues.h"
#include "Styling/AppStyle.h"
#endif

#define LOCTEXT_NAMESPACE "FPCGExElementsMetaModule"

void FPCGExElementsMetaModule::StartupModule()
{
	IPCGExLegacyModuleInterface::StartupModule();
}

void FPCGExElementsMetaModule::ShutdownModule()
{
	IPCGExLegacyModuleInterface::ShutdownModule();
}

#if WITH_EDITOR
void FPCGExElementsMetaModule::RegisterToEditor(const TSharedPtr<FSlateStyleSet>& InStyle)
{
	IPCGExModuleInterface::RegisterToEditor(InStyle);

	PCGEX_START_PCG_REGISTRATION
	PCGEX_REGISTER_DATA_TYPE(PartitionRule, PartitionRule)

	// ActorDataPacker: UAssetDefinition in PCGExtendedToolkitEditor handles color/category
}
#endif

#undef LOCTEXT_NAMESPACE

PCGEX_IMPLEMENT_MODULE(FPCGExElementsMetaModule, PCGExElementsMeta)
