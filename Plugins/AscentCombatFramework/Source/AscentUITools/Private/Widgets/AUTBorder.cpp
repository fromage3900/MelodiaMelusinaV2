// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "Widgets/AUTBorder.h"
#include "AUTUIFunctionLibrary.h"


void UAUTBorder::SynchronizeProperties()
{
    SetStyle(StyleIndex);
	Super::SynchronizeProperties();
}

void UAUTBorder::SetStyle(int32 inStyle) {
        StyleIndex = inStyle;
        FSlateBrush outBack;
        if (UAUTUIFunctionLibrary::TryGetBackgroundStyle(StyleIndex, outBack) && bUseStyle) {
            Background = outBack;
        }
}