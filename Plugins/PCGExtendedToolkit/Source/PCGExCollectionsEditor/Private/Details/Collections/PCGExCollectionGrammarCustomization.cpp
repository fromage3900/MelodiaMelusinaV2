// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "Details/Collections/PCGExCollectionGrammarCustomization.h"

#include "DetailWidgetRow.h"
#include "IDetailChildrenBuilder.h"
#include "PropertyHandle.h"

// Stubbed: FPCGExCollectionGrammarDetails is now LEGACY (schema v0). It only exists for
// PostLoad migration of pre-v1 data into the unified FPCGExAssetGrammarDetails. The struct
// is no longer surfaced in user-facing details panels, so this customization is effectively
// dead -- kept (and not registered) to preserve the header reference until the legacy struct
// is dropped entirely in a future major version.

TSharedRef<IPropertyTypeCustomization> FPCGExCollectionGrammarCustomization::MakeInstance()
{
	return MakeShareable(new FPCGExCollectionGrammarCustomization());
}

void FPCGExCollectionGrammarCustomization::CustomizeHeader(
	TSharedRef<IPropertyHandle> PropertyHandle,
	FDetailWidgetRow& HeaderRow,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	HeaderRow.NameContent()[PropertyHandle->CreatePropertyNameWidget()];
}

void FPCGExCollectionGrammarCustomization::CustomizeChildren(
	TSharedRef<IPropertyHandle> PropertyHandle,
	IDetailChildrenBuilder& ChildBuilder,
	IPropertyTypeCustomizationUtils& CustomizationUtils)
{
	uint32 NumChildren = 0;
	PropertyHandle->GetNumChildren(NumChildren);
	for (uint32 i = 0; i < NumChildren; i++)
	{
		if (TSharedPtr<IPropertyHandle> Child = PropertyHandle->GetChildHandle(i))
		{
			ChildBuilder.AddProperty(Child.ToSharedRef());
		}
	}
}
