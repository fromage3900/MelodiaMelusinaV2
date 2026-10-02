// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "ACFTeamManagerSubsystem.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "Net/UnrealNetwork.h"
#include <GenericTeamAgentInterface.h>

#include "ACFTeamManagerComponent.generated.h"

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class ASCENTTEAMS_API UACFTeamManagerComponent : public UActorComponent {
    GENERATED_BODY()

    // Constructors
public:
    // Sets default values for this component's properties
    UACFTeamManagerComponent();

    // Replication
    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
    virtual bool IsSupportedForNetworking() const override { return true; }

    // Friendly Fire Management - SERVER ONLY
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF Team")
    void SetFriendlyFireEnabled(bool bEnabled);

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    bool IsFriendlyFireEnabled() const { return bFriendlyFireEnabled || CurrentBattleType == EBattleType::EEveryoneAgainstEveryone; }

    // Battle Type Management - SERVER ONLY
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF Team")
    void SetBattleType(EBattleType NewBattleType);

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    EBattleType GetBattleType() const { return CurrentBattleType; }

    // Data Asset Reference - SERVER ONLY
    UFUNCTION(BlueprintCallable, BlueprintAuthorityOnly, Category = "ACF Team")
    void SetTeamConfigDataAsset(UACFTeamsConfigDataAsset* InTeamConfig);

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    UACFTeamsConfigDataAsset* GetTeamConfigDataAsset() const { return TeamConfigDataAsset; }

    UFUNCTION(BlueprintPure, Category = "ACF Team")
    TEnumAsByte<ETeamAttitude::Type> GetDefaultAttitude() const { return DefaultAttitude; }

    // Events
    UPROPERTY(BlueprintAssignable, Category = "ACF Team")
    FOnBattleTypeChanged OnBattleTypeChanged;

    // Events
    UPROPERTY(BlueprintAssignable, Category = "ACF Team")
    FOnFriendlyFireChanged OnFriendlyFireChanged;

protected:
    // Runtime settings - replicated
    UPROPERTY(ReplicatedUsing = OnRep_BattleType, BlueprintReadOnly, EditDefaultsOnly, Category = "ACF Team")
    EBattleType CurrentBattleType = EBattleType::ETeamBased;

    // Only runtime settings, NOT data duplication
    UPROPERTY(ReplicatedUsing = OnRep_FriendlyFireEnabled, BlueprintReadOnly, EditDefaultsOnly, Category = "ACF Team")
    bool bFriendlyFireEnabled = false;

    UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "ACF Team")
    TEnumAsByte<ETeamAttitude::Type> DefaultAttitude = ETeamAttitude::Neutral;

    // Reference to data asset - NOT replicated, loaded on all clients
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "ACF Team")
    UACFTeamsConfigDataAsset* TeamConfigDataAsset;

    UFUNCTION()
    void OnRep_FriendlyFireEnabled();

    UFUNCTION()
    void OnRep_BattleType();
};
