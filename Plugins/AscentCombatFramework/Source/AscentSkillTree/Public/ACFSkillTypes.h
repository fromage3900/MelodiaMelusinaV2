// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFCoreTypes.h"
#include "ACFRPGTypes.h"
#include "CoreMinimal.h"
#include "MediaSource.h"
#include <Net/Serialization/FastArraySerializer.h>

#include "ACFSkillTypes.generated.h"

USTRUCT(BlueprintType)
struct FSkillSaveData : public FFastArraySerializerItem {

public:
    GENERATED_BODY()

    FSkillSaveData() {
    };

    FSkillSaveData(const FGuid& inSkillId, const FGameplayTag& inTreeTag)
    {
        SkillId = inSkillId;
        SkillTreeTag = inTreeTag;
    };
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGuid SkillId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayTag SkillTreeTag;

    /*
    FORCEINLINE bool operator==(const FSkillSaveData& Other)
    {
        return SkillTag == Other.SkillTag && SkillTreeTag == Other.SkillTreeTag;
    }

    FORCEINLINE bool operator!=(const FSkillSaveData& Other)
    {
        return SkillTag != Other.SkillTag;
    }*/
};

FORCEINLINE bool operator==(const FSkillSaveData& A, const FSkillSaveData& B)
{
    return A.SkillId == B.SkillId && A.SkillTreeTag == B.SkillTreeTag;
}

FORCEINLINE uint32 GetTypeHash(const FSkillSaveData& Key)
{
    return HashCombine(GetTypeHash(Key.SkillId), GetTypeHash(Key.SkillTreeTag));
}

USTRUCT(BlueprintType)
struct FSkillSaveContainer : public FFastArraySerializer {
    GENERATED_BODY()

    UPROPERTY()
    TArray<FSkillSaveData> Skills;

    bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
    {
        return FFastArraySerializer::FastArrayDeltaSerialize<FSkillSaveData, FSkillSaveContainer>(Skills, DeltaParms, *this);
    }

    void AddSkill(const FSkillSaveData& NewSkill)
    {
        const int32 NewIndex = Skills.Add(NewSkill);
        MarkItemDirty(Skills[NewIndex]);
    }

    void RemoveSkillById(const FGuid& SkillTag)
    {
        int32 Index = Skills.IndexOfByPredicate([&](const FSkillSaveData& Skill) {
            return Skill.SkillId == SkillTag;
        });

        if (Index != INDEX_NONE) {
            Skills.RemoveAt(Index);
            MarkArrayDirty();
        }
    }

    bool Contains(const FGuid& SkillTag) const
    {
        return Skills.ContainsByPredicate([&](const FSkillSaveData& Skill) {
            return Skill.SkillId == SkillTag;
        });
    }

    bool Contains(const FSkillSaveData& Skill) const
    {
        return Skills.Contains(Skill);
    }

    const FSkillSaveData* GetSkill(const FGuid& SkillTag) const
    {
        return Skills.FindByPredicate([&](const FSkillSaveData& Skill) {
            return Skill.SkillId == SkillTag;
        });
    }
    /**
     * Clears all saved skills and marks the array as dirty for replication.
     */
    void ClearAllSkills()
    {
        Skills.Reset();
        MarkArrayDirty();
    }
};

template <>
struct TStructOpsTypeTraits<FSkillSaveContainer> : public TStructOpsTypeTraitsBase2<FSkillSaveContainer> {
    enum {
        WithNetDeltaSerializer = true,
    };
};

USTRUCT(BlueprintType)
struct FSkillConfig {

public:
    GENERATED_BODY()

    FSkillConfig()
    {
        RequiredLevel = 1;
        RequiredSkillPoint = 1;
    };

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FAbilityConfig AbilityToGrant;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    FGameplayEffectConfig GameplayEffect;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    int32 RequiredLevel;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = ACF)
    int32 RequiredSkillPoint;
};

USTRUCT(BlueprintType)
struct FSkillUIConfig {

public:
    GENERATED_BODY()

    FSkillUIConfig()
    {
        UnlockedIcon = nullptr;
        LockedIcon = nullptr;
        PreviewVideo = nullptr;
    };

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|UI")
    FText SkillName;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|UI")
    FText Description;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|UI")
    TObjectPtr<UMediaSource> PreviewVideo;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|UI")
    TObjectPtr<UTexture2D> UnlockedIcon;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF|UI")
    TObjectPtr<UTexture2D> LockedIcon;
};
UCLASS()
class ASCENTSKILLTREE_API UACFSkillTypes : public UObject {
    GENERATED_BODY()
};
