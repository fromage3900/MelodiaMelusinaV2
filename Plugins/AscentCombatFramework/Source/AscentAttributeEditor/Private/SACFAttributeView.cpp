// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "SACFAttributeView.h"

#include "ACFAttributeTableRow.h"

void SACFAttributeView::Construct(const FArguments& InArgs)
{
	Items = InArgs._Items;

	SizeManager = MakeShared<SACFAttributeViewSizeManager>();

	ChildSlot
	[
		SNew(SBorder)
		.Padding(6.f)
		[
			SAssignNew(TreeViewWidget, SACFAttributeTreeView)
			.TreeItemsSource(&Items)
			.OnGenerateRow(this, &SACFAttributeView::OnGenerateRow)
			.OnGetChildren(this, &SACFAttributeView::OnGetChildren)
			.SelectionMode(ESelectionMode::Single)
			.OnSelectionChanged(InArgs._OnSelectionChanged)
			.HeaderRow
			(
				SNew(SHeaderRow)
				+ SHeaderRow::Column("Class")
					.DefaultLabel(NSLOCTEXT("SACFAttributeTreeView", "ClassColumn", "Class"))
					.ManualWidth_Lambda([this]()
					{
						return SizeManager->GetSize("Class");
					})
				+ SHeaderRow::Column("Separator")
					.DefaultLabel(NSLOCTEXT("SACFAttributeTreeView", "SeparatorColumn", "Separator"))
					.ManualWidth_Lambda([this]()
					{
						return SizeManager->GetSize("Separator");
					})
				+ SHeaderRow::Column("Attribute")
					.DefaultLabel(NSLOCTEXT("SACFAttributeTreeView", "AttributeColumn", "Attribute"))
					.ManualWidth_Lambda([this]()
					{
						return SizeManager->GetSize("Attribute");
					})
			)
		]
	];

	TreeViewWidget->GetHeaderRow()->SetVisibility(EVisibility::Collapsed);
}

void SACFAttributeView::SetHighlightText(const FText& InHighlightText)
{
	HighlightText = InHighlightText;
}

void SACFAttributeView::SetItems(TArray<TSharedPtr<FACFAttributeWrapper>> InItems)
{
	Items = MoveTemp(InItems);
	if (TreeViewWidget.IsValid())
	{
		TreeViewWidget->RequestTreeRefresh();
	}
}

FVector2D SACFAttributeView::ComputeDesiredSize(float InScale) const
{
	FVector2D Size = SCompoundWidget::ComputeDesiredSize(InScale);
	Size.X = FMath::Max(SizeManager->GetTotalSize() * InScale, Size.X);
	return Size;
}

TSharedRef<ITableRow> SACFAttributeView::OnGenerateRow(TSharedPtr<FACFAttributeWrapper> InItem,
                                                           const TSharedRef<STableViewBase>& OwnerTable)
{
	return SNew(ACFAttributeTableRow, OwnerTable)
		.Item(InItem)
		.SizeManager(SizeManager)
		.HighlightText(HighlightText);
}

void SACFAttributeView::OnGetChildren(TSharedPtr<FACFAttributeWrapper> InItem,
	TArray<TSharedPtr<FACFAttributeWrapper>>& OutChildren) const
{
}
