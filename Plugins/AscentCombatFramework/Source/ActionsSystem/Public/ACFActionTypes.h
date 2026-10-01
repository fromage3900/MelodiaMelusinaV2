// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFActionsFunctionLibrary.h"
#include "ACFRPGTypes.h"
#include "ACMTypes.h"
#include "ARSFunctionLibrary.h"
#include "ARSTypes.h"
#include "Camera/CameraShakeBase.h"
#include "CoreMinimal.h"
#include "GenericTeamAgentInterface.h"
#include "Interfaces/ACFEntityInterface.h"
#include "NiagaraSystem.h"
#include "RootMotionModifier.h"
#include "Templates/SubclassOf.h"
#include <Abilities/GameplayAbility.h>
#include <AttributeSet.h>
#include <Engine/DataTable.h>
#include <GameFramework/DamageType.h>
#include <GameplayAbilitySpecHandle.h>
#include <GameplayTagContainer.h>
#include <InputAction.h>

#include "ACFActionTypes.generated.h"

class UACFActionAbility;

namespace ACF {
	const FName AbilityRoot = TEXT("Actions");
	const FName ExitTag = TEXT("Actions.AbilitySystem.ExitAction");
	const FName EnterSubTag = TEXT("Actions.AbilitySystem.EnterSubState");
	const FName ExitSubTag = TEXT("Actions.AbilitySystem.ExitSubState");
	const FName NotableTag = TEXT("Actions.AbilitySystem.NotablePoint");
	const FName FXTag = TEXT("Actions.AbilitySystem.PlayFX");
	const FName DamageTag = TEXT("Actions.AbilitySystem.ApplyDamage");
	const FName CooldownTag = TEXT("Actions.AbilitySystem.Cooldown");
	const FName StancesTag = TEXT("Stances");
	const FName AimTag = TEXT("Stances.Aiming");
	const FName BlockTag = TEXT("Stances.Blocking");
}

/*
 * Specifies how animation montages should be reproduced during ability execution.
 */
UENUM(BlueprintType)
enum class EMontageReproductionType : uint8 {
	ERootMotion UMETA(DisplayName = "Root Motion"),
	ERootMotionScaled UMETA(DisplayName = "Root Motion Scaled"),
	EMotionWarped UMETA(DisplayName = "Root Motion Warped"),
};

/*
 * Represents the current state of a sustained (held) action input.
 */
UENUM(BlueprintType)
enum class ESustainedActionState : uint8 {
	ENotStarted = 0 UMETA(DisplayName = "Not Started"),
	EStarted = 1 UMETA(DisplayName = "Started"),
	EReleased = 2 UMETA(DisplayName = "Released"),
};

/*
 * Determines the type of target used for motion warping.
 */
UENUM(BlueprintType)
enum class EWarpTargetType : uint8 {
	ETargetTransform UMETA(DisplayName = "Target Transform"),
	ETargetComponent UMETA(DisplayName = "Target Component"),
};

/*
 * Defines the direction used when firing or aiming.
 */
UENUM(BlueprintType)
enum class EShootDirection : uint8 {
	EControllerDirection = 0 UMETA(DisplayName = "Towards Controller Direction"),
	ECurrentTarget = 1 UMETA(DisplayName = "Towards Current Target"),
};

UENUM(BlueprintType)
enum EACFCustomMovementMode : uint8
{
	CMOVE_None UMETA(DisplayName = "None"),
	CMOVE_Ladder UMETA(DisplayName = "Ladder"),
	CMOVE_Climbing	UMETA(DisplayName = "Climbing")
};

	

/*
 * Struct used to track the state of a combo attack sequence.
 */
USTRUCT(BlueprintType)
struct FComboCounter {
	GENERATED_BODY()

public:
	FComboCounter()
	{
		Counter = 0;
		ComboTag = FGameplayTag();
	}

	FComboCounter(const FGameplayTag& inTag, const int32 count)
	{
		Counter = count;
		ComboTag = inTag;
	}

	UPROPERTY(Category = ACF, BlueprintReadOnly)
	FGameplayTag ComboTag;

