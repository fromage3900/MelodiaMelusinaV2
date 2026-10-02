// Copyright (C) Developed by Pask and Yurii Agapov, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.
#pragma once

namespace ACFAttributePropertyUtils
{
	template <typename Type>
	inline void WithPropertyValue(const TSharedPtr<IPropertyHandle>& Handle, TFunction<void (Type& Value)>&& Func)
	{
		if (!Handle.IsValid())
			return;
		TArray<void*> RawData;
		Handle->AccessRawData(RawData);
		for (void* Data : RawData)
		{
			if (Data)
				Func(*static_cast<Type*>(Data));
		}
	}
}