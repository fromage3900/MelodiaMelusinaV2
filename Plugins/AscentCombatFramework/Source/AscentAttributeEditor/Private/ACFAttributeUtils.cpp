// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeUtils.h"

#include "AttributeSet.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/AssetManager.h"
#include "Engine/StreamableManager.h"

namespace ACFAttributeUtils
{
	bool IsValid(const FGameplayAttribute& InAttribute)
	{
		static FObjectProperty* Property = CastField<FObjectProperty>(FGameplayAttribute::StaticStruct()->FindPropertyByName("AttributeOwner"));
		return Property && IsValid(Property->GetObjectPtrPropertyValuePtr(Property->ContainerPtrToValuePtr<uint8>(&InAttribute))->Get());
	}

	FString ExportToString(const FGameplayAttribute& InAttribute)
	{
		FString Str;	
		if (const TObjectPtr<UObject> OwnerObject = InAttribute.GetAttributeSetClass()->GetDefaultObject(false))
		{

			FGameplayAttribute::StaticStruct()->ExportText(Str, &InAttribute, &InAttribute, OwnerObject, 0,
														   nullptr);
		}
		return Str;
	}

	FGameplayAttribute ImportFromString(const FString& InStr)
	{
		FGameplayAttribute Attribute;
		FGameplayAttribute::StaticStruct()->ImportText(*InStr, &Attribute, /*OwnerObject*/nullptr, 0, nullptr,
													   FGameplayAttribute::StaticStruct()->GetName(),
													   /*bAllowNativeOverride*/true);

		return Attribute;
	}

	bool IsAttributeType(const FProperty* InProperty)
	{
		return CastField<FNumericProperty>(InProperty)
			|| FGameplayAttribute::IsGameplayAttributeDataProperty(InProperty);
	}

}
