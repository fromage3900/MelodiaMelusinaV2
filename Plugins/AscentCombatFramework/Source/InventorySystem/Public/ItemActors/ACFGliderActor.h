// Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/SkeletalMesh.h"
#include "ItemActors/ACFItemActor.h"

#include "ACFGliderActor.generated.h"

/**
 * Replicated actor spawned while the glider ability is active.
 * The mesh is stored as a replicated property so all clients apply it
 * automatically via OnRep without needing InitItemActor to run client-side.
 */
UCLASS(Blueprintable, BlueprintType)
class INVENTORYSYSTEM_API AACFGliderActor : public AACFItemActor
{
    GENERATED_BODY()

public:
    AACFGliderActor();

    UFUNCTION(BlueprintPure, Category = "ACF|Glider")
    USkeletalMeshComponent* GetMeshComponent() const { return Mesh; }

    UFUNCTION(BlueprintPure, Category = "ACF|Glider")
    USceneComponent* GetLeftHandIKComponent() const { return LeftHandIKPos; }

    virtual void InitItemActor(APawn* inOwner, UACFItem* inItemDefinition) override;

    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "ACF|Glider")
    TObjectPtr<USkeletalMeshComponent> Mesh;

    /** Drag in the Blueprint viewport to set where the LEFT hand grips. */
    UPROPERTY(BlueprintReadOnly, EditAnywhere, Category = "ACF|Glider")
    TObjectPtr<USceneComponent> LeftHandIKPos;

    /** Replicated so clients can apply the correct mesh in OnRep. */
    UPROPERTY(ReplicatedUsing = OnRep_GliderMesh)
    TObjectPtr<USkeletalMesh> ReplicatedMesh;

    UFUNCTION()
    void OnRep_GliderMesh();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void OnRep_ItemOwner() override;
    virtual void InitItemFromDefinition_Implementation(UACFItem* inItemDefinition) override;

private:
    void ApplyMesh();
    void ApplyIKOverride();
    void ClearIKOverride();
};
