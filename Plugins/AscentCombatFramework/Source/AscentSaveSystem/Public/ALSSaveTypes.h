// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Engine/Level.h"
#include "Engine/LevelStreaming.h"
#include "GameFramework/Actor.h"
#include "Serialization/ObjectAndNameAsStringProxyArchive.h"

#include "ALSSaveTypes.generated.h"

/**
 *
 */

struct FALSSaveGameArchive : public FObjectAndNameAsStringProxyArchive {
    FALSSaveGameArchive(FArchive& InInnerArchive, bool isSavegame)
        : FObjectAndNameAsStringProxyArchive(InInnerArchive, false)
    {
        ArIsSaveGame = true;
    }
};

UENUM(BlueprintType)
enum class ELoadType : uint8 {
    EDontReload = 0 UMETA(DisplayName = "Don't Load"),
    EPlayerOnly = 1 UMETA(DisplayName = "Load Player Only"),
    EFullReload = 2 UMETA(DisplayName = "Load Full World"),
};

USTRUCT()
struct FALSBaseData {
    GENERATED_BODY()

public:
    UPROPERTY(SaveGame)
    FName alsName;

    FName GetName() const
    {
        return alsName;
    }

    FALSBaseData()
        : alsName()
    {
    }

    inline virtual bool Serialize(FArchive& Ar)
    {
        Ar << alsName;
        return true;
    }
    friend FArchive& operator<<(FArchive& Ar, FALSBaseData& Record)
    {
        Record.Serialize(Ar);
        return Ar;
    }
    virtual ~FALSBaseData() { }
};

/** Represents a serialized Object */
USTRUCT()
struct FALSObjectData : public FALSBaseData {
    GENERATED_BODY()

public:
    UPROPERTY(SaveGame)
    UClass* Class;

    UPROPERTY(SaveGame)
    TArray<uint8> Data;

    FALSObjectData()
        : Super()
        , Class(nullptr)
    {
    }
    FALSObjectData(const UObject* Object);

    inline virtual bool Serialize(FArchive& Ar) override
    {
        FALSBaseData::Serialize(Ar);
        Ar << Class;
        Ar << alsName;
        Ar << Data;
        return true;
    }

    bool IsValid() const
    {
        return !alsName.IsNone() && Class && Data.Num() > 0;
    }

    FORCEINLINE bool operator==(const FALSObjectData& Other) const
    {
        return this->alsName == Other.alsName;
    }
    FORCEINLINE bool operator!=(const FALSObjectData& Other) const
    {
        return this->alsName != Other.alsName;
    }
    FORCEINLINE bool operator==(const UObject* Other) const
    {
        return this->alsName == Other->GetFName();
    }

    FORCEINLINE bool operator!=(const UObject* Other) const
    {
        return this->alsName != Other->GetFName();
    }

    FORCEINLINE bool operator==(const FName Name) const
    {
        return this->alsName == Name;
    }

    FORCEINLINE bool operator!=(const FName Name) const
    {
        return this->alsName != Name;
    }
};

/** Represents a serialized Component */
USTRUCT()
struct FALSComponentData : public FALSObjectData {
    GENERATED_BODY()

public:
    UPROPERTY(SaveGame)
    FTransform Transform;

    FALSComponentData()
        : Super()
    {
    }
    FALSComponentData(const UActorComponent* comp)
        : Super(comp)
    {
    }

    inline virtual bool Serialize(FArchive& Ar) override
    {
        FALSObjectData::Serialize(Ar);
        Ar << Transform;
        return true;
    }

    FORCEINLINE bool operator==(const UActorComponent* Other) const
    {
        return this->alsName == Other->GetFName();
    }

    FORCEINLINE bool operator!=(const UActorComponent* Other) const
    {
        return this->alsName != Other->GetFName();
    }

    FORCEINLINE bool operator==(const FName Name) const
    {
        return this->alsName == Name;
    }

    FORCEINLINE bool operator!=(const FName Name) const
    {
        return this->alsName != Name;
    }
};

/** Represents a serialized Actor */
USTRUCT()
struct FALSActorData : public FALSObjectData {
    GENERATED_BODY()

private:
    UPROPERTY(SaveGame)
    TArray<FALSComponentData> ComponentRecords;

public:
    FALSActorData()
        : Super()
    {
        bHiddenInGame = false;
    }

