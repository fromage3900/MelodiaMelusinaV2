#pragma once

#include "Modules/ModuleInterface.h"
#include "Templates/SharedPointer.h"

DECLARE_LOG_CATEGORY_EXTERN(LogProceduralModelingToolkit, Log, All);

class FProceduralModelingToolkitEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	void RegisterMenus();
	void UnregisterMenus();
	void RegisterTabSpawner();
	void UnregisterTabSpawner();
	void OpenToolkitTab();
	void ProcessSelectedStaticMeshes();

	TSharedRef<class SDockTab> SpawnToolkitTab(const class FSpawnTabArgs& Args);
};
