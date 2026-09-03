// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExPropertyLabelRow.h"

#include "DetailLayoutBuilder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

namespace PCGExPropertyLabelRow
{
	TSharedRef<SWidget> Build(TAttribute<FText> NameAttr, TAttribute<FText> TypeAttr, bool bShowSeparator)
	{
		TSharedRef<SHorizontalBox> Row = SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			[
				SNew(STextBlock)
				.Text(MoveTemp(NameAttr))
				.Font(IDetailLayoutBuilder::GetDetailFont())
			];

		if (bShowSeparator)
		{
			Row->AddSlot()
			   .AutoWidth()
			   .VAlign(VAlign_Center)
			   .Padding(6, 0, 6, 0)
			[
				SNew(STextBlock)
				.Text(FText::FromString(TEXT("|")))
				.Font(IDetailLayoutBuilder::GetDetailFont())
				.ColorAndOpacity(FSlateColor::UseSubduedForeground())
			];
		}

		Row->AddSlot()
		   .AutoWidth()
		   .VAlign(VAlign_Center)
		   .Padding(bShowSeparator ? 0 : 6, 0, 0, 0)
		[
			SNew(STextBlock)
			.Text(MoveTemp(TypeAttr))
			.Font(IDetailLayoutBuilder::GetDetailFontItalic())
			.ColorAndOpacity(FSlateColor::UseSubduedForeground())
		];

		return Row;
	}
}
