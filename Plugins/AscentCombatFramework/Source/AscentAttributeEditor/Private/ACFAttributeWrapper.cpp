// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeWrapper.h"

#include "ACFAttributeUtils.h"


FACFAttributeWrapper::FACFAttributeWrapper(const FProperty* Property)
	: ClassPath(Property ? Property->GetOwnerClass() : nullptr)
	, PropertyName(Property ? Property->GetFName() : NAME_None)
	, ClassPtr(Property ? Property->GetOwnerClass() : nullptr)
	, Property(Property)
{
}

FACFAttributeWrapper::FACFAttributeWrapper(const FGameplayAttribute& Attribute)
	: FACFAttributeWrapper(ACFAttributeUtils::IsValid(Attribute) ? Attribute.GetUProperty() : nullptr)
{
}

FACFAttributeWrapper::FACFAttributeWrapper(const FSoftClassPath& ClassPath, const FName& PropertyName)
	: ClassPath(ClassPath)
	, PropertyName(PropertyName)
{
	UpdateCache();
}

bool FACFAttributeWrapper::IsValidFast() const
{
	return ClassPtr && Property;
}

bool FACFAttributeWrapper::IsValidSafe() const
{
	if (!IsValidFast())
		UpdateCache();
	return IsValidFast();
}

FACFAttributeWrapper::operator FGameplayAttribute() const
{
	return IsValidSafe() ? FGameplayAttribute{const_cast<FProperty*>(Property)} : FGameplayAttribute{};
}

FString FACFAttributeWrapper::ToPathString() const
{
	return IsValidSafe()
		? FString::Printf(TEXT("%s.%s"), *ClassPath.GetAssetName(), *PropertyName.ToString())
		: "None";
}

FString FACFAttributeWrapper::GetClassName() const
{
	return IsValidSafe()
		? ClassPath.GetAssetName() 
		: "None";
}

FString FACFAttributeWrapper::GetAttributeName() const
{
	return PropertyName.IsValid() ? PropertyName.ToString() : FString{};
}

FSoftClassPath FACFAttributeWrapper::GetClassPath() const
{
	return ClassPath;
}

void FACFAttributeWrapper::UpdateCache() const
{
	if (ClassPtr)
	{
		if (!Property)
			Property = ClassPtr->FindPropertyByName(PropertyName);
	}
	else
	{
		if (ClassPtr = ClassPath.ResolveClass(); ClassPtr)
			Property = ClassPtr->FindPropertyByName(PropertyName);
		else
			Property = nullptr;
	}
}