	UPROPERTY(Category = ACF, BlueprintReadOnly)
	int32 Counter;

	FORCEINLINE bool operator!=(const FComboCounter& Other) const
	{
		return ComboTag != Other.ComboTag;
	}

	FORCEINLINE bool operator==(const FComboCounter& Other) const
	{
		return ComboTag == Other.ComboTag;
	}

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return ComboTag != Other;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return ComboTag == Other;
	}
};

USTRUCT(BlueprintType)
struct FActionsTags {
	GENERATED_BODY()

public:
	FActionsTags()
	{
		Moveset = FGameplayTag();
		ActionTag = FGameplayTag();
	}

	FActionsTags(const FGameplayTag& inMoveset, const FGameplayTag& inAction)
	{
		Moveset = inMoveset;
		ActionTag = inAction;
	}

	UPROPERTY(Category = ACF, BlueprintReadOnly)
	FGameplayTag Moveset;

	UPROPERTY(Category = ACF, BlueprintReadOnly)
	FGameplayTag ActionTag;
};

USTRUCT(BlueprintType)
struct FActionsHandlers {
	GENERATED_BODY()

public:
	FActionsHandlers()
	{
		AbilityHandle = FGameplayAbilitySpecHandle();
		FActionsTags();
	};

	FActionsHandlers(const FGameplayAbilitySpecHandle& inHandle,
		const FGameplayTag& inMoveset, const FGameplayTag& inAction)
	{
		AbilityHandle = inHandle;
		ActionTags.Moveset = inMoveset;
		ActionTags.ActionTag = inAction;
	}

	UPROPERTY(Category = ACF, BlueprintReadOnly)
	FGameplayAbilitySpecHandle AbilityHandle;

	UPROPERTY(Category = ACF, BlueprintReadOnly)
	FActionsTags ActionTags;

	FORCEINLINE bool operator!=(const FGameplayAbilitySpecHandle& Other) const
	{
		return AbilityHandle != Other;
	}

	FORCEINLINE bool operator==(const FGameplayAbilitySpecHandle& Other) const
	{
		return AbilityHandle == Other;
	}

	FORCEINLINE bool operator!=(const FActionsTags& Other) const
	{
		return ActionTags.ActionTag != Other.ActionTag || ActionTags.Moveset != Other.Moveset;
	}

	FORCEINLINE bool operator==(const FActionsTags& Other) const
	{
		return ActionTags.ActionTag == Other.ActionTag && ActionTags.Moveset == Other.Moveset;
	}
};

USTRUCT(BlueprintType)
struct FACFWarpInfo {

	GENERATED_BODY()
public:
	FACFWarpInfo()
	{
		//  WarpStartTime = 0.f;
		//  bIgnoreZAxis = true;
		//  WarpEndTime = 1.f;
		 // WarpRotationTime = 1.f;
		//RotationType = EMotionWarpRotationType::Default;
		SyncPoint = "Target";
		//bAutoWarp = true;
		TargetType = EWarpTargetType::ETargetTransform;
	}



	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	FName SyncPoint;

	//THOSE ARE NOW IN THE NOTIFY
	 /*Turn this off if you want to use the anim notify instead
	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	bool bAutoWarp;

	UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "bAutoWarp == true"), EditDefaultsOnly, Category = ACF)
	float WarpStartTime;

	UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "bAutoWarp == true"), EditDefaultsOnly, Category = ACF)
	float WarpEndTime;

	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	float WarpRotationTime;

	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	bool bIgnoreZAxis;

	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	EMotionWarpRotationType RotationType;*/

	UPROPERTY(BlueprintReadWrite, EditDefaultsOnly, Category = ACF)
	EWarpTargetType TargetType = EWarpTargetType::ETargetTransform;

	UPROPERTY(EditDefaultsOnly, Category = ACF)
	bool bShowWarpDebug = false;
};

USTRUCT(BlueprintType)
struct FACFWarpReproductionInfo {

	GENERATED_BODY()
public:
	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FACFWarpInfo WarpConfig;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FVector WarpLocation;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FRotator WarpRotation;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	USceneComponent* TargetComponent;

