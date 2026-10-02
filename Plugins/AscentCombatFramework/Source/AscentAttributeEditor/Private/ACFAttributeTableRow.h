// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

struct FACFAttributeWrapper;

class SACFAttributeViewSizeManager
{
public:
	void SetSize(const FName& Column, const float Width);
	void Reset();
	float GetSize(const FName& Column) const;
	float GetTotalSize() const;

private:
	TMap<FName, float> Columns;
	float TotalSize = 0.f;
};

class ACFAttributeTableRow final : public SMultiColumnTableRow<TSharedPtr<FACFAttributeWrapper>>
{
public:
	SLATE_BEGIN_ARGS(ACFAttributeTableRow)
	{}
		SLATE_ARGUMENT(FText, HighlightText)
		SLATE_ARGUMENT(TSharedPtr<FACFAttributeWrapper>, Item)
		SLATE_ARGUMENT(TSharedPtr<SACFAttributeViewSizeManager>, SizeManager)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, const TSharedRef<STableViewBase>& InOwnerTable);

	virtual TSharedRef<SWidget> GenerateWidgetForColumn(const FName& ColumnName) override;

private:
	FText HighlightClassName;
	FText HighlightAttribute;
	TSharedPtr<FACFAttributeWrapper> Item;
	TSharedPtr<SACFAttributeViewSizeManager> SizeManager;
};
