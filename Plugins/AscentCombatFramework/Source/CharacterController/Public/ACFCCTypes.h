// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ARSTypes.h"
#include "CoreMinimal.h"
#include "Engine/HitResult.h"
#include <Engine/DataTable.h>
#include <GameplayTagContainer.h>
#include "ACFRPGTypes.h"

#include "ACFCCTypes.generated.h"

/**
 *
 */

UENUM(BlueprintType)
enum class ERotationMode : uint8 {
    EForwardFacing = 0 UMETA(DisplayName = "ForwardFacing"),
    EStrafing = 1 UMETA(DisplayName = "Strafing"),
};

UENUM(BlueprintType)
enum class ELocomotionState : uint8 {
    EIdle = 0 UMETA(DisplayName = "Idle"),
    EWalk = 1 UMETA(DisplayName = "Walk"),
    EJog = 2 UMETA(DisplayName = "Jog"),
    ESprint = 3 UMETA(DisplayName = "Sprint"),
};

UENUM(BlueprintType)
enum class EMovementStance : uint8 {
    EIdle = 0 UMETA(DisplayName = "Idle"),
    EAiming = 1 UMETA(DisplayName = "Aiming"),
    EBlock = 2 UMETA(DisplayName = "Blocking"),
    ECustom = 3 UMETA(DisplayName = "Custom"),
};

USTRUCT(BlueprintType)
struct FAimOffset {
    GENERATED_BODY()

    FAimOffset()
    {
        AimOffsetYaw = 0.f;
        AimOffsetPitch = 0.f;
    };

    FAimOffset(const float& yaw, const float& pitch)
    {
        AimOffsetYaw = yaw;
        AimOffsetPitch = pitch;
    };

    UPROPERTY(BlueprintReadWrite, Category = ACF)
    float AimOffsetYaw;

    UPROPERTY(BlueprintReadWrite, Category = ACF)
    float AimOffsetPitch;
};

/**
 *
 *	Information about the ground under the character.
 */
USTRUCT(BlueprintType)
struct FCharacterGroundInfo {
    GENERATED_BODY()

    FCharacterGroundInfo()
        : LastUpdateFrame(0)
        , GroundDistance(0.0f)
        , SlopePitch(0.0f)
        , SlopeRoll(0.0f)
    {
    }

    uint64 LastUpdateFrame;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    FHitResult GroundHitResult;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    float GroundDistance;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    float SlopePitch;

    UPROPERTY(BlueprintReadOnly, Category = ACF)
    float SlopeRoll;
};

USTRUCT(BlueprintType)
struct FMovStances {
    GENERATED_BODY()

    FMovStances()
    {
        MovementStance = EMovementStance::EIdle;
        locomotionState = ELocomotionState::EWalk;
    }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    EMovementStance MovementStance;

    FORCEINLINE bool operator!=(const EMovementStance& Other) const
    {
        return MovementStance != Other;
    }

    FORCEINLINE bool operator==(const EMovementStance& Other) const
    {
        return MovementStance == Other;
    }

    FORCEINLINE bool operator!=(const FMovStances& Other) const
    {
        return MovementStance != Other.MovementStance;
    }

    FORCEINLINE bool operator==(const FMovStances& Other) const
    {
        return MovementStance == Other.MovementStance;
    }

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    ELocomotionState locomotionState;
};

USTRUCT(BlueprintType)
struct FOverlayConfig {
    GENERATED_BODY()

    FOverlayConfig()
    {
        OverlayAnim = nullptr;
        BlendTime = 0.3f;
        BlendAlpha = 0.85f;
    }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    class UAnimSequence* OverlayAnim;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float BlendTime = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float BlendAlpha = 0.75f;
};

USTRUCT(BlueprintType)
struct FACFLocomotionState {
    GENERATED_BODY()

    FACFLocomotionState()
    {
        State = ELocomotionState::EWalk;
        StateModifier = FAttributesSetModifier();
        MaxStateSpeed = 0.f;
        MaxStateSwimSpeed = 300.f;
    };
        FACFLocomotionState(ELocomotionState state)
    {
        State = state;
        StateModifier = FAttributesSetModifier();
        MaxStateSpeed = 0.f;
        MaxStateSwimSpeed = 300.f;
    };

    FACFLocomotionState(ELocomotionState state, float maxStateSpeed, float maxSwimSpeed)
    {
        State = state;
        MaxStateSpeed = maxStateSpeed;
        StateModifier = FAttributesSetModifier();
        MaxStateSwimSpeed = maxSwimSpeed;
    };

public:
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    ELocomotionState State;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    float MaxStateSpeed;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = ACF)
    float MaxStateSwimSpeed;


    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|ARS" )
    FAttributesSetModifier StateModifier;

    /*
    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|GAS")
    FGameplayEffectConfig StateGEModifier;*/

    FORCEINLINE bool operator<(const FACFLocomotionState& Other) const
    {
        return this->MaxStateSpeed < Other.MaxStateSpeed;
    }

    FORCEINLINE bool operator==(const FACFLocomotionState& Other) const
    {
        return this->State == Other.State;
    }

    FORCEINLINE bool operator!=(const ELocomotionState& Other) const
    {
        return this->State != Other;
    }

    FORCEINLINE bool operator==(const ELocomotionState& Other) const
    {
        return this->State == Other;
    }

    FORCEINLINE bool operator!=(const FACFLocomotionState& Other) const
    {
        return this->State != Other.State;
    }
};

/**
 *  Compressed representation of acceleration
 */
USTRUCT()
struct FReplicatedAcceleration {
    GENERATED_BODY()

    UPROPERTY()
    uint8 AccelXYRadians = 0; // Direction of XY accel component, quantized to represent [0, 2*pi]

    UPROPERTY()
    uint8 AccelXYMagnitude = 0; // Accel rate of XY component, quantized to represent [0, MaxAcceleration]

    UPROPERTY()
    int8 AccelZ = 0; // Raw Z accel rate component, quantized to represent [-MaxAcceleration, MaxAcceleration]
};

USTRUCT(BlueprintType)
struct FVaultMontageSelectors {
    GENERATED_BODY()

public:
    FVaultMontageSelectors()
    {
        MaxDistance = 50.f;
        MontageName = "Default";
    }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float MaxDistance;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FName MontageName;
};

// TO BE DEPRECATED

USTRUCT(BlueprintType)
struct FSnapConfiguration {
    GENERATED_BODY()

public:
    FSnapConfiguration()
    {
        target = nullptr;
    }

    UPROPERTY(BlueprintReadWrite, Category = ACF)
    AActor* target;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float preferredDistance = 150.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float maxSnapMultiplier = 2.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float RotationRateSnapMult = 1.0f;
};

UCLASS()
class CHARACTERCONTROLLER_API UACFCCTypes : public UObject {
    GENERATED_BODY()
};
