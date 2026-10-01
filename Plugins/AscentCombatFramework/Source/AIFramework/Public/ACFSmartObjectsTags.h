// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once

#include "GameplayTagContainer.h"
#include "NativeGameplayTags.h"


UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_SmartObjects_Chair);
UE_DECLARE_GAMEPLAY_TAG_EXTERN(Tag_SmartObjects_Bed);

struct FACFSmartObjectTags
{
	static FGameplayTag Chair() { return Tag_SmartObjects_Chair; }
	static FGameplayTag Bed()   { return Tag_SmartObjects_Bed; }
};
