// Copyright 2026 Timothé Lapetite and contributors
// Released under the MIT license https://opensource.org/license/MIT/

#include "PCGExEnumSelector.h"

FText FPCGExEnumSelector::GetDisplayName() const
{
	if (!Class)
	{
		return FText::GetEmpty();
	}
	return Class->GetDisplayNameTextByValue(Value);
}

FString FPCGExEnumSelector::GetCultureInvariantDisplayName() const
{
	if (!Class)
	{
		return FString();
	}
	return Class->GetDisplayNameTextByValue(Value).BuildSourceString();
}
