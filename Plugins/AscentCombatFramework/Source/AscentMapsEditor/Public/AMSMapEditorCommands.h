// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/Commands/Commands.h"
#include "AMSMapEditorStyle.h"
#include <Framework/Commands/UICommandInfo.h>

class FAMSMapEditorCommands : public TCommands<FAMSMapEditorCommands>
{
public:

	FAMSMapEditorCommands()
		: TCommands<FAMSMapEditorCommands>(TEXT("AMSMapEditor"), NSLOCTEXT("Contexts", "AMSMapEditor", "AMSMapEditor Plugin"), NAME_None, FAMSMapsEditorStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > PluginAction;
};
