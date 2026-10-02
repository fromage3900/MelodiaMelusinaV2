// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ALSSaveTypes.h"
#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"

#include "ALSSaveInfo.generated.h"

/**
 *
 */

USTRUCT(Blueprintable)
struct FALSSaveMetadata {
    GENERATED_BODY()

public:

    FALSSaveMetadata() {
        PlayTime = 0;
    }
    UPROPERTY(BlueprintReadOnly, Savegame, Category = ALS)
    FString SaveName;

    UPROPERTY(BlueprintReadOnly, Savegame, Category = ALS)
    FString MapToLoad;

    UPROPERTY(BlueprintReadOnly, Savegame, Category = ALS)
    FString SaveDescription;

    UPROPERTY(BlueprintReadOnly, Savegame, Category = ALS)
    FDateTime Data;

    UPROPERTY(BlueprintReadOnly, Savegame, Category = ALS)
    int32 PlayTime = 0;

    FORCEINLINE bool operator==(const FALSSaveMetadata& Other) const
    {
        return this->SaveName == Other.SaveName;
    }

    FORCEINLINE bool operator!=(const FALSSaveMetadata& Other) const
    {
        return this->SaveName != Other.SaveName;
    }

    FORCEINLINE bool operator==(const FString& Other) const
    {
        return this->SaveName == Other;
    }

    FORCEINLINE bool operator!=(const FString& Other) const
    {
        return this->SaveName != Other;
    }

    FORCEINLINE bool operator<(const FALSSaveMetadata& Other) const
    {
        return this->Data > Other.Data;
    }
};

UCLASS(Blueprintable, Category = ALS)
class ASCENTSAVESYSTEM_API UALSSaveInfo : public USaveGame {
    GENERATED_BODY()

protected:
    UPROPERTY(SaveGame)
    TArray<FALSSaveMetadata> SaveSlots;

public:
    TArray<FALSSaveMetadata> GetSaveSlots() const
    {
        return SaveSlots;
    }

    void AddSlot(const FALSSaveMetadata& slotToAdd)
    {
        if (SaveSlots.Contains(slotToAdd)) {
            SaveSlots.Remove(slotToAdd);
        }
        SaveSlots.Emplace(slotToAdd);
        SaveSlots.HeapSort();
    }

    bool DeleteSlot(const FString& SlotName)
    {
        if (SaveSlots.Contains(SlotName)) {
            FALSSaveMetadata outData = *(SaveSlots.FindByKey(SlotName));
            SaveSlots.Remove(outData);
            return true;
        }
        return false;
    }

    bool TryGetSaveSlotData(const FString& SlotName, FALSSaveMetadata& outData) const
    {
        if (SaveSlots.Contains(SlotName)) {
            outData = *(SaveSlots.FindByKey(SlotName));
            return true;
        }
        return false;
    }
};