    UPROPERTY(SaveGame)
    TArray<FName> Tags;

    const FALSComponentData* GetComponentData(const UActorComponent* component) const
    {
        return ComponentRecords.FindByKey(component->GetFName());
    }

    bool HasComponent(const UActorComponent* component) const
    {
        return ComponentRecords.Contains(component->GetFName());
    }

    void AddComponentData(const FALSComponentData& component)
    {
        ComponentRecords.Add(component);
    }
    UPROPERTY(SaveGame)
    bool bHiddenInGame;

    UPROPERTY(SaveGame)
    FTransform Transform;

    FALSActorData(const AActor* Actor)
        : Super(Actor)
    {
    }

    inline virtual bool Serialize(FArchive& Ar) override
    {
        FALSObjectData::Serialize(Ar);
        Ar.SerializeBits(&bHiddenInGame, 1);
        Ar << Transform;
        Ar << ComponentRecords;
        return true;
    }

    FORCEINLINE bool operator==(const FALSActorData& Other) const
    {
        return this->alsName == Other.GetName();
    }

    FORCEINLINE bool operator!=(const FALSActorData& Other) const
    {
        return this->alsName != Other.GetName();
    }

    FORCEINLINE bool operator==(const AActor* Other) const
    {
        return this->alsName == Other->GetFName();
    }

    FORCEINLINE bool operator!=(const AActor* Other) const
    {
        return this->alsName != Other->GetFName();
    }

    FORCEINLINE bool operator==(const FName Name) const
    {
        return this->alsName == Name;
    }

    FORCEINLINE bool operator!=(const FName Name) const
    {
        return this->alsName != Name;
    }
};

/** Represents a level in the world (streaming or persistent) */
USTRUCT()
struct FALSLevelData : public FALSObjectData {
    GENERATED_BODY()

protected:
    /** Records of the World Actors */
    UPROPERTY(SaveGame)
    TArray<FALSActorData> Actors;

    UPROPERTY(SaveGame)
    TArray<FALSActorData> WPActors;

public:
    void AddActorRecord(const FALSActorData& actorData)
    {
        if (Actors.Contains(actorData)) {
            Actors.Remove(actorData);
        }
        Actors.AddUnique(actorData);
    }

    TArray<FALSActorData> GetActorsCopy() const
    {
        return Actors;
    }

    void GetWPActors(TArray<FALSActorData>& outActors) const
    {
        outActors = WPActors;
    }

    void CleanActors()
    {
        Actors.Empty(Actors.Num());
    }

    const FALSActorData* GetActorData(const AActor* actor) const
    {
        return Actors.FindByKey(actor);
    }

    bool HasActor(const AActor* actor) const
    {
        return Actors.Contains(actor);
    }

    bool HasWPActor(const AActor* actor) const
    {
        return WPActors.Contains(actor);
    }

    void AddWPActorRecord(const FALSActorData& actorData)
    {
        if (WPActors.Contains(actorData)) {
            WPActors.Remove(actorData);
        }
        WPActors.AddUnique(actorData);
    }

    const FALSActorData* GetWPActorData(const AActor* actor) const
    {
        return WPActors.FindByKey(actor);
    }

    FALSLevelData() { };
    FALSLevelData(const ULevel* level)
        : Super(level)
    {
    }
    inline virtual bool Serialize(FArchive& Ar) override
    {
        FALSObjectData::Serialize(Ar);
        Ar << Actors;
        Ar << WPActors;
        return true;
    }

    bool IsValid() const { return !alsName.IsNone(); }
};

USTRUCT()
struct FALSActorLoaded {
    GENERATED_BODY()

public:
    FALSActorLoaded(const FTransform& inTransform)
    {
        transform = inTransform;
    }

    FALSActorLoaded() { };
    FTransform transform;
};

USTRUCT()
struct FALSPlayerData {
    GENERATED_BODY()

public:
    FALSPlayerData() { };

    FALSPlayerData(const FALSActorData& inController, const FALSActorData& inPawn)
    {
        PlayerController = inController;
        Pawn = inPawn;
    }

    UPROPERTY(SaveGame)
    FALSActorData Pawn;

    UPROPERTY(SaveGame)
    FALSActorData PlayerController;
};

UCLASS()
class ASCENTSAVESYSTEM_API UALSSaveTypes : public UObject {
    GENERATED_BODY()
};
