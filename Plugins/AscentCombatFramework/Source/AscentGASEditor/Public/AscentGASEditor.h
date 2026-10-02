// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

static const FString PluginName = "AscentCombatFramework";


class FAscentGASEditorModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;


private:

	TSharedPtr<FUICommandList> PluginCommands;

	void OnClicked();
};
