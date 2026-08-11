// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/Collections/PCGExSelectorClosestMatchAxisCustomization.h"

#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "PropertyHandle.h"
#include "Details/Collections/PCGExCollectionEditorSlateUtils.h"
#include "Selectors/PCGExSelectorClosestMatch.h"
#include "Widgets/SBoxPanel.h"

using PCGExCollectionEditorSlateUtils::MakeSmallLabel;

TSharedRef<IPropertyTypeCustomization> FPCGExSelectorClosestMatchAxisCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExSelectorClosestMatchAxisCustomization());
}

void FPCGExSelectorClosestMatchAxisCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	const TSharedPtr<IPropertyHandle> PropertyNameHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExSelectorClosestMatchAxis, PropertyName));
	const TSharedPtr<IPropertyHandle> AttributeNameHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExSelectorClosestMatchAxis, AttributeName));
	const TSharedPtr<IPropertyHandle> WeightHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExSelectorClosestMatchAxis, Weight));
	const TSharedPtr<IPropertyHandle> NormalizeHandle = PropertyHandle->GetChildHandle(GET_MEMBER_NAME_CHECKED(FPCGExSelectorClosestMatchAxis, bNormalize));

	HeaderRow
		.NameContent()
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0)
			[
				PropertyHandle->CreatePropertyNameWidget()
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(1, 0)
			[
				MakeSmallLabel(TEXT("Prop:"))
			]
			+ SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center).Padding(1, 0)
			[
				PropertyNameHandle->CreatePropertyValueWidget()
			]
		]
		.ValueContent()
		.MinDesiredWidth(300)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(1, 0)
			[
				MakeSmallLabel(TEXT("Attr:"))
			]
			+ SHorizontalBox::Slot().FillWidth(1).VAlign(VAlign_Center).Padding(1, 0)
			[
				AttributeNameHandle->CreatePropertyValueWidget()
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4, 0, 1, 0)
			[
				MakeSmallLabel(TEXT("W:"))
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(1, 0)
			[
				WeightHandle->CreatePropertyValueWidget()
			]
			// Normalize toggle -- no label; tooltip on the property carries the explanation.
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(6, 0, 0, 0)
			[
				NormalizeHandle->CreatePropertyValueWidget()
			]
		];
}

void FPCGExSelectorClosestMatchAxisCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	// Header carries everything; nothing to expand.
}
