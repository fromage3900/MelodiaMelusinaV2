// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameplayTagContainer.h"
#include "GenericTeamAgentInterface.h"
#include "Net/UnrealNetwork.h"

#include "ACFTeamComponent.generated.h"


DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnTeamChanged,  FGameplayTag, NewTeam);

UCLASS(BlueprintType, Blueprintable, ClassGroup=(ACF), meta=(BlueprintSpawnableComponent))
class ASCENTTEAMS_API UACFTeamComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    UACFTeamComponent();

    // Replication
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual bool IsSupportedForNetworking() const override { return true; }

protected:
    virtual void BeginPlay() override;

public:
    // Team Management - SERVER ONLY
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF Team")
    void SetTeam(const FGameplayTag& NewTeam);

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    FGameplayTag GetTeam() const { return CurrentTeam; }

    // Server RPC for clients to request team change
    UFUNCTION(Server, Reliable, BlueprintCallable, Category = "ACF Team")
    void ServerRequestTeamChange(const FGameplayTag& NewTeam);

    // Utility Functions
    UFUNCTION(BlueprintPure, Category = "ACF Team")
    ETeamAttitude::Type GetAttitudeTowards(const FGameplayTag& OtherTeam) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    ETeamAttitude::Type GetAttitudeTowardsActor(AActor* OtherActor) const;

    /**/
    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool IsHostileTowards(const FGameplayTag& OtherTeam) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool IsFriendlyWith(const FGameplayTag& OtherTeam) const;

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool CanDamageTeam(const FGameplayTag& OtherTeam) const;

    // Events
    UPROPERTY(BlueprintAssignable, Category = "ACF Team")
    FOnTeamChanged OnTeamChanged;

    // GenericTeamInterface support
    FGenericTeamId GetGenericTeamId() const;

protected:
    // REPLICATED team data
    UPROPERTY(ReplicatedUsing = OnRep_CurrentTeam, EditAnywhere, BlueprintReadOnly, meta = (Categories = "Teams"), Category = "ACF Team")
    FGameplayTag CurrentTeam;

    // RepNotify function
    UFUNCTION()
    void OnRep_CurrentTeam();

    // Internal team change logic
    void Internal_SetTeam(const FGameplayTag& NewTeam);
};
