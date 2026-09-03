// Copyright Bruno Caxito. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"

/**
 * Add custom blueprint toolbar commands.
 */
class FQuillscriptEditorToolbarCommands final : public TCommands<FQuillscriptEditorToolbarCommands>
{
public:
	TSharedPtr<FUICommandInfo> OpenAlbum;
	TSharedPtr<FUICommandInfo> OpenHomeSite;
	TSharedPtr<FUICommandInfo> OpenIllustrationsFolder;

	FQuillscriptEditorToolbarCommands()
		: TCommands(
			"Quillscript",
			FText::FromString("Editor extension"),
			NAME_None,
			FAppStyle::GetAppStyleSetName()
		) { }

	virtual void RegisterCommands() override;
};