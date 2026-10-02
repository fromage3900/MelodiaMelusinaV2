// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FAscentMapsEditor : public IModuleInterface {
public:
    /** IModuleInterface implementation */
    void StartupModule() override;
    void ShutdownModule() override;

    /** This function will be bound to Command. */
    void PluginButtonClicked();

	/**
	 * Gets the plugin name that contains this module
	 * @return The name of the plugin
	 */
	static FString GetPluginName();

	/**
	 * Gets the plugin name that contains the specified module
	 * @param ModuleName - The name of the module to find the plugin for
	 * @return The name of the plugin that contains the module, or empty string if not found
	 */
	static FString GetPluginNameForModule(const FString& ModuleName);

private:
    void RegisterMenus();

	TSharedPtr<class FUICommandList> PluginCommands;
};
