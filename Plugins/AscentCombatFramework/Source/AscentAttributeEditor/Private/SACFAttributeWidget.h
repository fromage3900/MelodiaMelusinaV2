// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAttributeWrapper.h"

class SACFAttributeWidget : public SCompoundWidget
{
public:
	DECLARE_DELEGATE_OneParam(FOnAttributeChanged, const FACFAttributeWrapper&)

	SLATE_BEGIN_ARGS(SACFAttributeWidget) : _CompactMode(false)
	{}
	SLATE_ARGUMENT(bool, CompactMode)
	SLATE_ARGUMENT(FString, FilterMetaData)
	SLATE_ARGUMENT(FACFAttributeWrapper, DefaultAttribute)
	SLATE_ARGUMENT(TArray<UClass*>, WhiteList)
	SLATE_EVENT(FOnAttributeChanged, OnAttributeChanged)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	FOnAttributeChanged OnAttributeChanged;
	FString FilterMetaData;
	FACFAttributeWrapper SelectedAttribute;
	TSharedPtr<SComboButton> ComboButton;
	TArray<UClass*> WhiteList;

	TSharedRef<SWidget> GenerateAttributePicker();
	FText GetSelectedValueAsString() const;
	void OnMenu(const FPointerEvent& MouseEvent);
	void OnCopyAttribute(const FACFAttributeWrapper& copiedAttribute);
	bool CanPaste() const;
	void OnPasteAttribute();
	void OnAttributePicked(const FACFAttributeWrapper& InAttribute);
};
