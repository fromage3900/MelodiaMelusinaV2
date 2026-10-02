// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "Widgets/AUTTextBlock.h"
#include "AUTUIFunctionLibrary.h"

void UAUTTextBlock::SynchronizeProperties()
{
    UpdateStyle();
    
    Super::SynchronizeProperties();
}

void UAUTTextBlock::SetStyleIndex(int32 inStyleIndex)
{
    StyleIndex = inStyleIndex;
    UpdateStyle();
}

void UAUTTextBlock::UpdateStyle()
{
    FAUTTextStyle outBack;
    if (bUseStyle && UAUTUIFunctionLibrary::TryGetTitleStyle(StyleIndex, outBack)) {
        outBack.Normal.Size = TextSize;
        SetFont(outBack.Normal);
        SetColorAndOpacity(outBack.NormalColor);
    }
}

void UAUTTextBlock::SetFontSize(int32 inFontSize)
{
    TextSize = inFontSize;
    UpdateStyle();
}
