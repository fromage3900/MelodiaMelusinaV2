// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2023. All Rights Reserved.

#include "Widgets/AUTRichTextBlock.h"
#include "AUTUIFunctionLibrary.h"

void UAUTRichTextBlock::SynchronizeProperties()
{
	UpdateStyle();
    
	Super::SynchronizeProperties();
}

void UAUTRichTextBlock::SetStyleIndex(int32 inStyleIndex)
{
	StyleIndex = inStyleIndex;
	UpdateStyle();
}

void UAUTRichTextBlock::UpdateStyle()
{
	FAUTTextStyle outBack;
	if (bUseStyle && UAUTUIFunctionLibrary::TryGetTitleStyle(StyleIndex, outBack)) {
		outBack.Normal.Size = TextSize;
		SetDefaultFont(outBack.Normal);
		SetDefaultColorAndOpacity(outBack.NormalColor);
	}
}

void UAUTRichTextBlock::SetFontSize(int32 inFontSize)
{
	TextSize = inFontSize;
	UpdateStyle();
}
