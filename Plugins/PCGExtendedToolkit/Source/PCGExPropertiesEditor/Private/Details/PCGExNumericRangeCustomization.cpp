// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExNumericRangeCustomization.h"

#include "DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "PropertyHandle.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "FPCGExNumericRangeCustomization"

TSharedRef<IPropertyTypeCustomization> FPCGExNumericRangeCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExNumericRangeCustomization());
}

void FPCGExNumericRangeCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	TSharedPtr<IPropertyHandle> ClampMinHandle = PropertyHandle->GetChildHandle(TEXT("bClampMin"));
	TSharedPtr<IPropertyHandle> MinHandle = PropertyHandle->GetChildHandle(TEXT("Min"));
	TSharedPtr<IPropertyHandle> ClampMaxHandle = PropertyHandle->GetChildHandle(TEXT("bClampMax"));
	TSharedPtr<IPropertyHandle> MaxHandle = PropertyHandle->GetChildHandle(TEXT("Max"));

	// Bail to default rendering if the struct shape ever changes underneath us;
	// callers will see the four default rows, no UI breakage.
	if (!ClampMinHandle.IsValid() || !MinHandle.IsValid() || !ClampMaxHandle.IsValid() || !MaxHandle.IsValid())
	{
		HeaderRow
			.NameContent()[PropertyHandle->CreatePropertyNameWidget()];
		return;
	}

	// Values stay always-editable; the checkboxes only toggle whether the clamp APPLIES
	// downstream (to numeric pickers in overrides). Lets the schema author configure both
	// numbers up front and then flip the toggles independently without having to re-enter
	// values when re-enabling a previously-disabled clamp.
	HeaderRow
		.NameContent()
		[
			PropertyHandle->CreatePropertyNameWidget()
		]
		.ValueContent()
		.MinDesiredWidth(280.0f)
		.MaxDesiredWidth(3000.0f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.Padding(0, 0, 4, 0)
			[
				ClampMinHandle->CreatePropertyValueWidget()
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.Padding(0, 0, 4, 0)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("MinLabel", "Min"))
				.Font(IDetailLayoutBuilder::GetDetailFont())
			]
			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			.Padding(0, 0, 12, 0)
			[
				MinHandle->CreatePropertyValueWidget()
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.Padding(0, 0, 4, 0)
			[
				ClampMaxHandle->CreatePropertyValueWidget()
			]
			+ SHorizontalBox::Slot()
			.AutoWidth()
			.VAlign(VAlign_Center)
			.Padding(0, 0, 4, 0)
			[
				SNew(STextBlock)
				.Text(LOCTEXT("MaxLabel", "Max"))
				.Font(IDetailLayoutBuilder::GetDetailFont())
			]
			+ SHorizontalBox::Slot()
			.FillWidth(1.0f)
			.VAlign(VAlign_Center)
			[
				MaxHandle->CreatePropertyValueWidget()
			]
		];
}

void FPCGExNumericRangeCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	// Everything visible lives in the header strip; suppress the expandable child rows.
}

#undef LOCTEXT_NAMESPACE
