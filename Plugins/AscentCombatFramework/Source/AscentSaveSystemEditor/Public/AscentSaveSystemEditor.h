// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Modules/ModuleManager.h"

/**
 * Editor module that integrates the Ascent Save System with the Level Editor.
 *
 * Responsibilities:
 *  - Adds a "PIE Save" combo-box to the Level Editor Play toolbar so the
 *    developer can choose whether the next Play In Editor session starts as a
 *    New Game or loads an existing save slot.
 *  - Hooks into PIE startup to load current-level save data once PIE is running.
 */
class FAscentSaveSystemEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	/** Registers the PIE Save combo-box into the Play toolbar. */
	void RegisterMenus();

	/** Loads current-level data after PIE has started so dynamic actors are restored. */
	void OnPostPIEStarted(bool bIsSimulating);
	FDelegateHandle PostPIEStartedHandle;
};
