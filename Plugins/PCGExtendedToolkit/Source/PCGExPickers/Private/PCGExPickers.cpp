// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExPickers.h"

#if WITH_EDITOR
#include "Core/PCGExPickerFactoryProvider.h"
#include "Data/Registry/PCGDataTypeRegistry.h"
#include "Styling/AppStyle.h"
#endif

#define LOCTEXT_NAMESPACE "FPCGExPickersModule"

void FPCGExPickersModule::StartupModule()
{
	IPCGExLegacyModuleInterface::StartupModule();
}

void FPCGExPickersModule::ShutdownModule()
{
	IPCGExLegacyModuleInterface::ShutdownModule();
}

#if WITH_EDITOR
void FPCGExPickersModule::RegisterToEditor(const TSharedPtr<FSlateStyleSet>& InStyle)
{
	IPCGExModuleInterface::RegisterToEditor(InStyle);

	PCGEX_START_PCG_REGISTRATION
	PCGEX_REGISTER_DATA_TYPE(Picker, Picker)
}
#endif

#undef LOCTEXT_NAMESPACE

PCGEX_IMPLEMENT_MODULE(FPCGExPickersModule, PCGExPickers)
