#pragma once

#include "Modules/ModuleInterface.h"

class FMonolithAudioModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
