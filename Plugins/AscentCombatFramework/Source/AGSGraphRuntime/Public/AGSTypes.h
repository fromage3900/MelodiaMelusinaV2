// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include <Net/Serialization/FastArraySerializer.h>

#include "AGSTypes.generated.h"

USTRUCT(BlueprintType)
struct FAGSGraphRecord : public FFastArraySerializerItem {
    GENERATED_BODY()

public:
    FAGSGraphRecord(const class UGSGraph* graph);

    FAGSGraphRecord() { };

    UPROPERTY(BlueprintReadOnly, SaveGame, Category = AGS)
    FGuid GraphID;

    UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
    TArray<FGuid> ActiveNodeIds;

    FORCEINLINE bool operator==(const FAGSGraphRecord& Other) const
    {
        return this->GraphID == Other.GraphID;
    }

    FORCEINLINE bool operator!=(const FAGSGraphRecord& Other) const
    {
        return this->GraphID != Other.GraphID;
    }

    FORCEINLINE bool operator==(const FGuid& Other) const
    {
        return this->GraphID == Other;
    }

    FORCEINLINE bool operator!=(const FGuid& Other) const
    {
        return this->GraphID != Other;
    }
};

USTRUCT(BlueprintType, meta = (HasNativeNetSerialize))
struct FAGSGraphList : public FFastArraySerializer {
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintReadOnly, SaveGame, Category = AQS)
    TArray<FAGSGraphRecord> Graphs;

    bool NetDeltaSerialize(FNetDeltaSerializeInfo& DeltaParms)
    {
        return FFastArraySerializer::FastArrayDeltaSerialize<FAGSGraphRecord, FAGSGraphList>(Graphs, DeltaParms, *this);
    }

    void AddGraph(const FAGSGraphRecord& Record)
    {
        const int32 Index = Graphs.IndexOfByKey(Record);

        if (Index != INDEX_NONE) {
            Graphs[Index] = Record;
            MarkItemDirty(Graphs[Index]);
        } else {
            const int32 NewIndex = Graphs.Add(Record);
            MarkItemDirty(Graphs[NewIndex]);
        }
    }

    bool Contains(const FGuid& graphId) const
    {
        return Graphs.Contains(graphId);
    }

    void RemoveGraph(const FGuid& graphId)
    {
        const int32 Index = Graphs.IndexOfByPredicate([&](const FAGSGraphRecord& R) {
            return R.GraphID == graphId;
        });
        if (Index != INDEX_NONE) {
            Graphs.RemoveAt(Index);
            MarkArrayDirty();
        }
    }
    void Remove(const FAGSGraphRecord& Record)
    {
        const int32 Index = Graphs.IndexOfByKey(Record);
        if (Index != INDEX_NONE) {
            Graphs.RemoveAt(Index);
            MarkArrayDirty();
        }
    }

    const FAGSGraphRecord* GetGraph(const FGuid& graphId) const
    {
        return Graphs.FindByPredicate([&](const FAGSGraphRecord& R) {
            return R.GraphID == graphId;
        });
    }
};

template <>
struct TStructOpsTypeTraits<FAGSGraphList> : public TStructOpsTypeTraitsBase2<FAGSGraphList> {
    enum { WithNetDeltaSerializer = true };
};

UCLASS()
class AGSGRAPHRUNTIME_API UAGSTypes : public UObject {
    GENERATED_BODY()
};
