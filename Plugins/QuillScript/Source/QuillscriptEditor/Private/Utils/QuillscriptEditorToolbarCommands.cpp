// Copyright Bruno Caxito. All Rights Reserved.

#include "Utils/QuillscriptEditorToolbarCommands.h"


#define LOCTEXT_NAMESPACE "QuillscriptEditorToolbarCommands"

void FQuillscriptEditorToolbarCommands::RegisterCommands()
{
	UI_COMMAND(
		this->OpenHomeSite,
		"Site",
		"Open Quillscript website",
		EUserInterfaceActionType::Button,
		FInputChord()
	);
}

#undef LOCTEXT_NAMESPACE