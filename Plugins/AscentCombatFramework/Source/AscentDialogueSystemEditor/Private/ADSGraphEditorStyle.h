// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "CoreMinimal.h"
#include "Styling/SlateStyle.h"

class FADSGraphEditorStyle
{
public:
	static void Initialize();
	static void Shutdown();

	static const FName& GetStyleSetName();

private:
	static TSharedPtr<FSlateStyleSet> StyleSet;
};
