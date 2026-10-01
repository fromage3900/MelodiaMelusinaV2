// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CCMTypes.h"
#include "Components/ActorComponent.h"
#include "CoreMinimal.h"

#include "CCMFadeableActorComponent.generated.h"

class UMaterialInterface;

UCLASS(ClassGroup = (CCM), meta = (BlueprintSpawnableComponent))
class CINEMATICCAMERAMANAGER_API UCCMFadeableActorComponent : public UActorComponent {
    GENERATED_BODY()

public:
    // Sets default values for this component's properties
    UCCMFadeableActorComponent();

    UFUNCTION(BlueprintCallable, Category = CCM)
    void SetMaterialOverride(UMaterialInterface* newMaterial);
    
    UFUNCTION(BlueprintCallable, Category = CCM)
    void SetMaterialOverlay(UMaterialInterface* newMaterial);

    UFUNCTION(BlueprintCallable, Category = CCM)
    void RemoveMaterialOverlay();

    UFUNCTION(BlueprintPure, Category = CCM)
    bool GetIsMaterialOverriden() const
    {
        return bOverriden;
    }

    UFUNCTION(BlueprintPure, Category = CCM)
    UMaterialInterface* GetCurrentMaterialOverride() const
    {
        return currentMaterial;
    }
    UFUNCTION(BlueprintCallable, Category = CCM)
    void RestoreMaterials();

protected:
    // Called when the game starts
    virtual void BeginPlay() override;

    UPROPERTY(BlueprintReadOnly, Category = CCM)
    TArray<FMeshMaterials> MeshesMaterials;

private:
    bool bOverriden;

    TObjectPtr<UMaterialInterface> currentMaterial;

    void GatherMaterials();
};
