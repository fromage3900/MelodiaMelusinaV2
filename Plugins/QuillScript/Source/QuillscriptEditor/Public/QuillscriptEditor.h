// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateStyle.h"
#include "Modules/ModuleManager.h"


/**
 * Quillscript plugin editor module.
 */
class FQuillscriptEditorModule final : public IModuleInterface
{
public:
	/** IModuleInterface implementation */
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;


private:
	static inline const FName QuillscriptStyleName{ "QuillscriptStyle" };

	TSharedPtr<FSlateStyleSet> StyleSet;
	TSharedPtr<FUICommandList> Commands;


	/// Editor Watcher Extension

	static void OnDirectoryContentsChanged(const TArray<struct FFileChangeData>& FileChanges);


	/// Editor Toolbar Extension

	void AddToolbarButtons(FToolBarBuilder& ToolbarBuilder);
	static TSharedRef<SWidget> FillComboButton(const TSharedPtr<FUICommandList> CommandsList);


	/// Editor Menu Extension

	void AddMenuEntry(FMenuBuilder& MenuBuilder) const;
	void FillSubmenu(FMenuBuilder& MenuBuilder) const;


	/// Blueprints Toolbar Extension

	static void OnGatherExtensions(const TSharedPtr<FExtender> Extender, UBlueprint* Blueprint);
	static void AddBlueprintsToolbarButton(FToolBarBuilder& Builder);


	/// Blueprints Extension Commands

	static void OnOpenAlbum(UBlueprint* Blueprint);
	void SpawnScriptViewer() const;
};