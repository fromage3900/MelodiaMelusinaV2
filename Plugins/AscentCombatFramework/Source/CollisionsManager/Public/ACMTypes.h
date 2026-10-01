// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "GameplayEffectTypes.h"
#include "NiagaraSystem.h"
#include "PhysicalMaterials/PhysicalMaterial.h"
#include "Sound/SoundCue.h"
#include <GameFramework/DamageType.h>
#include <GameplayTagsManager.h>
#include "ACFRPGTypes.h"

#include "ACMTypes.generated.h"

class UParticleSystemComponent;
class UAudioComponent;

/**
 *
 */
namespace ACF {
	const FName HitCue = TEXT("GameplayCue.ACF.HitEffectCue");
	const FName ImpactCue = TEXT("GameplayCue.ACF.ImpactCue");
	const FName ActionCue = TEXT("GameplayCue.ACF.ActionCue");
	const FName ReactionCue = TEXT("GameplayCue.ACF.ReactionCue");
}

UENUM(BlueprintType)
enum class EDebugType : uint8 {
    EDontShowDebugInfos = 0 UMETA(DisplayName = "Don't Show Debug Info"),
    EShowInfoDuringSwing = 1 UMETA(DisplayName = "Show Info During Swing"),
    EAlwaysShowDebug = 2 UMETA(DisplayName = "Always Show Debug Info"),
};

UENUM(BlueprintType)
enum class EDamageType : uint8 {
    EPoint UMETA(DisplayName = "Point Damage"),
    EArea UMETA(DisplayName = "Area Damage"),
};

UENUM(BlueprintType)
enum class ESpawnFXLocation : uint8 {
    ESpawnOnActorLocation UMETA(DisplayName = "Attached to Actor"),
    ESpawnAttachedToSocketOrBone UMETA(DisplayName = "Attached to Socket / Bone"),
    ESpawnAtLocation UMETA(DisplayName = "Spawn On Provided Tranform")
};

USTRUCT(BlueprintType)
struct FBaseFX {
    GENERATED_BODY()

public:
    /*The Sound Cue to be played*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    class USoundBase* ActionSound;

    /*The Niagara Particle to be played*/
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    class UNiagaraSystem* NiagaraParticle;

    /*The Particle to be played*/
    UPROPERTY(EditAnywhere, meta = (DeprecatedFunction, DeprecationMessage = "USE NIAGARA PARTICLE!!"), BlueprintReadWrite, Category = ACF)
    class UParticleSystem* ActionParticle;

    FBaseFX()
    {
        ActionSound = nullptr;
        NiagaraParticle = nullptr;
        ActionParticle = nullptr;
    }

    FBaseFX(class USoundBase* inSound, class UNiagaraSystem* inParticle, class UParticleSystem* cascadeParticle)
    {
        ActionSound = inSound;
        NiagaraParticle = inParticle;
        ActionParticle = cascadeParticle;
    }
};

USTRUCT(BlueprintType)
struct FAreaDamageInfo {
    GENERATED_BODY()

public:
    FAreaDamageInfo()
    {
        Radius = 0.f;
        Location = FVector();
        bIsActive = false;
    }

    UPROPERTY(BlueprintReadOnly, Category = ACM)
    float Radius;

    UPROPERTY(BlueprintReadOnly, Category = ACM)
    FVector Location;

    UPROPERTY(BlueprintReadOnly, Category = ACM)
    bool bIsActive;

    // Timer used to handle looping damage
    UPROPERTY()
    FTimerHandle AreaLoopTimer;
};

USTRUCT(BlueprintType)
struct FHitActors {
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadOnly, EditDefaultsOnly, Category = ACM)
    TArray<class AActor*> AlreadyHitActors;
};

USTRUCT(BlueprintType)
struct FAttachedComponents {
    GENERATED_BODY()

public:
    FAttachedComponents()
    {
        CascadeComp = nullptr;
        NiagaraComp = nullptr;
        AudioComp = nullptr;
    }

    TObjectPtr<UParticleSystemComponent> CascadeComp;
    TObjectPtr<UNiagaraComponent> NiagaraComp;
    TObjectPtr<UAudioComponent> AudioComp;
};

USTRUCT(BlueprintType)
struct FActionEffect : public FBaseFX {
    GENERATED_BODY()

public:
    FActionEffect()
    {
        ActionSound = nullptr;
        ActionParticle = nullptr;
        NiagaraParticle = nullptr;
        Guid = FGuid::NewGuid();
    }

    FActionEffect(const FBaseFX& baseFX, const ESpawnFXLocation& inLocationType, const FName& inName)
    {
        ActionSound = baseFX.ActionSound;
        NiagaraParticle = baseFX.NiagaraParticle;
        ActionParticle = baseFX.ActionParticle;
        SpawnLocation = inLocationType;
        SocketOrBoneName = inName;
        Guid = FGuid::NewGuid();
    }

    FGuid GetGuid() const
    {
        return Guid;
    }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FName SocketOrBoneName = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    ESpawnFXLocation SpawnLocation = ESpawnFXLocation::ESpawnOnActorLocation;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float NoiseEmitted = 0.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    FTransform RelativeOffset;

private:
    UPROPERTY(Meta = (IgnoreForMemberInitializationTest))
    FGuid Guid = FGuid();
};

USTRUCT(BlueprintType)
struct FComponentFX{
    GENERATED_BODY()

public:

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    UNiagaraComponent* NiagaraComponent = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    UParticleSystemComponent* ParticleSystemComponent = nullptr;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    UAudioComponent* AudioComponent = nullptr;


};

