// // Copyright (C) Developed by Pask, Published by Dark Tower Interactive SRL 2026. All Rights Reserved.

#include "CCMFadeableActorComponent.h"
#include "CCMTypes.h"
#include "Components/MeshComponent.h"

// Sets default values for this component's properties
UCCMFadeableActorComponent::UCCMFadeableActorComponent()
{
    // Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
    // off to improve performance if you don't need them.
    PrimaryComponentTick.bCanEverTick = false;

    // ...
}

void UCCMFadeableActorComponent::SetMaterialOverride(UMaterialInterface* newMaterial)
{
    if (!bOverriden) {
        GatherMaterials();
       
    }
    bOverriden = true;
    for (auto meshDesc : MeshesMaterials) {
        if (meshDesc.Mesh) {

            const int32 numMat = meshDesc.Mesh->GetNumMaterials();
            for (int32 i = 0; i < numMat; i++) {
                meshDesc.Mesh->SetMaterial(i, newMaterial);
            }
        }
    }
    
    currentMaterial = newMaterial;
}

void UCCMFadeableActorComponent::SetMaterialOverlay(UMaterialInterface* newMaterial)
{
    TArray<UActorComponent*> meshes;
    GetOwner()->GetComponents(UMeshComponent::StaticClass(), meshes);
    for (auto& mesh : meshes) {
        UMeshComponent* meshComp = Cast<UMeshComponent>(mesh);
        if (meshComp) {
            meshComp->SetOverlayMaterial(newMaterial);
        }
    }
}

void UCCMFadeableActorComponent::RemoveMaterialOverlay()
{
    TArray<UActorComponent*> meshes;
    GetOwner()->GetComponents(UMeshComponent::StaticClass(), meshes);

    for (auto& mesh : meshes) {
        UMeshComponent* meshComp = Cast<UMeshComponent>(mesh);
        if (meshComp) {
            meshComp->SetOverlayMaterial(nullptr);
        }
    }
}

void UCCMFadeableActorComponent::RestoreMaterials()
{
    /*    GatherMaterials();*/
    for (auto& meshDesc : MeshesMaterials) {
        if (meshDesc.Mesh) {

            int32 numMat = 0;
            for (const auto& overrideMat : meshDesc.Materials) {
                meshDesc.Mesh->SetMaterial(numMat, overrideMat);
                numMat++;
            }
        }
    }
    bOverriden = false;
    currentMaterial = nullptr;
}

// Called when the game starts
void UCCMFadeableActorComponent::BeginPlay()
{
    Super::BeginPlay();

    // ...
}

void UCCMFadeableActorComponent::GatherMaterials()
{
    MeshesMaterials.Empty();
    TArray<UActorComponent*> meshes;
    GetOwner()->GetComponents(UMeshComponent::StaticClass(), meshes);

    for (auto& mesh : meshes) {
        UMeshComponent* meshComp = Cast<UMeshComponent>(mesh);

        if (meshComp) {
            MeshesMaterials.Add(FMeshMaterials(meshComp));
        }
    }
}
