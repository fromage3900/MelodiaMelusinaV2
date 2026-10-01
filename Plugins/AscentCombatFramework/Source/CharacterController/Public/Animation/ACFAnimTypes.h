// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved. 

#pragma once


#include "CoreMinimal.h"
#include <GameplayTagContainer.h>
#include "Animation/AnimSequence.h"
#include "ACFCoreTypes.h"
#include "ACFCCTypes.h"
#include "AnimNode_ACFBlendByMask.h"
#include "ACFAnimTypes.generated.h"

class UACFBoneBlendMask;
class UACFOverlayLayer;
class UAimOffsetBlendSpace;

/**
 * 
 */
 USTRUCT(BlueprintType)
struct FBaseLayer {

    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite,  meta = (Categories = "Moveset,Mount"), Category = ACF)
    FGameplayTag TagName;

    FORCEINLINE bool operator!=(const FGameplayTag& Other) const
    {
        return TagName != Other;
    }

    FORCEINLINE bool operator==(const FGameplayTag& Other) const
    {
        return TagName == Other;
    }

    FORCEINLINE bool operator!=(const FACFStruct& Other) const
    {
        return TagName != Other.TagName;
    }

    FORCEINLINE bool operator==(const FACFStruct& Other) const
    {
        return TagName == Other.TagName;
    }
};


USTRUCT(BlueprintType)
struct FMoveset : public FBaseLayer {

	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TSubclassOf<class UACFMovesetLayer> Moveset;
};


USTRUCT(BlueprintType)
struct FOverlayLayer : public FBaseLayer {

	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TSubclassOf<class UACFOverlayLayer> Overlay;
};

/** One overlay animation entry with its own blend mask and blend mode. */
USTRUCT(BlueprintType)
struct FACFOverlayAnimationData
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	FOverlayConfig Overlay;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	TObjectPtr<UACFBoneBlendMask> BlendMask;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	EACFMaskBlendMode BlendMode = EACFMaskBlendMode::DynamicAdditive;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	TObjectPtr<UAimOffsetBlendSpace> AimOffset;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	float AimOffsetAlpha = 1.f;
};
/** Data-driven overlay definition consumed by the generic UACFOverlayLayer and ACFBlendByMask. */
USTRUCT(BlueprintType)
struct FACFOverlayData
{
	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Moveset"), Category = ACF)
	FGameplayTag TagName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	FACFOverlayAnimationData IdleOverlay;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (Categories = "Stances"), Category = ACF)
	TMap<FGameplayTag, FACFOverlayAnimationData> LocomotionStancesOverlays;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	float DefaultSwitchTime = 0.5f;

	FORCEINLINE bool operator==(const FGameplayTag& Other) const { return TagName == Other; }
	FORCEINLINE bool operator!=(const FGameplayTag& Other) const { return TagName != Other; }
};

USTRUCT(BlueprintType)
struct FRiderLayer : public FBaseLayer {

	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TSubclassOf<class UACFRiderLayer> RiderLayer;
};



