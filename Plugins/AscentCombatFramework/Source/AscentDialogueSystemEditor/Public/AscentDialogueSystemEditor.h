// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 


#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FExtender;
class FMenuBuilder;
struct FAssetData;
class UADSDialogue;

class FAscentDialogueSystemEditorModule : public IModuleInterface
{
public:

	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	/** Adds batch generation entries to the Content Browser context menu for selected Dialogue assets. */
	TSharedRef<FExtender> OnExtendDialogueAssetSelectionMenu(const TArray<FAssetData>& SelectedAssets);

	/** Builds the actual menu entries (TTS voices + facial animation) for the given dialogues. */
	void PopulateDialogueBatchMenu(FMenuBuilder& MenuBuilder, TArray<TWeakObjectPtr<UADSDialogue>> Dialogues);

	/** Handle to the registered Content Browser menu extender, used to unregister on shutdown. */
	FDelegateHandle ContentBrowserExtenderHandle;
};
