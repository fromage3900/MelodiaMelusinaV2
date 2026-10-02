// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Misc/TextFilter.h"

class UAttributeSet;
class SACFAttributeView;
struct FACFAttributeWrapper;

DECLARE_DELEGATE_OneParam(FOnACFAttributePicked, const FACFAttributeWrapper&);

class SACFAttributePicker : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SACFAttributePicker)
		{}

		SLATE_ARGUMENT(FString, FilterMetaData)
		SLATE_ARGUMENT(FOnACFAttributePicked, OnAttributePickedDelegate)
		SLATE_ARGUMENT(TArray<UClass*>, WhiteList)

	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual ~SACFAttributePicker() override;

private:
	using FAttributeTextFilter = TTextFilter<const FProperty&>;

	FOnACFAttributePicked OnAttributePicked;
	TSharedPtr<SSearchBox> SearchBoxPtr;
	TSharedPtr<SACFAttributeView> AttributeView;
	TSharedPtr<FAttributeTextFilter> AttributeTextFilter;
	FString FilterMetaData;
	TArray<UClass*> WhiteList;

	void OnFilterTextChanged(const FText& InFilterText);
	void OnAttributeSelectionChanged(TSharedPtr<FACFAttributeWrapper> Item, ESelectInfo::Type SelectInfo);
	TArray<TSharedPtr<FACFAttributeWrapper>> CreateAttributes() const;
};
