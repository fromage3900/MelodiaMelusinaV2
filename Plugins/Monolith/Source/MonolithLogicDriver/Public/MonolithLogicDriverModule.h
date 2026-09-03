#pragma once

#include "Modules/ModuleInterface.h"

class FMonolithLogicDriverModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
