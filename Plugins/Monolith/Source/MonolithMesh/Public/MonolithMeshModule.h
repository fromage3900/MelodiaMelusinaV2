#pragma once

#include "Modules/ModuleManager.h"

#if WITH_GEOMETRYSCRIPT
class UMonolithMeshHandlePool;
#endif

class FMonolithMeshModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
#if WITH_GEOMETRYSCRIPT
	UMonolithMeshHandlePool* HandlePool = nullptr;
#endif
};
