// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayCueNotify_Static.h"
#include <GameplayEffectTypes.h>
#include "Items/ACFConsumable.h"

#include "ACFItemUsedGameplayCue.generated.h"

USTRUCT()
struct FItemUseEffectContext : public FGameplayEffectContext {
    GENERATED_BODY()

    UPROPERTY()
    TSubclassOf<class UACFConsumable> ConsumedItemClass;

    virtual UScriptStruct* GetScriptStruct() const override { return StaticStruct(); }

    virtual FGameplayEffectContext* Duplicate() const override
    {
        return new FItemUseEffectContext(*this);
    }

    virtual bool NetSerialize(FArchive& Ar, class UPackageMap* Map, bool& bOutSuccess) override
    {
        Super::NetSerialize(Ar, Map, bOutSuccess);
        UObject* Obj = ConsumedItemClass.Get();
        Map->SerializeObject(Ar, UClass::StaticClass(), Obj);
        ConsumedItemClass = Cast<UClass>(Obj);
        bOutSuccess = true;
        return true;
    }
};

template <>
struct TStructOpsTypeTraits<FItemUseEffectContext> : public TStructOpsTypeTraitsBase2<FItemUseEffectContext> {
    enum {
        WithNetSerializer = true,
        WithCopy = true,
        WithDuplicate = true
    };
};

/**
 * Executes a visual/audio effect when a consumable item is used.
 */
UCLASS()
class INVENTORYSYSTEM_API UACFItemUsedGameplayCue : public UGameplayCueNotify_Static {
    GENERATED_BODY()

public:
    UACFItemUsedGameplayCue();

protected:
    bool OnExecute_Implementation(AActor* Target, const FGameplayCueParameters& Parameters) const;
};
