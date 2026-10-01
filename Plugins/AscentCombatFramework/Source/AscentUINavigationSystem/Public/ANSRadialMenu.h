// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Engine/Texture2D.h"
#include "ANSRadialMenu.generated.h"

USTRUCT(BlueprintType)
struct FACFRadialMenuData {

	GENERATED_BODY()

public:

	FACFRadialMenuData()
	{
		TagName = FGameplayTag::EmptyTag;
		Name = FText::FromString("Default");
		Texture = nullptr;
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FGameplayTag TagName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	FText Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "ACF")
	UTexture2D* Texture;

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return TagName != Other;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return TagName == Other;
	}

	FORCEINLINE bool operator!=(const FACFRadialMenuData& Other) const
	{
		return TagName != Other.TagName;
	}

	FORCEINLINE bool operator==(const FACFRadialMenuData& Other) const
	{
		return TagName == Other.TagName;
	}
};

class ASCENTUINAVIGATIONSYSTEM_API ANSRadialMenu
{
public:
	ANSRadialMenu();
	~ANSRadialMenu();
};