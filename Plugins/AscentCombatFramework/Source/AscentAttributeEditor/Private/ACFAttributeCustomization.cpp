// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeCustomization.h"

#include "DetailWidgetRow.h"
#include "ACFAttributeWrapper.h"
#include "ACFAttributePropertyUtils.h"
#include "SACFAttributeWidget.h"

TSharedRef<IPropertyTypeCustomization> FACFAttributeCustomization::MakeInstance()
{
	return MakeShared<FACFAttributeCustomization>();
}

void FACFAttributeCustomization::CustomizeHeader(TSharedRef<IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{	
	AttributeProperty = StructPropertyHandle;

	TArray<UClass*> AttributeSetClasses;
	if (StructPropertyHandle->HasMetaData("OwnerAttributesOnly"))
	{
		TArray<UObject*> OuterObjects;
		AttributeProperty->GetOuterObjects(OuterObjects);
		for (UObject* Object : OuterObjects)
		{
			if (UAttributeSet* AttributeSet = Cast<UAttributeSet>(Object->GetOuter()))
			{
				AttributeSetClasses.Add(AttributeSet->GetClass());
			}
		}
	}

	const FString& FilterMetaStr = StructPropertyHandle->GetProperty()->GetMetaData(TEXT("FilterMetaTag"));

	FACFAttributeWrapper Attribute;
	ACFAttributePropertyUtils::WithPropertyValue<FGameplayAttribute>(AttributeProperty, [&Attribute](auto& Value)
	{
		Attribute = Value;
	});

	HeaderRow.
		NameContent()
		[
			StructPropertyHandle->CreatePropertyNameWidget()
		]
	.ValueContent()
		.MinDesiredWidth(500)
		.MaxDesiredWidth(4096)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot()
			//.FillWidth(1.0f)
			.HAlign(HAlign_Fill)
			.Padding(0.f, 0.f, 2.f, 0.f)
			[
				SNew(SACFAttributeWidget)
				.OnAttributeChanged(this, &FACFAttributeCustomization::OnAttributeChanged)
				.DefaultAttribute(Attribute)
				.FilterMetaData(FilterMetaStr)
				.WhiteList(AttributeSetClasses)
				.CompactMode(!AttributeSetClasses.IsEmpty())
			]
		];
}

void FACFAttributeCustomization::CustomizeChildren( TSharedRef<IPropertyHandle> StructPropertyHandle, class IDetailChildrenBuilder& StructBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils )
{
	// nothing
}

void FACFAttributeCustomization::OnAttributeChanged(const FACFAttributeWrapper& SelectedAttribute)
{
	AttributeProperty->NotifyPreChange();
	ACFAttributePropertyUtils::WithPropertyValue<FGameplayAttribute>(AttributeProperty, [SelectedAttribute](auto& Value)
	{
		Value = SelectedAttribute;
	});
	AttributeProperty->NotifyPostChange(EPropertyChangeType::ValueSet);
	AttributeProperty->NotifyFinishedChangingProperties();
}
