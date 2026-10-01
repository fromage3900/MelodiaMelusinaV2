// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "GenericTeamAgentInterface.h"
#include "Subsystems/WorldSubsystem.h"

#include "ACFTeamManagerSubsystem.generated.h"

class UACFTeamManagerComponent;

/**
 *
 */
UENUM(BlueprintType)
enum class EBattleType : uint8 {
    ETeamBased UMETA(DisplayName = "Team Based"),
    EEveryoneAgainstEveryone UMETA(DisplayName = "Everyone Against Everyone"),
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBattleTypeChanged, EBattleType, NewBattleType);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnActorTeamChanged, AActor*, Actor, FGameplayTag, NewTeam);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnFriendlyFireChanged, bool, bEnabled);

UCLASS()
class ASCENTTEAMS_API UACFTeamManagerSubsystem : public UWorldSubsystem {
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;

    // Utility Functions - Read directly from GameState component
    UFUNCTION(BlueprintPure, Category = "ACF Team")
    FGameplayTag GetActorTeam(const AActor* Actor) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    ETeamAttitude::Type GetAttitudeBetweenActors(const AActor* ActorA, const AActor* ActorB) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    FGenericTeamId FromTagToTeamId(const FGameplayTag& TeamTag) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    FGameplayTag FromTeamIdToTag(const FGenericTeamId& TeamId) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool AreActorsHostile(const AActor* Attacker, const AActor* Victim) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool CanActorDamageActor(const AActor* Attacker, const AActor* Victim) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool IsFriendlyFireEnabled() const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    EBattleType GetBattleType() const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    ETeamAttitude::Type GetDefaultAttitude() const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    UACFTeamsConfigDataAsset* GetTeamConfigDataAsset() const;

    // Team relationship queries - Read directly from data asset
    UFUNCTION(BlueprintPure, Category = "ACF Team")
    ETeamAttitude::Type GetTeamAttitudeTowards(const FGameplayTag& TeamA, const FGameplayTag& TeamB) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool AreTeamsHostile(const FGameplayTag& TeamA, const FGameplayTag& TeamB) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool AreTeamsFriendly(const FGameplayTag& TeamA, const FGameplayTag& TeamB) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool CanTeamDamageTeam(const FGameplayTag& AttackerTeam, const FGameplayTag& VictimTeam) const;

    // Collision channels - Read directly from data asset
    UFUNCTION(BlueprintPure, Category = "ACF Team")
    TArray<TEnumAsByte<ECollisionChannel>> GetHostileCollisionChannels(const FGameplayTag& Team) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    TArray<TEnumAsByte<ECollisionChannel>> GetAllDamageCollisionChannels() const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    TArray<TEnumAsByte<ECollisionChannel>> GetCollisionChannelsByTeam(const FGameplayTag& Team) const;
    // Events - forwarded from components
    UPROPERTY(BlueprintAssignable, Category = "ACF Team")
    FOnActorTeamChanged OnTeamChanged;

    UPROPERTY(BlueprintAssignable, Category = "ACF Team")
    FOnFriendlyFireChanged OnFriendlyFireChanged;

    UPROPERTY(BlueprintAssignable, Category = "ACF Team")
    FOnBattleTypeChanged OnBattleTypeChanged;

    // Internal - called by components
    void NotifyTeamChanged(AActor* Actor, const FGameplayTag& NewTeam);
    void NotifyFriendlyFireChanged(bool bEnabled);
    void NotifyBattleTypeChanged(EBattleType NewBattleType);

protected:
    // Cached reference to teams manager component
    UPROPERTY()
    mutable TWeakObjectPtr<UACFTeamManagerComponent> CachedTeamsManager;

    // Helper to get teams manager component with caching
    UACFTeamManagerComponent* GetTeamsManagerComponent() const;
};