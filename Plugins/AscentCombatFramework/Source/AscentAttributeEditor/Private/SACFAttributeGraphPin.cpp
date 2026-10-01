// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "SACFAttributeGraphPin.h"

#include "SACFAttributeWidget.h"

#include "AttributeSet.h"
#include "ScopedTransaction.h"
#include "UObject/UObjectIterator.h"
#include "Widgets/SBoxPanel.h"

#define LOCTEXT_NAMESPACE "K2Node"

void SACFAttributeGraphPin::Construct( const FArguments& InArgs, UEdGraphPin* InGraphPinObj )
{
	SGraphPin::Construct( SGraphPin::FArguments(), InGraphPinObj );
}

TSharedRef<SWidget>	SACFAttributeGraphPin::GetDefaultValueWidget()
{	
	FGameplayAttribute DefaultAttribute;

	FString DefaultString = GraphPinObj->GetDefaultAsString();
	if (!DefaultString.IsEmpty())
	{
		UScriptStruct* PinLiteralStructType = FGameplayAttribute::StaticStruct();
		PinLiteralStructType->ImportText(*DefaultString, &DefaultAttribute, nullptr, EPropertyPortFlags::PPF_SerializedAsImportText, GError, PinLiteralStructType->GetName(), true);
	}

	// Create widget
	return SNew(SVerticalBox)
		+SVerticalBox::Slot()
		.AutoHeight()
		[
			SNew(SACFAttributeWidget)
			.OnAttributeChanged(this, &SACFAttributeGraphPin::OnAttributeChanged)
			.DefaultAttribute(DefaultAttribute)
			.Visibility(this, &SGraphPin::GetDefaultValueVisibility)
			.IsEnabled(this, &SACFAttributeGraphPin::GetDefaultValueIsEnabled)
		];
}

void SACFAttributeGraphPin::OnAttributeChanged(const FACFAttributeWrapper& Attribute)
{
	SelectedAttribute = Attribute;

	FGameplayAttribute NewAttributeStruct = SelectedAttribute;

	FString FinalValue;
	FGameplayAttribute::StaticStruct()->ExportText(FinalValue, &NewAttributeStruct, &NewAttributeStruct, nullptr, EPropertyPortFlags::PPF_SerializedAsImportText, nullptr);
	if (FinalValue != GraphPinObj->GetDefaultAsString())
	{
		const FScopedTransaction Transaction(NSLOCTEXT("GraphEditor", "ChangePinValue", "Change Pin Value"));
		GraphPinObj->Modify();
		GraphPinObj->GetSchema()->TrySetDefaultValue(*GraphPinObj, FinalValue);
	}
}

bool SACFAttributeGraphPin::GetDefaultValueIsEnabled() const
{
	return !GraphPinObj->bDefaultValueIsReadOnly;
}

TSharedPtr<class SGraphPin> FACFAttributeGraphPanelPinFactory::CreatePin(class UEdGraphPin* InPin) const
{
	if (InPin->PinType.PinCategory == UEdGraphSchema_K2::PC_Struct && InPin->PinType.PinSubCategoryObject == FGameplayAttribute::StaticStruct())
	{
		return SNew(SACFAttributeGraphPin, InPin);
	}
	return nullptr;
}

#undef LOCTEXT_NAMESPACE
