#pragma once

#include "Modules/ModuleInterface.h"

class FMonolithGASModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
