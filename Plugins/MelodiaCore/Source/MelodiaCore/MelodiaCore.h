// MelodiaCore module ΓÇö public header.

#pragma once

#include "Modules/ModuleManager.h"

class FMelodiaCoreModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
