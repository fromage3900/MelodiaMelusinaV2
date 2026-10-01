// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "GameplayTagContainer.h"
#include <GameFramework/Character.h>
#include <ContextualAnimSceneAsset.h>

#include "CASTypes.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCombinedAnimationStarted, const FGameplayTag&, animTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnCombinedAnimationEnded, const FGameplayTag&, animTag);

UENUM(BlueprintType)
enum class ERelativeDirection : uint8 {
    EAny UMETA(DisplayName = "Any"),
    EFrontal UMETA(DisplayName = "Facing Each Other Only"),
    EOpposite UMETA(DisplayName = "From Behind"),
};

USTRUCT(BlueprintType)
struct FCombinedAnimConfig {
    GENERATED_BODY()

public:
    FCombinedAnimConfig()
    {
        //CombinedAnimation = nullptr;
        MaxDistanceToStart = 450.f;
        MasterRequiredActionsSet = FGameplayTag::EmptyTag;
        KillSlaveAfterAnim = false;
        AmbushExecution = false;
        AmbushRequiredDegrees = 45.f;
    }

    /*The tag of this combind anim */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    FGameplayTag AnimTag;

    /*The montage to be playd on master */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    TArray<UContextualAnimSceneAsset*> CombinedAnimation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    float MaxDistanceToStart = 450.f;

    /*The required MovesetActions tag for the Animmaster, empty means any moveset action or no one */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    FGameplayTag MasterRequiredActionsSet;

    /*The required tags to be checked in the SlaveComponent*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    FGameplayTagContainer SlaveRequiredTags;

     /*If this combined anim is a finisher, kills the slave character at the end of the animation*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    bool KillSlaveAfterAnim;
    
    /*If this combined anim is an ambush, checks the required degrees to be executed*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    bool AmbushExecution = false;
    
    /*The required degrees to be checked in the SlaveComponent*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS",
    meta = (EditCondition = "AmbushExecution", EditConditionHides))
    float AmbushRequiredDegrees = 45.f;
};

USTRUCT(BlueprintType)
struct FCombinedAnimsMaster : public FTableRowBase {
    GENERATED_BODY()

public:
    FCombinedAnimsMaster()
    {
        MasterAnimMontage = nullptr;
    }
    /*The tag of this combind anim */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    FGameplayTag AnimTag;

    /*The montage to be playd on master */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    class UAnimMontage* MasterAnimMontage;

    /*Max distance between master and slave characters to start snapping throught
    the start position*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    float MaxDistanceToStartWarping = 450.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    float MaxDistanceToStartCombinedAnimation = 50.f;

    /*Time to reachthe other character for the combined anim in seconds*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    float WarpTime = .2f;

    /*Time to reach the desired rotation toward the slave. The lower the faster*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    float WarpRotationTimeMultiplier = .5f;

    /*Time to reachthe other character for the combined anim in seconds*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    bool bIgnoreZAxis = true;

    /*If the slave is not in this relative direction to the master,
    the animation combined cannot start. Select Any to ignore this check*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    ERelativeDirection SlaveRequiredDirection = ERelativeDirection::EAny;

    /*Once the animation starts, the slaved character will be rotated to this direction.*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    ERelativeDirection SlaveForcedDirection = ERelativeDirection::EFrontal;
};

USTRUCT(BlueprintType)
struct FCombinedAnimsSlave : public FTableRowBase {
    GENERATED_BODY()

public:
    FCombinedAnimsSlave()
    {
        MasterAnimMontage = nullptr;
    }

    /*The tag of this combind anim */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    FGameplayTag AnimTag;

    /*The montage to be playd on slave */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "CAS")
    class UAnimMontage* MasterAnimMontage;
};

USTRUCT(BlueprintType)
struct FCurrentCombinedAnim {
    GENERATED_BODY()

public:
    FCurrentCombinedAnim()
    {

        AnimSlave = nullptr;
    };

    FCurrentCombinedAnim(const FCombinedAnimsMaster& inMasterConfig, const FGameplayTag& inTag, ACharacter* inCharacterRef)
    {
        MasterAnimConfig = inMasterConfig;
        AnimTag = inTag;
        AnimSlave = inCharacterRef;
    }
    UPROPERTY(BlueprintReadOnly, Category = "CAS")
    FTransform WarpTransform;

    UPROPERTY(BlueprintReadOnly, Category = "CAS")
    FCombinedAnimsMaster MasterAnimConfig;

    UPROPERTY(BlueprintReadOnly, Category = "CAS")
    FGameplayTag AnimTag;

    UPROPERTY(BlueprintReadOnly, Category = "CAS")
    ACharacter* AnimSlave;
};
/**
 *
 */
UCLASS()
class COMBINEDANIMATIONSSYSTEM_API UCASTypes : public UObject {
    GENERATED_BODY()
};
