#pragma once

#include "EditorStyleSet.h"

#include "CoreMinimal.h"
#include "Framework/Commands/UICommandInfo.h"
#include "Framework/Commands/Commands.h"
#include "Styling/AppStyle.h"


class AGSGRAPHEDITOR_API FEditorCommands_AGSGraph : public TCommands<FEditorCommands_AGSGraph> {
public:
	/** Constructor */
    FEditorCommands_AGSGraph()
        : TCommands<FEditorCommands_AGSGraph>("AGSGraphEditor", NSLOCTEXT("Contexts", "AGSGraphEditor", "AGS Graph Editor"), NAME_None, FAppStyle::GetAppStyleSetName() )
	{
	}
	
	TSharedPtr<FUICommandInfo> GraphSettings;

	virtual void RegisterCommands() override;
};
