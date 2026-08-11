// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/PCGExEnumSelectorCustomization.h"

#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "PropertyHandle.h"
#include "Details/PCGExEnumSelectorWidget.h"

#define LOCTEXT_NAMESPACE "PCGExEnumSelectorCustomization"

TSharedRef<IPropertyTypeCustomization> FPCGExEnumSelectorCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExEnumSelectorCustomization());
}

void FPCGExEnumSelectorCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	// Collapse the header. We render the single-row [name + widget] pair from CustomizeChildren
	// instead, so this customization composes cleanly with both default and
	// ShowOnlyInnerProperties usage at field sites without producing duplicate rows.
	HeaderRow.Visibility(EVisibility::Collapsed);
}

void FPCGExEnumSelectorCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	ChildBuilder.AddCustomRow(LOCTEXT("EnumSelector", "Enum Selector"))
	            .NameContent()
		[
			PropertyHandle->CreatePropertyNameWidget()
		]
		.ValueContent()
		.MinDesiredWidth(250.0f)
		.MaxDesiredWidth(3000.0f)
		[
			PCGExEnumSelectorWidget::Make(PropertyHandle, /*bAllowClassPicker=*/true)
		];
}

#undef LOCTEXT_NAMESPACE
