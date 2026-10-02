// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeTableRow.h"

#include "ACFAttributeWrapper.h"
#include "ACFAttributeStrUtils.h"
#include "ACFAttributePalette.h"

static float GetDPIScale(const TSharedPtr<SWidget>& Widget)
{
	float DPIScale = 1.f;
	if (Widget.IsValid())
	{
		TSharedPtr<SWindow> WidgetWindow = FSlateApplication::Get().FindWidgetWindow(Widget.ToSharedRef());
		if (WidgetWindow.IsValid())
		{
			DPIScale = WidgetWindow->GetNativeWindow()->GetDPIScaleFactor();
		}
	}
	return DPIScale;
}

static float GetMinWidth(const TSharedPtr<STextBlock>& Label, const float Scale)
{
	return Label->ComputeDesiredSize(Scale).X;	
}

void SACFAttributeViewSizeManager::SetSize(const FName& Column, const float Width)
{
	float& CurrentWidth = Columns.FindOrAdd(Column);
	TotalSize -= CurrentWidth;
	CurrentWidth = FMath::Max(CurrentWidth, Width);
	TotalSize += CurrentWidth;
}

void SACFAttributeViewSizeManager::Reset()
{
	Columns.Empty();
}

float SACFAttributeViewSizeManager::GetSize(const FName& Column) const
{
	return Columns.FindRef(Column);
}

float SACFAttributeViewSizeManager::GetTotalSize() const
{
	return TotalSize;
}

void ACFAttributeTableRow::Construct(const FArguments& InArgs, const TSharedRef<STableViewBase>& InOwnerTable)
{	
	Item = InArgs._Item;
	SizeManager = InArgs._SizeManager;
	
	const FString HighlightStr = InArgs._HighlightText.ToString();
	int32 SepIndex = INDEX_NONE;
	if (HighlightStr.FindChar('.', SepIndex))
	{
		HighlightClassName = FText::FromString(HighlightStr.Left(SepIndex));
		HighlightAttribute = FText::FromString(HighlightStr.Mid(SepIndex + 1));
	}
	else
	{
		HighlightClassName = InArgs._HighlightText;
		HighlightAttribute = InArgs._HighlightText;
	}

	SMultiColumnTableRow::Construct(
		FSuperRowType::FArguments(),
		InOwnerTable
	);
}

TSharedRef<SWidget> ACFAttributeTableRow::GenerateWidgetForColumn(const FName& ColumnName)
{
	if (!Item.IsValid() || !Item->IsValidSafe())
	{
		if (ColumnName == "Class")
			return SNew(STextBlock).Text(FText::FromString(TEXT("None"))).Justification(ETextJustify::Type::Right);
		return SNullWidget::NullWidget;
	}

	auto GetColor = [this]()
	{
		return ACFAttributePalette::GetColor(Item->GetClassName());
	};

	const float Scale = GetDPIScale(OwnerTablePtr.Pin()->AsWidget());
	
	if (ColumnName == "Class")
	{
		auto ClassLabel = SNew(STextBlock)
			.Text(FText::FromString(ACFAttributeStrUtils::GetDisplayClassName(*Item)))
			.Justification(ETextJustify::Type::Right)
			.ColorAndOpacity_Lambda(GetColor)
			.HighlightText(HighlightClassName);
		SizeManager->SetSize(ColumnName, GetMinWidth(ClassLabel, Scale));
		return ClassLabel;
	}
	if (ColumnName == "Separator")
	{
		auto SeparatorLabel = SNew(STextBlock)
			.Text(FText::FromString(TEXT(".")))
			.Justification(ETextJustify::Type::Center)
			.ColorAndOpacity(FSlateColor{FColor::White});
		SizeManager->SetSize(ColumnName, GetMinWidth(SeparatorLabel, Scale) * 3.f);
		return SeparatorLabel;
	}
	if (ColumnName == "Attribute")
	{
		auto AttributeLabel = SNew(STextBlock)
			.Text(FText::FromString(Item->GetAttributeName()))
			.ColorAndOpacity_Lambda(GetColor)
			.HighlightText(HighlightAttribute);
		SizeManager->SetSize(ColumnName, GetMinWidth(AttributeLabel, Scale));
		return AttributeLabel;
	}

	return SNullWidget::NullWidget;
}
