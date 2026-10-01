// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAttributeWrapper.h"

class SACFAttributeViewSizeManager;
using SACFAttributeTreeView = STreeView<TSharedPtr<FACFAttributeWrapper>>;

class SACFAttributeView final : public SCompoundWidget
{
public:
	using FOnSelectionChanged = SACFAttributeTreeView::FOnSelectionChanged;

	SLATE_BEGIN_ARGS(SACFAttributeView) {}
		SLATE_ARGUMENT(TArray<TSharedPtr<FACFAttributeWrapper>>, Items)
		SLATE_EVENT(FOnSelectionChanged, OnSelectionChanged)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	void SetHighlightText(const FText& InHighlightText);
	void SetItems(TArray<TSharedPtr<FACFAttributeWrapper>> InItems);

	virtual FVector2D ComputeDesiredSize(float InScale) const override;

private:
	TArray<TSharedPtr<FACFAttributeWrapper>> Items;
	TSharedPtr<SACFAttributeTreeView> TreeViewWidget;
	FText HighlightText;
	TSharedPtr<SACFAttributeViewSizeManager> SizeManager;

	TSharedRef<ITableRow> OnGenerateRow(
		TSharedPtr<FACFAttributeWrapper> InItem,
		const TSharedRef<STableViewBase>& OwnerTable);
	void OnGetChildren(
		TSharedPtr<FACFAttributeWrapper> InItem,
		TArray<TSharedPtr<FACFAttributeWrapper>>& OutChildren) const;
};