// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "Components/ActorComponent.h"
#include "CoreMinimal.h"
#include "Items/ACFItem.h"

#include "ACFBuildableComponent.generated.h"

class UACFItemsManagerComponent;

UENUM(BlueprintType)
enum class EBuildableState : uint8 {
    ENotBuilded = 0 UMETA(DisplayName = "Not Builded"),
    EBuilded = 1 UMETA(DisplayName = "Builded"),
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBuildableStatusChanged, const EBuildableState, newState);

UCLASS(ClassGroup = (ACF), meta = (BlueprintSpawnableComponent))
class CRAFTINGSYSTEM_API UACFBuildableComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UACFBuildableComponent();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    TArray<FBaseItem> BuildingRequirements;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = ACF)
    float BuildingCost;

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnComponentLoaded();

    UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = ACF)
    void OnComponentSaved();

public:
    /* ----------------- GETTERS -----------------------*/
    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    float GetPawnCurrency(const APawn* pawn) const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    class UACFEquipmentComponent* GetPawnEquipment(const APawn* pawn) const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    class UACFCurrencyComponent* GetPawnCurrencyComponent(const APawn* pawn) const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    UACFItemsManagerComponent* GetItemsManager() const;

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    EBuildableState GetBuildingState() const
    {
        return BuildingState;
    }

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    float GetBuildingCost() const
    {
        return BuildingCost;
    }

    UFUNCTION(BlueprintPure, Category = "ACF | Getters")
    void GetBuildingRequirements(TArray<FBaseItem>& outItem) const
    {
        outItem = BuildingRequirements;
    }

    /* ---------------------- BUILD ----------------------*/
    UFUNCTION(BlueprintPure, Category = "ACF | Build")
    bool CanBeBuildByPawn(const APawn* pawn);

    UFUNCTION(BlueprintCallable, Category = "ACF | Build")
    void Build(APawn* pawn);

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnBuildableStatusChanged OnBuildableStatusChanged;

    UPROPERTY(BlueprintAssignable, Category = ACF)
    FOnBuildableStatusChanged ClientsOnBuildableStatusChanged;

    virtual void SetBuildingState(const EBuildableState newState);

private:
    UPROPERTY(Savegame, ReplicatedUsing = OnRep_BuildingState)
    EBuildableState BuildingState;

    UFUNCTION()
    void OnRep_BuildingState();
};
