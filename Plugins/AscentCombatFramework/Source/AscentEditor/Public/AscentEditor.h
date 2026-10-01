// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FToolBarBuilder;
class FMenuBuilder;

class FAscentEditorModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
	
	/** This function will be bound to Command. */
	void PluginButtonClicked();

	/**
	 * Gets the plugin name that contains this module.
	 * @return The name of the plugin
	 */
	static FString GetPluginName();

	/**
	 * Gets the plugin name that contains the specified module.
	 * @param ModuleName The name of the module to find the plugin for
	 * @return The name of the plugin that contains the module, or empty string if not found
	 */
	static FString GetPluginNameForModule(const FString& ModuleName);

	/**
	 * Gets the friendly name of the plugin that contains this module (from .uplugin FriendlyName).
	 * Use to distinguish ACF / ACF J / ACF Ultimate in editor widgets.
	 * @return The friendly name (e.g. "Ascent Combat Framework Ultimate") or plugin name if not found
	 */
	static FString GetPluginFriendlyName();

private:

	void RegisterMenus();

        TSharedPtr<class FUICommandList> PluginCommands;
};
