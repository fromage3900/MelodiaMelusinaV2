// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#pragma once

struct FACFAttributeWrapper;

namespace ACFAttributeStrUtils
{
	FString ToString(const FACFAttributeWrapper& InAttribute);
	FString GetDisplayClassName(const FACFAttributeWrapper& InAttribute);
}