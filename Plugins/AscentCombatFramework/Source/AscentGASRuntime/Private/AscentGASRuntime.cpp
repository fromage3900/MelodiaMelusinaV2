// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "AscentGASRuntime.h"
#include "Logging.h"

#include "Modules/ModuleManager.h"

#define LOCTEXT_NAMESPACE "FAscentGASRuntime"

void FAscentGASRuntime::StartupModule()
{
}

void FAscentGASRuntime::ShutdownModule()
{
	
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FAscentGASRuntime, AscentGASRuntime);