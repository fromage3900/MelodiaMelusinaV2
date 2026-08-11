// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExSpatialDomains.h"

#include "NarrowPhase/PCGExNarrowPhase.h"
#include "NarrowPhase/PCGExNarrowPhaseRegistrations.h"

#define LOCTEXT_NAMESPACE "FPCGExSpatialDomainModule"

void FPCGExSpatialDomainsModule::StartupModule()
{
	IPCGExModuleInterface::StartupModule();

	// Register all built-in pair tests. Each entry-point lives next to its
	// pair-test implementations; new shape kinds add a Register*PairTests()
	// declaration to PCGExNarrowPhaseRegistrations.h and a call here.
	PCGExSpatial::NarrowPhase::RegisterOBBPairTests();
	PCGExSpatial::NarrowPhase::RegisterPolygonPairTests();
}

void FPCGExSpatialDomainsModule::ShutdownModule()
{
	// Hot-reload hygiene: drop registrations so a reloaded module starts
	// clean. Function pointers from a stale module would dangle otherwise.
	PCGExSpatial::NarrowPhase::UnregisterAll();

	IPCGExModuleInterface::ShutdownModule();
}

#if WITH_EDITOR
void FPCGExSpatialDomainsModule::RegisterToEditor(const TSharedPtr<FSlateStyleSet>& InStyle)
{
	IPCGExModuleInterface::RegisterToEditor(InStyle);
}
#endif

#undef LOCTEXT_NAMESPACE

PCGEX_IMPLEMENT_MODULE(FPCGExSpatialDomainsModule, PCGExSpatialDomains)
