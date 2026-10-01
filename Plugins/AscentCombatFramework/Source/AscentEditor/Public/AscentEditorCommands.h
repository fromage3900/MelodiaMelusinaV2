// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Framework/Commands/Commands.h"
#include "AscentEditorStyle.h"

class FAscentEditorCommands : public TCommands<FAscentEditorCommands>
{
public:

	FAscentEditorCommands()
		: TCommands<FAscentEditorCommands>(TEXT("AscentEditor"), NSLOCTEXT("Contexts", "AscentEditor", "AscentEditor Plugin"), NAME_None, FAscentEditorStyle::GetStyleSetName())
	{
	}

	// TCommands<> interface
	virtual void RegisterCommands() override;

public:
	TSharedPtr< FUICommandInfo > PluginAction;
};
