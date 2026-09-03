// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExHeuristics.h"

#if WITH_EDITOR
#include "Core/PCGExHeuristicsFactoryProvider.h"
#include "Data/Registry/PCGDataTypeRegistry.h"
#include "Styling/AppStyle.h"
#endif

#define LOCTEXT_NAMESPACE "FPCGExHeuristicsModule"

void FPCGExHeuristicsModule::StartupModule()
{
	IPCGExLegacyModuleInterface::StartupModule();
}

void FPCGExHeuristicsModule::ShutdownModule()
{
	IPCGExLegacyModuleInterface::ShutdownModule();
}

#if WITH_EDITOR
void FPCGExHeuristicsModule::RegisterToEditor(const TSharedPtr<FSlateStyleSet>& InStyle)
{
	IPCGExModuleInterface::RegisterToEditor(InStyle);

	PCGEX_START_PCG_REGISTRATION
	PCGEX_REGISTER_DATA_TYPE(Heuristics, Heuristics)
}
#endif

#undef LOCTEXT_NAMESPACE

PCGEX_IMPLEMENT_MODULE(FPCGExHeuristicsModule, PCGExHeuristics)
