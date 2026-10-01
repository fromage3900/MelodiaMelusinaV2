// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.


#include "GameplayEffects/ACFDefaultCooldownGE.h"
#include "ACFActionTypes.h"

UACFDefaultCooldownGE::UACFDefaultCooldownGE()
{
	DurationPolicy = EGameplayEffectDurationType::HasDuration;

	const FGameplayTag defaultTAG = FGameplayTag::RequestGameplayTag(ACF::CooldownTag, true);
	CachedGrantedTags.AddTag(defaultTAG);
	// Add the granted tags component
	/*
	UTargetTagsGameplayEffectComponent* TagsComp = CreateDefaultSubobject<UTargetTagsGameplayEffectComponent>(TEXT("TargetTags"));
	GEComponents.Add(TagsComp);

	FInheritedTagContainer Tags;
	Tags.AddTag();
	TagsComp->SetAndApplyTargetTagChanges(Tags);*/
}

