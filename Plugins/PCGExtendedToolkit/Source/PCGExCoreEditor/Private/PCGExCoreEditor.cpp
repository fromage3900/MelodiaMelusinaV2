// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExCoreEditor.h"

#include "PCGExAssetTypesMacros.h"
#include "PropertyEditorDelegates.h"
#include "PropertyEditorModule.h"
#include "Details/PCGExDotComparisonCustomization.h"
#include "Details/PCGExNameFiltersCustomization.h"

#define LOCTEXT_NAMESPACE "FPCGExCoreEditorModule"

#undef LOCTEXT_NAMESPACE

PCGEX_IMPLEMENT_MODULE(FPCGExCoreEditorModule, PCGExCoreEditor)

void FPCGExCoreEditorModule::StartupModule()
{
	IPCGExEditorModuleInterface::StartupModule();

	PCGEX_REGISTER_CUSTO_START
	PCGEX_REGISTER_CUSTO("PCGExStaticDotComparisonDetails", FPCGExDotComparisonCustomization)
	PCGEX_REGISTER_CUSTO("PCGExDotComparisonDetails", FPCGExDotComparisonCustomization)
	PCGEX_REGISTER_CUSTO("PCGExNameFiltersDetails", FPCGExNameFiltersDetailsCustomization)
	PCGEX_REGISTER_CUSTO("PCGExAttributeGatherDetails", FPCGExNameFiltersDetailsCustomization)
	PCGEX_REGISTER_CUSTO("PCGExForwardDetails", FPCGExForwardDetailsCustomization)
}

void FPCGExCoreEditorModule::ShutdownModule()
{
	IPCGExEditorModuleInterface::ShutdownModule();
}