USTRUCT(BlueprintType)
struct FImpactFX : public FBaseFX {
    GENERATED_BODY()

public:
    FImpactFX()
    {
        ActionSound = nullptr;
        NiagaraParticle = nullptr;
        ActionParticle = nullptr;
        SpawnLocation = FTransform();
    }

    FImpactFX(const FBaseFX& baseFX, const FVector& location)
    {
        ActionSound = baseFX.ActionSound;
        NiagaraParticle = baseFX.NiagaraParticle;
        ActionParticle = baseFX.ActionParticle;
        SpawnLocation = FTransform(location);
    }

    FImpactFX(const FActionEffect& baseFX, const FTransform& location)
    {
        ActionSound = baseFX.ActionSound;
        NiagaraParticle = baseFX.NiagaraParticle;
        ActionParticle = baseFX.ActionParticle;
        SpawnLocation = location;
    }

    FImpactFX(const FImpactFX& baseFX)
    {
        ActionSound = baseFX.ActionSound;
        NiagaraParticle = baseFX.NiagaraParticle;
        ActionParticle = baseFX.ActionParticle;
        SpawnLocation = baseFX.SpawnLocation;
    }

    UPROPERTY(BlueprintReadWrite, Category = ACF)
    FTransform SpawnLocation;
};

USTRUCT(BlueprintType)
struct FMaterialImpactFX : public FBaseFX {
    GENERATED_BODY()

public:
    FMaterialImpactFX()
    {
        ImpactMaterial = nullptr;
    }

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    UPhysicalMaterial* ImpactMaterial;

    FORCEINLINE bool operator!=(const FMaterialImpactFX& Other) const
    {
        return ImpactMaterial != Other.ImpactMaterial;
    }

    FORCEINLINE bool operator==(const FMaterialImpactFX& Other) const
    {
        return ImpactMaterial == Other.ImpactMaterial;
    }

    FORCEINLINE bool operator!=(const UPhysicalMaterial* Other) const
    {
        return ImpactMaterial != Other;
    }

    FORCEINLINE bool operator==(const UPhysicalMaterial* Other) const
    {
        return ImpactMaterial == Other;
    }
};

USTRUCT(BlueprintType)
struct FImpactsArray {
    GENERATED_BODY()

public:
    FImpactsArray() { };

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TArray<FMaterialImpactFX> ImpactsFX;
};

USTRUCT()
struct FACFGameplayEffectContext : public FGameplayEffectContext {

    GENERATED_BODY()

public:
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag ActionEffectTag;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    TSubclassOf<UDamageType> DamageTypeClass;

    virtual bool NetSerialize(FArchive& Ar, class UPackageMap* Map, bool& bOutSuccess) override
    {
        Super::NetSerialize(Ar, Map, bOutSuccess);
        Ar << ActionEffectTag;

        UObject* ClassObj = DamageTypeClass.Get();
        Map->SerializeObject(Ar, UClass::StaticClass(), ClassObj);
        DamageTypeClass = Cast<UClass>(ClassObj);
        bOutSuccess = true;
        return true;
    }

    virtual UScriptStruct* GetScriptStruct() const override
    {
        return FACFGameplayEffectContext::StaticStruct();
    }

    virtual FGameplayEffectContext* Duplicate() const override
    {
        return new FACFGameplayEffectContext(*this);
    }
};

template <>
struct TStructOpsTypeTraits<FACFGameplayEffectContext> : public TStructOpsTypeTraitsBase2<FACFGameplayEffectContext> {
    enum {
        WithNetSerializer = true,
        WithCopy = true,
        WithDuplicate = true
    };
};

USTRUCT(BlueprintType)
struct FBaseTraceInfo {

    GENERATED_BODY()

public:
    FBaseTraceInfo()
    {
        DamageTypeClass = UDamageType::StaticClass();
        DamageType = EDamageType::EPoint;
    }
    /** The type of damage applied*/
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACM)
    TSubclassOf<class UDamageType> DamageTypeClass = UDamageType::StaticClass();

    /** The base damage to apply to the actor (Can be modified in you TakeDamage Implementation)*/
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACM)
    float BaseDamage = 0.f;

    /** Select if it's Area or Point Damage*/
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACM)
    EDamageType DamageType;

    /** GameplayEffect to be applied on Hit*/
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = ACM)
    FGameplayEffectConfig GameplayEffect;
};

USTRUCT(BlueprintType)
struct FTraceInfo : public FBaseTraceInfo {
    GENERATED_BODY()

public:
    FTraceInfo()
    {
        AttackSound = nullptr;
        AttackParticle = nullptr;
        NiagaraTrail = nullptr;
        Radius = 10.f;
        StartSocket = "start";
        EndSocket = "end";
        bIsFirstFrame = true;
        oldEndSocketPos = FVector();
        bCrossframeAccuracy = true;
    }

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACM)
    float Radius;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACM)
    float TrailLength = 1.f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACM)
    class USoundCue* AttackSound;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACM)
    class UParticleSystem* AttackParticle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACM)
    class UNiagaraSystem* NiagaraTrail;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACM)
    FName StartSocket;
    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACM)
    FName EndSocket;

    UPROPERTY(BlueprintReadWrite, EditAnywhere, Category = ACM)
    bool bCrossframeAccuracy;

    bool bIsFirstFrame;
    FVector oldEndSocketPos;
};

UCLASS()
class COLLISIONSMANAGER_API UACMTypes : public UObject {
    GENERATED_BODY()
};
