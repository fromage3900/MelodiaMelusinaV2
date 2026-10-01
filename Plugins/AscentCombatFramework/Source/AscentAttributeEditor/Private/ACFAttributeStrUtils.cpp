// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "ACFAttributeStrUtils.h"

#include "ACFAttributeWrapper.h"

namespace ACFAttributeStrUtils
{	
	FString ToString(const FACFAttributeWrapper& InAttribute)
	{
		return InAttribute.IsValidSafe()
			? FString::Printf(TEXT("%s.%s"), *GetDisplayClassName(InAttribute), *InAttribute.GetAttributeName())
			: "None";
	}

	FString GetDisplayClassName(const FACFAttributeWrapper& InAttribute)
	{
		FString Name = InAttribute.GetClassName();
		if (Name.EndsWith("_C"))
		{
			Name = Name.LeftChop(2);
		}
		return Name;
	}
}
