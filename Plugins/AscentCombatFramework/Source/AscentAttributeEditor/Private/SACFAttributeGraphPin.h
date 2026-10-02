// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFAttributeWrapper.h"
#include "EdGraphUtilities.h"
#include "SGraphPin.h"

class SACFAttributeGraphPin : public SGraphPin
{
public:
	SLATE_BEGIN_ARGS(SACFAttributeGraphPin) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs, UEdGraphPin* InGraphPinObj);

	//~ Begin SGraphPin Interface
	virtual TSharedRef<SWidget>	GetDefaultValueWidget() override;
	//~ End SGraphPin Interface

private:
	FACFAttributeWrapper SelectedAttribute;

	void OnAttributeChanged(const FACFAttributeWrapper& Attribute);
	bool GetDefaultValueIsEnabled() const;
};

class FACFAttributeGraphPanelPinFactory: public FGraphPanelPinFactory
{
	virtual TSharedPtr<class SGraphPin> CreatePin(class UEdGraphPin* InPin) const override;
};