	FACFWarpReproductionInfo()
	{
		TargetComponent = nullptr;
		WarpConfig = FACFWarpInfo();
		WarpLocation = FVector(0.f);
		WarpRotation = FRotator(0.f);
	}
};

USTRUCT(BlueprintType)
struct FACFMontageInfo {
	GENERATED_BODY()
public:
	FACFMontageInfo(class UAnimMontage* inAnimMontage)
	{
		MontageAction = inAnimMontage;
		ReproductionSpeed = 1.f;
		StartSectionName = NAME_None;
		RootMotionScale = 1.f;
		ReproductionType = EMontageReproductionType::ERootMotion;
	}

	FACFMontageInfo()
	{
		MontageAction = nullptr;
		ReproductionSpeed = 1.f;
		StartSectionName = NAME_None;
		RootMotionScale = 1.f;
		ReproductionType = EMontageReproductionType::ERootMotion;
	}

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	class UAnimMontage* MontageAction;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	float ReproductionSpeed;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FName StartSectionName;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	EMontageReproductionType ReproductionType;

	UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "MontageReproductionType == EMontageReproductionType::ERootMotionScaled"), Category = ACF)
	float RootMotionScale;

	UPROPERTY(BlueprintReadWrite, meta = (EditCondition = "MontageReproductionType == EMontageReproductionType::EMotionWarped"), Category = ACF)
	FACFWarpReproductionInfo WarpInfo;
};

USTRUCT(BlueprintType)
struct FActionState : public FACFStruct {
	GENERATED_BODY()

public:
	FActionState()
	{
		MontageAction = nullptr;
		Action = nullptr;
		AbilityLevel = 1;
	}
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	TObjectPtr<class UAnimMontage> MontageAction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Instanced, Category = ACF)
	TObjectPtr<class UGameplayAbility> Action;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	int32 AbilityLevel;
};

USTRUCT(BlueprintType)
struct FActionAbilityConfig {
	GENERATED_BODY()

public:
	FActionAbilityConfig()
	{
		Action = nullptr;
		AbilityLevel = 1;
		TriggeringTag = FGameplayTag();
	}

	UPROPERTY(EditAnywhere, BlueprintReadOnly, meta = (Categories = "Actions,Ability"), Category = ACF)
	FGameplayTag TriggeringTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Instanced, meta = (DisplayName = "Ability"), Category = ACF)
	TObjectPtr<class UACFGameplayAbility> Action;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	int32 AbilityLevel;

	FORCEINLINE bool operator!=(const FGameplayTag& Other) const
	{
		return TriggeringTag != Other;
	}

	FORCEINLINE bool operator==(const FGameplayTag& Other) const
	{
		return TriggeringTag == Other;
	}

	FORCEINLINE bool operator!=(const FActionAbilityConfig& Other) const
	{
		return TriggeringTag != Other.TriggeringTag;
	}

	FORCEINLINE bool operator==(const FActionAbilityConfig& Other) const
	{
		return TriggeringTag == Other.TriggeringTag;
	}
};

USTRUCT(BlueprintType)
struct FActionsSet : public FACFStruct {

	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
	TSubclassOf<class UACFActionsSet> ActionsSet;
};

USTRUCT(BlueprintType)
struct FBoneSections {

	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	FName SectionName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
	TArray<FName> BoneNames;
};

USTRUCT(BlueprintType)
struct FActionsArray : public FACFStruct {

	GENERATED_BODY()

public:
	UPROPERTY(EditAnywhere, meta = (TitleProperty = "TagName"), BlueprintReadOnly, Category = ACF)
	TArray<FActionState> Actions;
};

UENUM(BlueprintType)
enum class EActionPriority : uint8 {
	ENone UMETA(DisplayName = "Very Low"),
	ELow UMETA(DisplayName = "Low"),
	EMedium UMETA(DisplayName = "Medium"),
	EHigh UMETA(DisplayName = "High"),
	EHighest UMETA(DisplayName = "Highest"),
};

