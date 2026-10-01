// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/BoxComponent.h"
#include "CoreMinimal.h"
#include "GameplayTagContainer.h"

#include "ACFVaultComponent.generated.h"

/**
 *
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnActivationStateChanged, bool, isActive);

UCLASS(Blueprintable, ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CHARACTERCONTROLLER_API UACFVaultComponent : public UBoxComponent {
    GENERATED_BODY()

public:
    UACFVaultComponent();

    /// SETTERS ///

    /*Sets the best actor to vault*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetActorToVault(AActor* val);

    /*Enables/Disables vaulting Checks*/
    UFUNCTION(BlueprintCallable,Category = ACF)
    void SetVaultingEnabled(bool inEnabled);

    /*Changes Vault action at runtime*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetVaultActionTag(const FGameplayTag& val) { VaultActionTag = val; }
    /*Changes Mantle action at runtime*/
    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetMantleActionTag(const FGameplayTag& val) { MantleActionTag = val; }

    UFUNCTION(BlueprintCallable, Category = ACF)
    void SetVaultCollisionChannel(TEnumAsByte<ECollisionChannel> channel) { VaultablesChannel = channel; }

    /// GETTERS ///

    UFUNCTION(BlueprintPure, Category = ACF)
    ACharacter* GetCharacterOwner() const { return charOwner; }

    UFUNCTION(BlueprintPure, Category = ACF)
    bool IsEnabled() const { return bVaultChecksEnabled; }

    UFUNCTION(BlueprintPure, Category = ACF)
    AActor* GetActorToVault() const { return actorToVault.Get(); }

    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetMantleActionTag() const { return MantleActionTag; }

    UFUNCTION(BlueprintPure, Category = ACF)
    FGameplayTag GetVaultActionTag() const { return VaultActionTag; }

    UFUNCTION(BlueprintPure, Category = ACF)
    TEnumAsByte<ECollisionChannel> GetVaultableCollisionChannel() const
    {
        return VaultablesChannel;
    }

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnActivationStateChanged OnActivationChanged;

    UFUNCTION(BlueprintPure, Category = ACF)
    bool CanVault() const;

protected:
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag VaultActionTag;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    FGameplayTag MantleActionTag;

    // If this components should activate automatically on beginplay
    UPROPERTY(EditDefaultsOnly, Category = ACF)
    bool bAutoEnable;

    UPROPERTY(EditDefaultsOnly, Category = ACF)
    TEnumAsByte<ECollisionChannel> VaultablesChannel;

    virtual void BeginPlay() override;

    UFUNCTION(BlueprintNativeEvent, Category = ACF)
    void OnEnabledStateChanged(const bool bEnabled);
    virtual void OnEnabledStateChanged_Implementation(const bool bEnabled);

private:
    TObjectPtr<ACharacter> charOwner;

    UPROPERTY(ReplicatedUsing = OnRep_Activated)
    bool bVaultChecksEnabled;

    UFUNCTION()
    void OnRep_Activated();

    TObjectPtr<AActor> actorToVault;
};