USTRUCT(BlueprintType)
struct FActionConfig {
	GENERATED_BODY()

public:
	FActionConfig()
	{
		CoolDownTime = 0.f;
		PerformableInMovementModes.Add(EMovementMode::MOVE_Walking);
		PerformableInMovementModes.Add(EMovementMode::MOVE_Falling);
		PerformableInMovementModes.Add(EMovementMode::MOVE_None);

		ActionIcon = nullptr;
		CostGEType = EGEType::ESetByCallerFromConfig;
		CoolDownGEType = EGEType::ESetByCallerFromConfig;
		// ActionEffect.CueTag = UGameplayTagsManager::Get().RequestGameplayTag(ACF::AbilityCue);
	}

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	EGEType CostGEType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "CostGEtYPE == EGEType::ESetByCallerFromConfig", HideEditConditionToggle), Category = "ARS")
	TArray<FStatisticValue> ActionCost;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	FAttributesSetModifier AttributeModifier;

	/*Whether the cooldown should start automatically on actionStart. Otherwise you can still
	call StartCooldown within the action blueprint*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	bool bAutoStartCooldown = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	EGEType CoolDownGEType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "CoolDownGEType == EGEType::ESetByCallerFromConfig"), Category = ACFActionConfig)
	float CoolDownTime;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	int32 RequiredLevel = 0;

	// Decide if the montage of the action is played automatically or you'll need to
	// call ExecuteAction
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	bool bAutoExecute = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	EMontageReproductionType MontageReproductionType = EMontageReproductionType::ERootMotion;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "MontageReproductionType == EMontageReproductionType::ERootMotionScaled"), Category = ACFActionConfig)
	float RootMotionScale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, meta = (EditCondition = "MontageReproductionType == EMontageReproductionType::EMotionWarped"), Category = ACFActionConfig)
	FACFWarpInfo WarpInfo;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFAnimConfig)
	bool bPlayRandomMontageSection = false;

	/*Decide if we have to stop AIController's BT during this action*/
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFAnimConfig)
	bool bStopBehavioralThree = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFAnimConfig)
	bool bPlayEffectOnActionStart = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	FActionEffect ActionEffect;

	// Useful for UI
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	UTexture2D* ActionIcon;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACFActionConfig)
	TArray<TEnumAsByte<EMovementMode>> PerformableInMovementModes;

};

USTRUCT(BlueprintType)
struct FACFAbilityPayload
{
	GENERATED_BODY()

	FACFAbilityPayload()
	{
		Invalidate();
	}

	// Description: Stores persistent payload data for a triggered ACF Action.
	UPROPERTY(BlueprintReadOnly, Category = ACF)
	bool bIsValid = false;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	float FloatPayload = 0.f;

	/** Combo step index requested by the client. Carried with the predicted activation so
	 *  client and server pick the same montage section without replicating the counter. */
	UPROPERTY(BlueprintReadWrite, Category = ACF)
	int32 ComboCounter = 0;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FVector VectorPayload = FVector::ZeroVector;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FHitResult HitResult;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	TObjectPtr<AActor> TargetActor = nullptr;

	UPROPERTY(BlueprintReadWrite, Category = ACF)
	FGameplayTag PayloadTag;

	FORCEINLINE void Invalidate()
	{
		bIsValid = false;
		FloatPayload = 0;
		ComboCounter = 0;
		VectorPayload = FVector::ZeroVector;
		HitResult = FHitResult();
	}
};

/**
 * Struct che definisce un binding tra Input Action e Ability Tag
 */
USTRUCT(BlueprintType)
struct FACFInputAbilityBinding {
	GENERATED_BODY()

public:


	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input", meta = (DisplayName = "Input Action"))
	UInputAction* EnhancedInputAction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ability", meta = (DisplayName = "Ability Tag"))
	FGameplayTag AbilityTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input", meta = (DisplayName = "Priority"))
	EActionPriority Priority;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Input", meta = (DisplayName = "Description"))
	FString Description = "";

	FACFInputAbilityBinding()
	{
		EnhancedInputAction = nullptr;
		AbilityTag = FGameplayTag();
		Priority = EActionPriority::EMedium;
		Description = "";
	}
};

UCLASS()
class ACTIONSSYSTEM_API UACFAttackTypes : public UObject {
	GENERATED_BODY()
};
